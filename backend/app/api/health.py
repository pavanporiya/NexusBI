from typing import Any, Dict
from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session
import structlog
from app.core.dependencies import get_db

logger = structlog.get_logger()
router = APIRouter()


@router.get("/health", response_model=Dict[str, str])
async def health_check() -> Dict[str, str]:
    """Liveness check to verify the service is running."""
    logger.debug("Liveness check hit")
    return {"status": "ok", "service": "NexusBI Backend"}


@router.get("/health/ready", response_model=Dict[str, Any])
async def readiness_check(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Readiness check to verify that all database connection pools are online."""
    checks: Dict[str, str] = {"postgres": "unhealthy"}
    status = "ok"

    # Verify PostgreSQL Metadata DB Connectivity
    try:
        db.execute(text("SELECT 1"))
        checks["postgres"] = "healthy"
    except Exception as e:
        logger.error("Readiness check: PostgreSQL connection failed", error=str(e))
        status = "unhealthy"

    return {
        "status": status,
        "checks": checks,
    }
