"""NexusBI Health Router (v1 namespace).

Re-exports the health router for inclusion under the /api/v1 prefix.
This file exists per the repository blueprint which places health.py
under app/api/v1/routers/.
"""

from app.api.health import router

__all__ = ["router"]
