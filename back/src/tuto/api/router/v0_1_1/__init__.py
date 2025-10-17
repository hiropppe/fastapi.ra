from ...auth.router import router as auth_router
from ..healthcheck_router import router as healthcheck_router
from ...user.router import router as user_router
from .version_router import router as version_router

__all__ = ["auth_router", "healthcheck_router", "user_router", "version_router"]
