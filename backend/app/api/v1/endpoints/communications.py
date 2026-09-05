"""
PEVN Backend — Institutional Communications API Endpoints (Phase 15)

REST Controller for administrative circulars, official announcements,
audience targeting, and acknowledgment metrics.
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
from app.models.communication import (
    CommunicationCategory,
    CommunicationPriority,
    PublishingStatus,
)
from app.schemas.communication import (
    CommunicationCreateRequest,
    CommunicationListResponse,
    CommunicationUpdateRequest,
    InstitutionalCommunicationResponse,
)
from app.services.communication_service import CommunicationService

router = APIRouter(prefix="/communications", tags=["Communications"])


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


@router.post(
    "",
    response_model=InstitutionalCommunicationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear comunicado institucional",
    description="Redacta y publica o guarda como borrador una circular oficial con segmentación de audiencia.",
    dependencies=[Depends(require_permission("communications", "create"))],
)
async def create_communication(
    payload: CommunicationCreateRequest,
    db: SessionDep,
    auth: AuthContextDep,
    current_user: CurrentUserDep,
    client_ip: ClientIpDep,
    institution_id: Annotated[
        uuid.UUID | None,
        Query(description="Override for SuperAdmin only"),
    ] = None,
) -> InstitutionalCommunicationResponse:
    target_institution_id = _resolve_institution_id(auth, current_user, institution_id)
    correlation_id = correlation_id_ctx.get()

    service = CommunicationService(session=db)
    comm = await service.create_communication(
        institution_id=target_institution_id,
        author_user_id=current_user.id,
        payload=payload,
        actor_ip=client_ip,
        correlation_id=correlation_id,
    )
    await db.commit()
    return InstitutionalCommunicationResponse.model_validate(comm)


@router.get(
    "/{communication_id}",
    response_model=InstitutionalCommunicationResponse,
    status_code=status.HTTP_200_OK,
    summary="Consultar comunicado por ID",
    description="Obtiene el detalle oficial de un comunicado validando el tenant.",
    dependencies=[Depends(require_permission("communications", "read"))],
)
async def get_communication(
    communication_id: uuid.UUID,
    db: SessionDep,
    auth: AuthContextDep,
    current_user: CurrentUserDep,
    institution_id: Annotated[
        uuid.UUID | None,
        Query(description="Override for SuperAdmin only"),
    ] = None,
) -> InstitutionalCommunicationResponse:
    target_institution_id = _resolve_institution_id(auth, current_user, institution_id)
    service = CommunicationService(session=db)
    comm = await service.get_communication_by_id(
        communication_id=communication_id,
        institution_id=target_institution_id,
        caller_user=current_user,
        register_read=True,
    )
    await db.commit()

    resp = InstitutionalCommunicationResponse.model_validate(comm)
    resp.total_receipts_count = len(comm.receipts)
    resp.acknowledged_receipts_count = len([r for r in comm.receipts if r.acknowledged_at is not None])
    return resp


@router.put(
    "/{communication_id}",
    response_model=InstitutionalCommunicationResponse,
    status_code=status.HTTP_200_OK,
    summary="Actualizar comunicado institucional",
    description="Modifica el contenido, prioridad o audiencia de una circular.",
    dependencies=[Depends(require_permission("communications", "update"))],
)
async def update_communication(
    communication_id: uuid.UUID,
    payload: CommunicationUpdateRequest,
    db: SessionDep,
    auth: AuthContextDep,
    current_user: CurrentUserDep,
    client_ip: ClientIpDep,
    institution_id: Annotated[
        uuid.UUID | None,
        Query(description="Override for SuperAdmin only"),
    ] = None,
) -> InstitutionalCommunicationResponse:
    target_institution_id = _resolve_institution_id(auth, current_user, institution_id)
    correlation_id = correlation_id_ctx.get()

    service = CommunicationService(session=db)
    comm = await service.update_communication(
        communication_id=communication_id,
        institution_id=target_institution_id,
        payload=payload,
        actor_id=current_user.id,
        actor_ip=client_ip,
        correlation_id=correlation_id,
    )
    await db.commit()
    return InstitutionalCommunicationResponse.model_validate(comm)


@router.post(
    "/{communication_id}/publish",
    response_model=InstitutionalCommunicationResponse,
    status_code=status.HTTP_200_OK,
    summary="Publicar comunicado",
    description="Cambia el estado de un borrador a publicado oficialmente.",
    dependencies=[Depends(require_permission("communications", "publish"))],
)
async def publish_communication(
    communication_id: uuid.UUID,
    db: SessionDep,
    auth: AuthContextDep,
    current_user: CurrentUserDep,
    client_ip: ClientIpDep,
    institution_id: Annotated[
        uuid.UUID | None,
        Query(description="Override for SuperAdmin only"),
    ] = None,
) -> InstitutionalCommunicationResponse:
    target_institution_id = _resolve_institution_id(auth, current_user, institution_id)
    correlation_id = correlation_id_ctx.get()

    service = CommunicationService(session=db)
    comm = await service.publish_communication(
        communication_id=communication_id,
        institution_id=target_institution_id,
        actor_id=current_user.id,
        actor_ip=client_ip,
        correlation_id=correlation_id,
    )
    await db.commit()
    return InstitutionalCommunicationResponse.model_validate(comm)


@router.post(
    "/{communication_id}/archive",
    response_model=InstitutionalCommunicationResponse,
    status_code=status.HTTP_200_OK,
    summary="Archivar comunicado",
    description="Archiva o retira de las bandejas activas un comunicado.",
    dependencies=[Depends(require_permission("communications", "delete"))],
)
async def archive_communication(
    communication_id: uuid.UUID,
    db: SessionDep,
    auth: AuthContextDep,
    current_user: CurrentUserDep,
    client_ip: ClientIpDep,
    institution_id: Annotated[
        uuid.UUID | None,
        Query(description="Override for SuperAdmin only"),
    ] = None,
) -> InstitutionalCommunicationResponse:
    target_institution_id = _resolve_institution_id(auth, current_user, institution_id)
    correlation_id = correlation_id_ctx.get()

    service = CommunicationService(session=db)
    comm = await service.archive_communication(
        communication_id=communication_id,
        institution_id=target_institution_id,
        actor_id=current_user.id,
        actor_ip=client_ip,
        correlation_id=correlation_id,
    )
    await db.commit()
    return InstitutionalCommunicationResponse.model_validate(comm)


@router.get(
    "",
    response_model=CommunicationListResponse,
    status_code=status.HTTP_200_OK,
    summary="Listar comunicados institucionales",
    description="Lista circulares y avisos oficiales de la institución con filtros opcionales.",
    dependencies=[Depends(require_permission("communications", "read"))],
)
async def list_communications(
    db: SessionDep,
    auth: AuthContextDep,
    current_user: CurrentUserDep,
    category: Annotated[CommunicationCategory | None, Query()] = None,
    priority: Annotated[CommunicationPriority | None, Query()] = None,
    status_filter: Annotated[PublishingStatus | None, Query(alias="status")] = None,
    include_expired: Annotated[bool, Query()] = False,
    institution_id: Annotated[
        uuid.UUID | None,
        Query(description="Override for SuperAdmin only"),
    ] = None,
) -> CommunicationListResponse:
    target_institution_id = _resolve_institution_id(auth, current_user, institution_id)
    service = CommunicationService(session=db)
    comms = await service.list_communications(
        institution_id=target_institution_id,
        category=category,
        priority=priority,
        status=status_filter,
        include_expired=include_expired,
    )

    items = []
    for c in comms:
        resp = InstitutionalCommunicationResponse.model_validate(c)
        resp.total_receipts_count = len(c.receipts)
        resp.acknowledged_receipts_count = len([r for r in c.receipts if r.acknowledged_at is not None])
        items.append(resp)

    return CommunicationListResponse(
        items=items,
        total=len(items),
    )
