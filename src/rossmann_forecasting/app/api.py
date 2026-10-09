"""Thin, local-only HTTP adapter over the approved read-only application services."""

from __future__ import annotations

import re
from datetime import date
from typing import Annotated, Any

from fastapi import FastAPI, Query, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from rossmann_forecasting.app.contracts import (
    ArtifactErrorCode,
    ArtifactReadError,
    ArtifactSelector,
    ForecastQuery,
    HistoryQuery,
    InvalidArtifactRequestError,
    InventoryComparisonQuery,
    ModelComparisonQuery,
    UncertaintyQuery,
)
from rossmann_forecasting.app.services import ApplicationServices, json_safe

_MAX_STORE_ID = 1115
_MAX_MODEL_COMPARISON_LIMIT = 500
_CASE_ID_PATTERN = re.compile(r"[A-Za-z0-9._-]{1,128}")
_ISO_DATE_PATTERN = re.compile(r"\d{4}-\d{2}-\d{2}")
_INVALID_REQUEST_MESSAGE = "The artifact request is invalid or outside the supported range."

StoreId = Annotated[int, Query(ge=1, le=_MAX_STORE_ID)]


def create_app(services: ApplicationServices | None = None) -> FastAPI:
    """Create the read-only demo API, optionally using fixture-backed services."""
    application = FastAPI(
        title="Rossmann development-results API",
        version="1.0.0",
        docs_url=None,
        redoc_url=None,
        openapi_url=None,
    )
    application_services = ApplicationServices() if services is None else services

    @application.exception_handler(ArtifactReadError)
    async def artifact_error_handler(_: Request, exc: ArtifactReadError) -> JSONResponse:
        status_code = (
            422
            if exc.code
            in {ArtifactErrorCode.INVALID_REQUEST, ArtifactErrorCode.UNSUPPORTED_SELECTOR}
            else 503
        )
        return _error_response(status_code, exc.code.value, str(exc))

    @application.exception_handler(RequestValidationError)
    async def request_validation_error_handler(
        _: Request, __: RequestValidationError
    ) -> JSONResponse:
        return _error_response(
            422, ArtifactErrorCode.INVALID_REQUEST.value, _INVALID_REQUEST_MESSAGE
        )

    @application.exception_handler(StarletteHTTPException)
    async def http_error_handler(_: Request, exc: StarletteHTTPException) -> JSONResponse:
        if exc.status_code == 404:
            code, message = "not_found", "The requested endpoint does not exist."
        elif exc.status_code == 405:
            code, message = "method_not_allowed", "The requested HTTP method is not allowed."
        else:
            code, message = "http_error", "The HTTP request could not be completed."
        headers = None
        if exc.status_code == 405 and exc.headers is not None:
            allow = exc.headers.get("Allow")
            if allow is not None:
                headers = {"Allow": allow}
        return _error_response(exc.status_code, code, message, headers=headers)

    @application.exception_handler(Exception)
    async def unexpected_error_handler(_: Request, __: Exception) -> JSONResponse:
        return _error_response(500, "internal_error", "An internal error occurred.")

    @application.get("/health")
    def health(request: Request) -> JSONResponse:
        _reject_unexpected_query(request, set(), ArtifactSelector.PHASE7_FORECASTS)
        return JSONResponse({"status": "ok", "mode": "local_read_only"})

    @application.get("/api/v1/catalog")
    def catalog(request: Request) -> JSONResponse:
        _reject_unexpected_query(request, set(), ArtifactSelector.PHASE7_FORECASTS)
        return _dto_response(application_services.catalog())

    @application.get("/api/v1/forecasts")
    def forecasts(
        request: Request,
        store_id: StoreId,
        forecast_origin: str = Query(..., min_length=1, max_length=10),
    ) -> JSONResponse:
        _reject_unexpected_query(
            request, {"store_id", "forecast_origin"}, ArtifactSelector.PHASE7_FORECASTS
        )
        query = ForecastQuery(
            store_id, _iso_date(forecast_origin, ArtifactSelector.PHASE7_FORECASTS)
        )
        return _dto_response(application_services.forecast_issuance(query))

    @application.get("/api/v1/uncertainty")
    def uncertainty(
        request: Request,
        store_id: StoreId,
        forecast_origin: str = Query(..., min_length=1, max_length=10),
        fit_id: str = Query(..., min_length=1, max_length=1),
    ) -> JSONResponse:
        _reject_unexpected_query(
            request,
            {"store_id", "forecast_origin", "fit_id"},
            ArtifactSelector.PHASE8_DAILY_INTERVALS,
        )
        query = UncertaintyQuery(
            store_id,
            _iso_date(forecast_origin, ArtifactSelector.PHASE8_DAILY_INTERVALS),
            fit_id,
        )
        return _dto_response(application_services.forecast_uncertainty(query))

    @application.get("/api/v1/model-comparison")
    def model_comparison(
        request: Request,
        candidate_id: str | None = Query(default=None, max_length=128),
        population: str | None = Query(default=None, max_length=128),
        scope: str | None = Query(default=None, max_length=128),
        validation_window: str | None = Query(default=None, max_length=128),
        horizon: Annotated[int | None, Query(ge=1, le=14)] = None,
        store_id: StoreId | None = None,
        metric: str | None = Query(default=None, max_length=128),
        limit: Annotated[int, Query(ge=1, le=_MAX_MODEL_COMPARISON_LIMIT)] = 200,
    ) -> JSONResponse:
        _reject_unexpected_query(
            request,
            {
                "candidate_id",
                "population",
                "scope",
                "validation_window",
                "horizon",
                "store_id",
                "metric",
                "limit",
            },
            ArtifactSelector.PHASE7_MODEL_COMPARISON,
        )
        query = ModelComparisonQuery(
            candidate_id=candidate_id,
            population=population,
            scope=scope,
            validation_window=validation_window,
            horizon=horizon,
            store_id=store_id,
            metric=metric,
            limit=limit,
        )
        return _dto_response(application_services.model_comparison(query))

    @application.get("/api/v1/inventory")
    def inventory(
        request: Request,
        case_id: str = Query(..., min_length=1, max_length=128),
        store_id: StoreId | None = None,
    ) -> JSONResponse:
        _reject_unexpected_query(
            request,
            {"case_id", "store_id"},
            ArtifactSelector.PHASE10_COMPARISON,
        )
        if _CASE_ID_PATTERN.fullmatch(case_id) is None:
            raise InvalidArtifactRequestError(ArtifactSelector.PHASE10_COMPARISON)
        query = InventoryComparisonQuery(case_id, store_id)
        return _dto_response(application_services.inventory_comparison(query))

    @application.get("/api/v1/history")
    def history(
        request: Request,
        store_id: StoreId,
        start_date: str = Query(..., min_length=1, max_length=10),
        end_date: str = Query(..., min_length=1, max_length=10),
    ) -> JSONResponse:
        selector = ArtifactSelector.HISTORICAL_SALES
        _reject_unexpected_query(request, {"store_id", "start_date", "end_date"}, selector)
        query = HistoryQuery(
            store_id,
            _iso_date(start_date, selector),
            _iso_date(end_date, selector),
        )
        return _dto_response(application_services.sales_history(query))

    return application


def _reject_unexpected_query(
    request: Request, allowed: set[str], selector: ArtifactSelector
) -> None:
    """Fail closed on unknown or repeated query keys before calling application services."""
    if any(
        name not in allowed or len(request.query_params.getlist(name)) != 1
        for name in request.query_params
    ):
        raise InvalidArtifactRequestError(selector)


def _iso_date(value: str, selector: ArtifactSelector) -> date:
    if _ISO_DATE_PATTERN.fullmatch(value) is None:
        raise InvalidArtifactRequestError(selector)
    try:
        return date.fromisoformat(value)
    except ValueError:
        raise InvalidArtifactRequestError(selector) from None


def _dto_response(value: Any) -> JSONResponse:
    return JSONResponse(content=json_safe(value))


def _error_response(
    status_code: int,
    code: str,
    message: str,
    *,
    headers: dict[str, str] | None = None,
) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={"error": {"code": code, "message": message}},
        headers=headers,
    )


app = create_app()
