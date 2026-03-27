from __future__ import annotations

from typing import Any, Dict, Optional

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from loguru import logger
from pydantic import ValidationError as PydanticValidationError


# ---------------------------------------------------------------------------
# Base exception
# ---------------------------------------------------------------------------
class PulseSignalException(HTTPException):
    """Base exception for all PulseSignal Pro domain errors."""

    def __init__(
        self,
        status_code: int,
        detail: str,
        error_code: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> None:
        super().__init__(status_code=status_code, detail=detail, headers=headers)
        self.error_code = error_code or "PULSESIGNAL_ERROR"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "error": True,
            "error_code": self.error_code,
            "detail": self.detail,
            "status_code": self.status_code,
        }


# ---------------------------------------------------------------------------
# Specific domain exceptions
# ---------------------------------------------------------------------------
class AuthenticationError(PulseSignalException):
    """Raised when authentication fails (wrong credentials, expired token, etc.)."""

    def __init__(self, detail: str = "Authentication failed.") -> None:
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            error_code="AUTHENTICATION_ERROR",
            headers={"WWW-Authenticate": "Bearer"},
        )


class AuthorizationError(PulseSignalException):
    """Raised when the user lacks permission to access a resource."""

    def __init__(self, detail: str = "Permission denied.") -> None:
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail,
            error_code="AUTHORIZATION_ERROR",
        )


class NotFoundError(PulseSignalException):
    """Raised when a requested resource does not exist."""

    def __init__(self, resource: str = "Resource", resource_id: Any = None) -> None:
        detail = f"{resource} not found."
        if resource_id is not None:
            detail = f"{resource} with id '{resource_id}' not found."
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=detail,
            error_code="NOT_FOUND",
        )


class ValidationError(PulseSignalException):
    """Raised when business-logic validation fails (distinct from schema validation)."""

    def __init__(self, detail: str = "Validation failed.") -> None:
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=detail,
            error_code="VALIDATION_ERROR",
        )


class RateLimitError(PulseSignalException):
    """Raised when a client exceeds the rate limit."""

    def __init__(
        self,
        detail: str = "Too many requests. Please slow down.",
        retry_after: Optional[int] = None,
    ) -> None:
        headers = {}
        if retry_after is not None:
            headers["Retry-After"] = str(retry_after)
        super().__init__(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=detail,
            error_code="RATE_LIMIT_EXCEEDED",
            headers=headers or None,
        )


class SubscriptionRequiredError(PulseSignalException):
    """Raised when a feature requires a paid subscription."""

    def __init__(
        self,
        detail: str = "This feature requires an active subscription.",
        required_plan: Optional[str] = None,
    ) -> None:
        if required_plan:
            detail = f"This feature requires the '{required_plan}' plan or higher."
        super().__init__(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail=detail,
            error_code="SUBSCRIPTION_REQUIRED",
        )


class ConflictError(PulseSignalException):
    """Raised when a resource already exists (e.g., duplicate email)."""

    def __init__(self, detail: str = "Resource already exists.") -> None:
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail=detail,
            error_code="CONFLICT",
        )


class ServiceUnavailableError(PulseSignalException):
    """Raised when a downstream service (exchange, etc.) is unavailable."""

    def __init__(self, detail: str = "Service temporarily unavailable.") -> None:
        super().__init__(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=detail,
            error_code="SERVICE_UNAVAILABLE",
        )


# ---------------------------------------------------------------------------
# Exception Handlers
# ---------------------------------------------------------------------------
async def _pulsesignal_exception_handler(
    request: Request, exc: PulseSignalException
) -> JSONResponse:
    logger.warning(
        f"PulseSignalException [{exc.error_code}] {request.method} "
        f"{request.url.path} — {exc.detail}"
    )
    return JSONResponse(
        status_code=exc.status_code,
        content=exc.to_dict(),
        headers=exc.headers or {},
    )


async def _http_exception_handler(
    request: Request, exc: HTTPException
) -> JSONResponse:
    logger.warning(
        f"HTTPException [{exc.status_code}] {request.method} "
        f"{request.url.path} — {exc.detail}"
    )
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": True,
            "error_code": "HTTP_ERROR",
            "detail": exc.detail,
            "status_code": exc.status_code,
        },
        headers=getattr(exc, "headers", None) or {},
    )


async def _validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    errors = []
    for error in exc.errors():
        field_path = " -> ".join(str(loc) for loc in error.get("loc", []))
        errors.append(
            {
                "field": field_path,
                "message": error.get("msg", ""),
                "type": error.get("type", ""),
            }
        )
    logger.debug(
        f"Validation error {request.method} {request.url.path}: {errors}"
    )
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": True,
            "error_code": "VALIDATION_ERROR",
            "detail": "Request validation failed.",
            "errors": errors,
            "status_code": 422,
        },
    )


async def _unhandled_exception_handler(
    request: Request, exc: Exception
) -> JSONResponse:
    logger.exception(
        f"Unhandled exception {request.method} {request.url.path}: {exc}"
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": True,
            "error_code": "INTERNAL_SERVER_ERROR",
            "detail": "An unexpected error occurred. Please try again later.",
            "status_code": 500,
        },
    )


def register_exception_handlers(app: FastAPI) -> None:
    """Register all exception handlers on the FastAPI application."""
    app.add_exception_handler(PulseSignalException, _pulsesignal_exception_handler)
    app.add_exception_handler(HTTPException, _http_exception_handler)
    app.add_exception_handler(RequestValidationError, _validation_exception_handler)
    app.add_exception_handler(Exception, _unhandled_exception_handler)
