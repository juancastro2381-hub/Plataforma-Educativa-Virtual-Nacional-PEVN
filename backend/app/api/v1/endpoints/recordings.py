"""
PEVN Backend — Recordings API Endpoints

REST Controller for synchronizing, publishing, listing, and managing virtual classroom
recording assets, delegating business rules to RecordingService.
"""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from app.api.deps import (
    AuthContextDep,
    ClientIpDep,
    CurrentUserDep,
    SessionDep,
    require_permission,
)
from app.core.logging import correlation_id_ctx
from app.core.security.interfaces import SystemRole
from app.exceptions.errors import AuthorizationError
from app.schemas.virtual_classroom import (
    MeetingRecordingListResponse,
    MeetingRecordingResponse,
    PublishRecordingRequest,
)
from app.services.recording_service import RecordingService

router = APIRouter(prefix="/recordings", tags=["Recordings"])


def _resolve_institution_id(
    auth: AuthContextDep,
    current_user: CurrentUserDep,
    institution_id_override: uuid.UUID | None = None,
) -> uuid.UUID:
    """Resolve active institution context adhering to tenant isolation."""
    if (
        SystemRole.SUPERADMIN in auth.roles
        or SystemRole.NATIONAL_ADMIN in auth.roles
        or auth.scope.is_national()
    ) and institution_id_override:
        return institution_id_override
    if current_user.institution_id:
        return current_user.institution_id
    raise AuthorizationError("Contexto institucional no disponible.")


@router.get(
    "/classroom/{classroom_id}",
    response_model=MeetingRecordingListResponse,
    summary="Listar grabaciones del aula virtual",
    description=(
        "Consulta las grabaciones de una sesión. Los estudiantes solo ven "
        "grabaciones publicadas; el personal docente y directivo ve todas."
    ),
    dependencies=[Depends(require_permission("recordings", "read"))],
)
async def list_recordings(
    classroom_id: uuid.UUID,
    auth: AuthContextDep,
    current_user: CurrentUserDep,
    db: SessionDep,
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    institution_id: Annotated[uuid.UUID | None, Query()] = None,
) -> MeetingRecordingListResponse:
    """List session recordings adhering to publication visibility rules."""
    inst_id = _resolve_institution_id(auth, current_user, institution_id)
    service = RecordingService(session=db)

    roles = [r.value for r in auth.roles]
    items, total = await service.list_recordings(
        classroom_id=classroom_id,
        institution_id=inst_id,
        user_roles=roles,
        skip=skip,
        limit=limit,
    )
    return MeetingRecordingListResponse(
        items=[MeetingRecordingResponse.model_validate(r) for r in items],
        total=total,
    )


@router.post(
    "/classroom/{classroom_id}/sync",
    response_model=MeetingRecordingListResponse,
    summary="Sincronizar grabaciones desde el proveedor",
    description="Descubre y registra nuevas grabaciones procesadas por el servidor.",
    dependencies=[Depends(require_permission("recordings", "manage"))],
)
async def sync_recordings(
    classroom_id: uuid.UUID,
    auth: AuthContextDep,
    current_user: CurrentUserDep,
    db: SessionDep,
    client_ip: ClientIpDep,
    institution_id: Annotated[uuid.UUID | None, Query()] = None,
) -> MeetingRecordingListResponse:
    """Synchronize recording assets from meeting provider."""
    inst_id = _resolve_institution_id(auth, current_user, institution_id)
    service = RecordingService(session=db)

    synced = await service.sync_recordings_from_provider(
        classroom_id=classroom_id,
        institution_id=inst_id,
        actor_id=current_user.id,
        actor_ip=client_ip,
        correlation_id=correlation_id_ctx.get(),
    )
    await db.commit()

    return MeetingRecordingListResponse(
        items=[MeetingRecordingResponse.model_validate(r) for r in synced],
        total=len(synced),
    )


@router.patch(
    "/{recording_id}/publish",
    response_model=MeetingRecordingResponse,
    summary="Publicar u ocultar grabación",
    description="Controla la visibilidad de la grabación para los estudiantes.",
    dependencies=[Depends(require_permission("recordings", "manage"))],
)
async def publish_recording(
    recording_id: uuid.UUID,
    payload: PublishRecordingRequest,
    auth: AuthContextDep,
    current_user: CurrentUserDep,
    db: SessionDep,
    client_ip: ClientIpDep,
    institution_id: Annotated[uuid.UUID | None, Query()] = None,
) -> MeetingRecordingResponse:
    """Toggle recording publication status."""
    inst_id = _resolve_institution_id(auth, current_user, institution_id)
    service = RecordingService(session=db)

    recording = await service.publish_recording(
        recording_id=recording_id,
        institution_id=inst_id,
        is_published=payload.is_published,
        actor_id=current_user.id,
        actor_ip=client_ip,
        correlation_id=correlation_id_ctx.get(),
    )
    await db.commit()

    return MeetingRecordingResponse.model_validate(recording)


@router.delete(
    "/{recording_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar grabación",
    description="Elimina el registro de una grabación dentro del tenant.",
    dependencies=[Depends(require_permission("recordings", "delete"))],
)
async def delete_recording(
    recording_id: uuid.UUID,
    auth: AuthContextDep,
    current_user: CurrentUserDep,
    db: SessionDep,
    client_ip: ClientIpDep,
    institution_id: Annotated[uuid.UUID | None, Query()] = None,
) -> None:
    """Delete recording metadata."""
    inst_id = _resolve_institution_id(auth, current_user, institution_id)
    service = RecordingService(session=db)

    await service.delete_recording(
        recording_id=recording_id,
        institution_id=inst_id,
        actor_id=current_user.id,
        actor_ip=client_ip,
        correlation_id=correlation_id_ctx.get(),
    )
    await db.commit()
