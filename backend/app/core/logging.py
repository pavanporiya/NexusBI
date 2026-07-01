import logging
import sys
from typing import Any
import structlog
from app.core.config import settings


def configure_logging() -> None:
    # Setup standard logging configuration
    log_level = logging.DEBUG if settings.DEBUG else logging.INFO

    # Define structlog processors
    processors: list[Any] = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso", utc=True),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]

    if settings.ENV == "development" and not sys.stdout.isatty():
        # Clean formatting in developmental containers or files
        processors.append(structlog.processors.JSONRenderer())
    elif settings.ENV == "development":
        # Colorful logging for standard console terminal runtimes
        processors.append(structlog.dev.ConsoleRenderer(colors=True))
    else:
        # Standard JSON formatting for production containers
        processors.append(structlog.processors.JSONRenderer())

    structlog.configure(
        processors=processors,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    # Bridge standard logging to use structlog
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(structlog.stdlib.ProcessorFormatter(
        processor=structlog.processors.JSONRenderer() if settings.ENV != "development" else structlog.dev.ConsoleRenderer()
    ))

    root_logger = logging.getLogger()
    root_logger.handlers = [handler]
    root_logger.setLevel(log_level)

    # Disable verbose third-party logs
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.error").setLevel(logging.WARNING)
