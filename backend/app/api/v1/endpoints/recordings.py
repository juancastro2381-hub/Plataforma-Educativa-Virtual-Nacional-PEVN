"""
PEVN Backend — Recordings API Endpoints

REST Controller for synchronizing, publishing, listing, and managing virtual classroom
recording assets, delegating business rules to RecordingService.
"""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import select

from app.api.deps import (
    AuthContextDep,
    ClientIpDep,
    CurrentUserDep,
    SessionDep,
    require_permission,
    resolve_institution_id,
)
from app.core.logging import correlation_id_ctx
from app.core.security.interfaces import SystemRole
from app.exceptions.errors import AuthorizationError
from app.models.virtual_classroom import MeetingRecording, VirtualClassroom
from app.schemas.virtual_classroom import (
    MeetingRecordingListResponse,
    MeetingRecordingResponse,
    PublishRecordingRequest,
)
from app.services.recording_service import RecordingService

router = APIRouter(prefix="/recordings", tags=["Recordings"])


async def _resolve_institution_id(
    db: SessionDep,
    auth: AuthContextDep,
    current_user: CurrentUserDep,
    institution_id_override: uuid.UUID | None = None,
) -> uuid.UUID:
    """Resolve active institution context adhering to tenant isolation."""
    return await resolve_institution_id(
        db=db,
        auth=auth,
        current_user=current_user,
        institution_id_override=institution_id_override,
    )


@router.get(
    "",
    response_model=MeetingRecordingListResponse,
    summary="Listar grabaciones institucionales",
    description="Consulta las grabaciones de la institución respetando visibilidad.",
    dependencies=[Depends(require_permission("recordings", "read"))],
)
async def list_institution_recordings(
    auth: AuthContextDep,
    current_user: CurrentUserDep,
    db: SessionDep,
    classroom_id: Annotated[uuid.UUID | None, Query()] = None,
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    institution_id: Annotated[uuid.UUID | None, Query()] = None,
) -> MeetingRecordingListResponse:
    """List recordings for institution adhering to publication rules."""
    inst_id = await _resolve_institution_id(db, auth, current_user, institution_id)
    service = RecordingService(session=db)
    roles = [r.value for r in auth.roles]

    if classroom_id:
        items, total = await service.list_recordings(
            classroom_id=classroom_id,
            institution_id=inst_id,
            user_roles=roles,
            skip=skip,
            limit=limit,
        )
    else:
        query = (
            select(MeetingRecording)
            .where(MeetingRecording.institution_id == inst_id)
        )
        if SystemRole.STUDENT.value in roles and not any(
            r in roles
            for r in [
                SystemRole.TEACHER.value,
                SystemRole.RECTOR.value,
                SystemRole.COORDINATOR.value,
                SystemRole.DEPARTMENT_ADMIN.value,
                SystemRole.NATIONAL_ADMIN.value,
                SystemRole.SUPERADMIN.value,
            ]
        ):
            query = query.where(MeetingRecording.is_published.is_(True))
        query = query.order_by(MeetingRecording.created_at.desc())
        all_recs = list((await db.execute(query)).scalars().all())
        total = len(all_recs)
        items = all_recs[skip : skip + limit]

    return MeetingRecordingListResponse(
        items=[MeetingRecordingResponse.model_validate(r) for r in items],
        total=total,
    )


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
    inst_id = await _resolve_institution_id(db, auth, current_user, institution_id)
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
    inst_id = await _resolve_institution_id(db, auth, current_user, institution_id)
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
    inst_id = await _resolve_institution_id(db, auth, current_user, institution_id)
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
    inst_id = await _resolve_institution_id(db, auth, current_user, institution_id)
    service = RecordingService(session=db)

    await service.delete_recording(
        recording_id=recording_id,
        institution_id=inst_id,
        actor_id=current_user.id,
        actor_ip=client_ip,
        correlation_id=correlation_id_ctx.get(),
    )
    await db.commit()
