"""
PEVN Backend — FastAPI Dependencies

Reusable FastAPI dependency functions.
These are the building blocks for route-level dependency injection.

Phase 1 provides:
  - get_async_session: Database session per request
  - get_settings: Application configuration

Phase 2 will add:
  - get_current_user: Authenticated user extraction from token
  - require_permission: Authorization guard factory
  - get_audit_service: Audit service injection
"""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.db.session import get_async_session

# Re-export for convenient import by route modules
__all__ = [
    "SessionDep",
    "SettingsDep",
    "get_async_session",
    "get_settings",
]

# Type aliases for FastAPI dependency injection
# Usage: async def endpoint(db: SessionDep, settings: SettingsDep)
SessionDep = Annotated[AsyncSession, Depends(get_async_session)]
SettingsDep = Annotated[Settings, Depends(get_settings)]
