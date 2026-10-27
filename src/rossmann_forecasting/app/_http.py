"""Shared sanitized HTTP errors for the canonical and synthetic API adapters."""

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException


def error_response(
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


async def http_error_handler(_: Request, exc: HTTPException) -> JSONResponse:
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
    return error_response(exc.status_code, code, message, headers=headers)
