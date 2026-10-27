"""Explicit offline FastAPI adapter over verified controlled-synthetic demo services."""

from __future__ import annotations

import json
import math
import re
from collections.abc import Callable
from dataclasses import fields, is_dataclass
from datetime import date
from enum import Enum
from pathlib import Path
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, Response
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.types import ASGIApp, Receive, Scope, Send

from rossmann_forecasting.app._http import error_response as _error_response
from rossmann_forecasting.app._http import http_error_handler
from rossmann_forecasting.app.contracts import (
    ForecastQuery,
    HistoryQuery,
    InventoryComparisonQuery,
    ModelComparisonQuery,
    UncertaintyQuery,
)
from rossmann_forecasting.app.demo_provider import (
    DemoErrorCode,
    DemoInvalidRequestError,
    DemoProfile,
    DemoProviderError,
    DemoReleaseIntegrityError,
    DemoReleaseUnavailableError,
    SyntheticProvenance,
)
from rossmann_forecasting.app.demo_services import DemoServices

_EVIDENCE_LABEL = "CONTROLLED SYNTHETIC DEMONSTRATION \u2014 NOT OBSERVED ROSSMANN DATA"
_INVALID_MESSAGE = "The synthetic demonstration request is invalid or outside the supported range."
_INTERNAL_MESSAGE = "An internal error occurred."
_MAX_QUERY_BYTES = 4096
_MAX_EMPTY_BODY_MESSAGES = 8
_MAX_QUERY_VALUE_LENGTH = 128
_MAX_DATE_LENGTH = 10
_MAX_RESPONSE_BYTES = 2 * 1024 * 1024
_MAX_SERIALIZATION_DEPTH = 12
_MAX_SERIALIZED_VALUES = 20_000
_MAX_SEQUENCE_ITEMS = 5000
_MAX_STRING_LENGTH = 4096
_MAX_COMPARISON_ROWS = 500
_DEFAULT_COMPARISON_LIMIT = 200
_MANIFEST_PIN = re.compile(r"[0-9a-f]{64}\Z", re.ASCII)
_CANONICAL_INTEGER = re.compile(r"(?:0|[1-9][0-9]*)\Z", re.ASCII)
_ISO_DATE = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}\Z", re.ASCII)


class _SerializationBudget:
    __slots__ = ("visited", "encoded_bytes")

    def __init__(self) -> None:
        self.visited = 0
        self.encoded_bytes = 0


def _charge_serialized_bytes(budget: _SerializationBudget, size: int) -> None:
    budget.encoded_bytes += size
    if budget.encoded_bytes > _MAX_RESPONSE_BYTES:
        raise TypeError("The synthetic result exceeds serialization limits.")


def _json_string_size(value: str) -> int:
    return len(json.dumps(value, ensure_ascii=False).encode("utf-8"))


class _BoundGetRequestMiddleware:
    """Bound query length and reject GET bodies while replaying empty ASGI request messages."""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope.get("type") != "http" or scope.get("method") != "GET":
            await self.app(scope, receive, send)
            return
        query_string = scope.get("query_string", b"")
        if type(query_string) is not bytes or len(query_string) > _MAX_QUERY_BYTES:
            response = _error_response(422, DemoErrorCode.REQUEST.value, _INVALID_MESSAGE)
            await response(scope, receive, send)
            return

        if any(
            name.lower() == b"content-length" and value not in (b"", b"0")
            for name, value in scope.get("headers", ())
        ):
            response = _error_response(422, DemoErrorCode.REQUEST.value, _INVALID_MESSAGE)
            await response(scope, receive, send)
            return

        pending: list[dict[str, Any]] = []
        empty_messages = 0
        while True:
            message = await receive()
            pending.append(message)
            if message["type"] == "http.disconnect":
                return
            if message["type"] == "http.request":
                if message.get("body", b""):
                    response = _error_response(422, DemoErrorCode.REQUEST.value, _INVALID_MESSAGE)
                    await response(scope, receive, send)
                    return
                if not message.get("more_body", False):
                    break
                empty_messages += 1
                if empty_messages >= _MAX_EMPTY_BODY_MESSAGES:
                    response = _error_response(422, DemoErrorCode.REQUEST.value, _INVALID_MESSAGE)
                    await response(scope, receive, send)
                    return

        async def replay_request() -> dict[str, Any]:
            if pending:
                return pending.pop(0)
            return await receive()

        await self.app(scope, replay_request, send)


def _json_value(value: Any, budget: _SerializationBudget, depth: int = 0) -> Any:
    """Serialize only bounded frozen B1 DTOs and exact JSON-compatible primitive values."""
    budget.visited += 1
    if depth > _MAX_SERIALIZATION_DEPTH or budget.visited > _MAX_SERIALIZED_VALUES:
        raise TypeError("The synthetic result exceeds serialization limits.")

    value_type = type(value)
    if value is None:
        _charge_serialized_bytes(budget, 4)
        return value
    if value_type is bool:
        _charge_serialized_bytes(budget, 4 if value else 5)
        return value
    if value_type is int:
        if value.bit_length() > 256:
            raise TypeError("The synthetic result exceeds serialization limits.")
        _charge_serialized_bytes(budget, len(str(value)))
        return value
    if value_type is str:
        if len(value) > _MAX_STRING_LENGTH:
            raise TypeError("The synthetic result exceeds serialization limits.")
        _charge_serialized_bytes(budget, _json_string_size(value))
        return value
    if value_type is float:
        if not math.isfinite(value):
            raise TypeError("The synthetic result contains a non-finite number.")
        _charge_serialized_bytes(budget, len(json.dumps(value, allow_nan=False)))
        return value
    if value_type is date:
        serialized_date = value.isoformat()
        _charge_serialized_bytes(budget, _json_string_size(serialized_date))
        return serialized_date
    if isinstance(value, Enum):
        enum_value = value.value
        if type(enum_value) is str and len(enum_value) <= _MAX_STRING_LENGTH:
            _charge_serialized_bytes(budget, _json_string_size(enum_value))
            return enum_value
        raise TypeError("The synthetic result contains an unsupported enum value.")
    if value_type is tuple:
        if len(value) > _MAX_SEQUENCE_ITEMS:
            raise TypeError("The synthetic result exceeds serialization limits.")
        _charge_serialized_bytes(budget, 2 + max(0, len(value) - 1))
        return [_json_value(item, budget, depth + 1) for item in value]
    if is_dataclass(value) and not isinstance(value, type):
        parameters = getattr(value_type, "__dataclass_params__", None)
        if parameters is None or not parameters.frozen:
            raise TypeError("The synthetic result contains a mutable record.")
        dataclass_fields = fields(value)
        _charge_serialized_bytes(budget, 2 + max(0, len(dataclass_fields) - 1))
        serialized: dict[str, Any] = {}
        for item in dataclass_fields:
            _charge_serialized_bytes(budget, _json_string_size(item.name) + 1)
            serialized[item.name] = _json_value(getattr(value, item.name), budget, depth + 1)
        return serialized
    raise TypeError("The synthetic result contains an unsupported value.")


def _success_response(result: Any) -> Response:
    """Place the exact B1 provenance beside its complete serialized result data."""
    if not is_dataclass(result) or isinstance(result, type):
        raise TypeError("The synthetic service returned an unsupported result.")
    provenance = getattr(result, "provenance", None)
    if type(provenance) is not SyntheticProvenance:
        raise TypeError("The synthetic service result has no verified provenance.")

    budget = _SerializationBudget()
    serialized = _json_value(result, budget)
    if type(serialized) is not dict or "provenance" not in serialized:
        raise TypeError("The synthetic service result has an invalid shape.")
    exact_provenance = serialized.pop("provenance")
    body = {
        "evidence_label": _EVIDENCE_LABEL,
        "data": serialized,
        "provenance": exact_provenance,
    }
    _charge_serialized_bytes(budget, _json_string_size("evidence_label") + 1)
    _charge_serialized_bytes(budget, _json_string_size(_EVIDENCE_LABEL))
    _charge_serialized_bytes(budget, _json_string_size("data") + 1)
    _charge_serialized_bytes(budget, _json_string_size("provenance") + 1)
    encoded = json.dumps(
        body,
        ensure_ascii=False,
        allow_nan=False,
        separators=(",", ":"),
    ).encode("utf-8")
    if len(encoded) > _MAX_RESPONSE_BYTES:
        raise TypeError("The synthetic result exceeds serialization limits.")
    return Response(content=encoded, media_type="application/json")


def _query_values(
    request: Request,
    *,
    allowed: set[str],
    required: set[str],
) -> dict[str, str]:
    parameters = request.query_params
    values: dict[str, str] = {}
    for name in parameters.keys():
        items = parameters.getlist(name)
        if name not in allowed or len(items) != 1:
            raise DemoInvalidRequestError()
        value = items[0]
        if len(value) > _MAX_QUERY_VALUE_LENGTH:
            raise DemoInvalidRequestError()
        values[name] = value
    if not required.issubset(values):
        raise DemoInvalidRequestError()
    return values


def _integer(value: str, *, minimum: int, maximum: int) -> int:
    if _CANONICAL_INTEGER.fullmatch(value) is None:
        raise DemoInvalidRequestError()
    parsed = int(value)
    if not minimum <= parsed <= maximum:
        raise DemoInvalidRequestError()
    return parsed


def _store_id(value: str) -> int:
    store_id = _integer(value, minimum=1, maximum=999)
    if store_id not in (101, 202, 303):
        raise DemoInvalidRequestError()
    return store_id


def _iso_date(value: str) -> date:
    if len(value) != _MAX_DATE_LENGTH or _ISO_DATE.fullmatch(value) is None:
        raise DemoInvalidRequestError()
    try:
        parsed = date.fromisoformat(value)
    except ValueError:
        raise DemoInvalidRequestError() from None
    if parsed.isoformat() != value:
        raise DemoInvalidRequestError()
    return parsed


def create_demo_app(
    *,
    profile: DemoProfile,
    expected_manifest_sha256: str,
    repository_root: Path | None = None,
) -> FastAPI:
    """Build a synthetic-only app from explicit trusted configuration.

    Configuration errors fail factory construction. A valid pin whose release is missing or
    invalid leaves process liveness available but makes every analytical route return 503. The
    one B1 initialization attempt happens here; requests never retry or discover another source.
    """
    if profile is not DemoProfile.CONTROLLED_SYNTHETIC:
        raise ValueError("An explicit supported synthetic profile is required.")
    if (
        type(expected_manifest_sha256) is not str
        or _MANIFEST_PIN.fullmatch(expected_manifest_sha256) is None
    ):
        raise ValueError("An exact lowercase manifest SHA-256 pin is required.")
    if repository_root is not None and not isinstance(repository_root, Path):
        raise TypeError("repository_root must be a trusted pathlib.Path or None.")

    services: DemoServices | None = None
    release_failure: tuple[str, str] | None = None
    try:
        services = DemoServices.open(
            profile=profile,
            expected_manifest_sha256=expected_manifest_sha256,
            repository_root=repository_root,
        )
    except DemoReleaseUnavailableError as exc:
        release_failure = (DemoErrorCode.UNAVAILABLE.value, str(exc))
    except DemoReleaseIntegrityError as exc:
        release_failure = (DemoErrorCode.INTEGRITY.value, str(exc))

    application = FastAPI(
        title="Controlled synthetic demonstration API",
        version="1.0.0",
        docs_url=None,
        redoc_url=None,
        openapi_url=None,
    )

    application.add_middleware(_BoundGetRequestMiddleware)

    @application.exception_handler(DemoInvalidRequestError)
    async def invalid_request_handler(_: Request, exc: DemoInvalidRequestError) -> JSONResponse:
        return _error_response(422, exc.code.value, _INVALID_MESSAGE)

    @application.exception_handler(DemoProviderError)
    async def provider_error_handler(_: Request, exc: DemoProviderError) -> JSONResponse:
        return _error_response(
            503, exc.code.value, "The synthetic demonstration release is unavailable."
        )

    @application.exception_handler(RequestValidationError)
    async def validation_error_handler(_: Request, __: RequestValidationError) -> JSONResponse:
        return _error_response(422, DemoErrorCode.REQUEST.value, _INVALID_MESSAGE)

    application.add_exception_handler(StarletteHTTPException, http_error_handler)

    @application.exception_handler(Exception)
    async def unexpected_error_handler(_: Request, __: Exception) -> JSONResponse:
        return _error_response(500, "internal_error", _INTERNAL_MESSAGE)

    def analytical_response(call: Callable[[DemoServices], Any]) -> Response:
        if services is None:
            if release_failure is None:
                return _error_response(
                    503,
                    DemoErrorCode.UNAVAILABLE.value,
                    "The synthetic demonstration release is unavailable.",
                )
            code, message = release_failure
            return _error_response(503, code, message)
        return _success_response(call(services))

    @application.get("/health")
    def health(request: Request) -> JSONResponse:
        _query_values(request, allowed=set(), required=set())
        return JSONResponse({"status": "ok", "semantics": "process_liveness_only"})

    @application.get("/api/v1/catalog")
    def catalog(request: Request) -> Response:
        _query_values(request, allowed=set(), required=set())
        return analytical_response(lambda current: current.catalog())

    @application.get("/api/v1/history")
    def history(request: Request) -> Response:
        query = _query_values(
            request,
            allowed={"store_id", "start_date", "end_date"},
            required={"store_id", "start_date", "end_date"},
        )
        dto = HistoryQuery(
            store_id=_store_id(query["store_id"]),
            start_date=_iso_date(query["start_date"]),
            end_date=_iso_date(query["end_date"]),
        )
        return analytical_response(lambda current: current.sales_history(dto))

    @application.get("/api/v1/forecasts")
    def forecasts(request: Request) -> Response:
        query = _query_values(
            request,
            allowed={"store_id", "forecast_origin"},
            required={"store_id", "forecast_origin"},
        )
        dto = ForecastQuery(
            store_id=_store_id(query["store_id"]),
            forecast_origin=_iso_date(query["forecast_origin"]),
        )
        return analytical_response(lambda current: current.forecast_issuance(dto))

    @application.get("/api/v1/uncertainty")
    def uncertainty(request: Request) -> Response:
        query = _query_values(
            request,
            allowed={"store_id", "forecast_origin", "fit_id"},
            required={"store_id", "forecast_origin", "fit_id"},
        )
        dto = UncertaintyQuery(
            store_id=_store_id(query["store_id"]),
            forecast_origin=_iso_date(query["forecast_origin"]),
            fit_id=query["fit_id"],
        )
        return analytical_response(lambda current: current.forecast_uncertainty(dto))

    @application.get("/api/v1/model-comparison")
    def model_comparison(request: Request) -> Response:
        allowed = {
            "candidate_id",
            "population",
            "scope",
            "validation_window",
            "horizon",
            "store_id",
            "metric",
            "limit",
        }
        query = _query_values(request, allowed=allowed, required=set())
        string_filters = {
            name: value
            for name in ("candidate_id", "population", "scope", "validation_window", "metric")
            if (value := query.get(name)) is not None
        }
        dto = ModelComparisonQuery(
            **string_filters,
            horizon=(
                _integer(query["horizon"], minimum=1, maximum=14) if "horizon" in query else None
            ),
            store_id=_store_id(query["store_id"]) if "store_id" in query else None,
            limit=(
                _integer(query["limit"], minimum=1, maximum=_MAX_COMPARISON_ROWS)
                if "limit" in query
                else _DEFAULT_COMPARISON_LIMIT
            ),
        )
        return analytical_response(lambda current: current.model_comparison(dto))

    @application.get("/api/v1/inventory")
    def inventory(request: Request) -> Response:
        query = _query_values(
            request,
            allowed={"case_id", "store_id"},
            required={"case_id"},
        )
        dto = InventoryComparisonQuery(
            case_id=query["case_id"],
            store_id=_store_id(query["store_id"]) if "store_id" in query else None,
        )
        return analytical_response(lambda current: current.inventory_comparison(dto))

    return application
