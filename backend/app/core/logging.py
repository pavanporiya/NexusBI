"""NexusBI Structured Logging Platform.

Provides a production-grade logging configuration engine using structlog
with support for JSON output, console rendering, request correlation IDs,
and audit logging channels.

Architecture Reference:
- phase2_1_repository_blueprint.md Section 6 (Logging Strategy)
- phase2_3_api_service_blueprint.md Section 7 (Observability)
"""

from __future__ import annotations

import logging
import sys
import uuid
from contextvars import ContextVar
from typing import Any

import structlog
from structlog.types import EventDict, WrappedLogger

# ---------------------------------------------------------------------------
# Correlation ID Context Variable
# ---------------------------------------------------------------------------

correlation_id_ctx: ContextVar[str] = ContextVar("correlation_id", default="")


def get_correlation_id() -> str:
    """Return the current correlation ID, generating one if absent."""
    cid = correlation_id_ctx.get("")
    if not cid:
        cid = uuid.uuid4().hex
        correlation_id_ctx.set(cid)
    return cid


def set_correlation_id(cid: str) -> None:
    """Set the correlation ID for the current async context."""
    correlation_id_ctx.set(cid)


def reset_correlation_id() -> None:
    """Reset the correlation ID context variable."""
    correlation_id_ctx.set("")


# ---------------------------------------------------------------------------
# Custom Structlog Processors
# ---------------------------------------------------------------------------


def add_correlation_id(
    _logger: WrappedLogger, _method_name: str, event_dict: EventDict
) -> EventDict:
    """Inject the current correlation ID into every log entry."""
    cid = correlation_id_ctx.get("")
    if cid:
        event_dict["correlation_id"] = cid
    return event_dict


def add_service_context(
    _logger: WrappedLogger, _method_name: str, event_dict: EventDict
) -> EventDict:
    """Inject standard service metadata into every log entry."""
    event_dict.setdefault("service", "nexusbi-backend")
    return event_dict


def censor_sensitive_data(
    _logger: WrappedLogger, _method_name: str, event_dict: EventDict
) -> EventDict:
    """Redact known sensitive field values from log output."""
    sensitive_keys = {
        "password",
        "secret",
        "token",
        "api_key",
        "authorization",
        "secret_key",
        "access_token",
        "refresh_token",
    }
    for key in list(event_dict.keys()):
        if any(s in key.lower() for s in sensitive_keys):
            event_dict[key] = "***REDACTED***"
    return event_dict


# ---------------------------------------------------------------------------
# Logging Configuration
# ---------------------------------------------------------------------------


def configure_logging(
    log_level: int = logging.INFO,
    json_output: bool = True,  # noqa: ARG001
    environment: str = "production",
) -> None:
    """Configure the global logging infrastructure.

    Parameters
    ----------
    log_level:
        The stdlib logging level (e.g., logging.DEBUG).
    _json_output:
        If True, emit structured JSON logs. If False, emit
        human-readable console output.
    environment:
        The current runtime environment name.
    """
    # Build the processor chain
    shared_processors: list[Any] = [
        structlog.contextvars.merge_contextvars,
        add_correlation_id,
        add_service_context,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso", utc=True),
        structlog.processors.StackInfoRenderer(),
        censor_sensitive_data,
        structlog.processors.format_exc_info,
    ]

    # Select renderer based on environment
    if environment == "development" and sys.stdout.isatty():
        renderer: Any = structlog.dev.ConsoleRenderer(colors=True)
    else:
        renderer = structlog.processors.JSONRenderer()

    structlog.configure(
        processors=[*shared_processors, renderer],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    # Bridge stdlib logging through structlog
    formatter = structlog.stdlib.ProcessorFormatter(
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            renderer,
        ],
        foreign_pre_chain=shared_processors,
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.addHandler(handler)
    root_logger.setLevel(log_level)

    # Suppress verbose third-party log output
    for noisy_logger in (
        "uvicorn.access",
        "uvicorn.error",
        "sqlalchemy.engine",
        "httpx",
        "httpcore",
    ):
        logging.getLogger(noisy_logger).setLevel(logging.WARNING)


# ---------------------------------------------------------------------------
# Logger Factory
# ---------------------------------------------------------------------------


def get_logger(
    name: str | None = None, **initial_context: Any
) -> structlog.stdlib.BoundLogger:
    """Return a bound structlog logger with optional initial context.

    Parameters
    ----------
    name:
        An optional logger name, typically the module ``__name__``.
    initial_context:
        Key-value pairs bound to every message emitted by this logger.

    Returns
    -------
    A structlog BoundLogger instance.
    """
    log: structlog.stdlib.BoundLogger = structlog.get_logger(name)
    if initial_context:
        log = log.bind(**initial_context)
    return log


# ---------------------------------------------------------------------------
# Audit Logger
# ---------------------------------------------------------------------------


class AuditLogger:
    """Structured audit logger for compliance-grade event recording.

    Audit entries are emitted as structured log events tagged with
    ``log_type=audit`` so they can be routed by the log aggregation
    pipeline (Loki) to long-term SOC 2 compliant storage.

    Architecture Reference:
    - phase2_1_repository_blueprint.md Section 6.2.1 (Audit Logs)
    """

    def __init__(self) -> None:
        self._logger: structlog.stdlib.BoundLogger = get_logger(
            "nexusbi.audit", log_type="audit"
        )

    def log_query_execution(
        self,
        *,
        user_id: str,
        query_text: str,
        generated_sql: str,
        execution_time_ms: float,
        row_count: int,
        tables_accessed: list[str],
        status: str = "success",
        error: str | None = None,
    ) -> None:
        """Record a user query execution for audit compliance."""
        self._logger.info(
            "query_execution",
            user_id=user_id,
            query_text=query_text,
            generated_sql=generated_sql,
            execution_time_ms=round(execution_time_ms, 2),
            row_count=row_count,
            tables_accessed=tables_accessed,
            status=status,
            error=error,
        )

    def log_llm_transaction(
        self,
        *,
        user_id: str,
        model: str,
        prompt_tokens: int,
        completion_tokens: int,
        latency_ms: float,
        cost_usd: float | None = None,
        status: str = "success",
        retry_count: int = 0,
    ) -> None:
        """Record an LLM API transaction for cost tracking and audit."""
        self._logger.info(
            "llm_transaction",
            user_id=user_id,
            model=model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            latency_ms=round(latency_ms, 2),
            cost_usd=cost_usd,
            status=status,
            retry_count=retry_count,
        )

    def log_security_event(
        self,
        *,
        event_type: str,
        user_id: str | None = None,
        ip_address: str | None = None,
        detail: str,
        severity: str = "warning",
    ) -> None:
        """Record a security event (login failure, rate limit, injection)."""
        log_method = getattr(self._logger, severity, self._logger.warning)
        log_method(
            "security_event",
            event_type=event_type,
            user_id=user_id,
            ip_address=ip_address,
            detail=detail,
        )

    def log_data_access(
        self,
        *,
        user_id: str,
        resource_type: str,
        resource_id: str,
        action: str,
    ) -> None:
        """Record a data access event for SOC 2 compliance."""
        self._logger.info(
            "data_access",
            user_id=user_id,
            resource_type=resource_type,
            resource_id=resource_id,
            action=action,
        )
