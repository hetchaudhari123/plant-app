# routes/__init__.py

from .auth_router import router as auth_router
from .profile_router import router as profile_router

__all__ = ["auth_router", "profile_router"]
