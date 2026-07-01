from datetime import datetime, timezone
from typing import Any, Dict
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import structlog

logger = structlog.get_logger()


class BaseAppException(Exception):
    """Base application exception for all custom NexusBI errors."""

    def __init__(
        self,
        code: str,
        message: str,
        status_code: int = 500,
        detail: str | None = None,
    ):
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code
        self.detail = detail


class AppValidationError(BaseAppException):
    def __init__(self, message: str, detail: str | None = None):
        super().__init__(
            code="NBI-1001", message=message, status_code=400, detail=detail
        )


class AppAuthenticationError(BaseAppException):
    def __init__(self, message: str = "Invalid credentials", detail: str | None = None):
        super().__init__(
            code="NBI-1002", message=message, status_code=401, detail=detail
        )


class AppAuthorizationError(BaseAppException):
    def __init__(self, message: str = "Permission denied", detail: str | None = None):
        super().__init__(
            code="NBI-1003", message=message, status_code=403, detail=detail
        )


class AIProviderError(BaseAppException):
    def __init__(self, message: str, detail: str | None = None):
        super().__init__(
            code="NBI-2001", message=message, status_code=504, detail=detail
        )


class SQLValidationError(BaseAppException):
    def __init__(self, message: str, detail: str | None = None):
        super().__init__(
            code="NBI-2002", message=message, status_code=422, detail=detail
        )


class WarehouseQueryError(BaseAppException):
    def __init__(self, message: str, detail: str | None = None):
        super().__init__(
            code="NBI-3001", message=message, status_code=500, detail=detail
        )


class WarehouseTimeoutError(BaseAppException):
    def __init__(self, message: str = "Query execution timed out", detail: str | None = None):
        super().__init__(
            code="NBI-3002", message=message, status_code=504, detail=detail
        )


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(BaseAppException)
    async def app_exception_handler(request: Request, exc: BaseAppException) -> JSONResponse:
        logger.error(
            "Application error encountered",
            code=exc.code,
            message=exc.message,
            status_code=exc.status_code,
            detail=exc.detail,
            path=request.url.path,
        )
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "status": "error",
                "error": {
                    "code": exc.code,
                    "message": exc.message,
                    "detail": exc.detail or exc.message,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                },
            },
        )

    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.exception(
            "Unhandled server exception",
            path=request.url.path,
        )
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "error": {
                    "code": "NBI-9999",
                    "message": "An unexpected server error occurred",
                    "detail": str(exc),
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                },
            },
        )
