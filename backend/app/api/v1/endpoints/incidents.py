"""
PEVN Backend — School Coexistence & Student Incidents API Endpoints (Phase 15)

REST Controller for "Observador del Estudiante", Ley 1620 de 2013 due-process cases,
restorative commitments, and teacher/coordinator scope validation.
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
from app.models.coexistence_incident import (
    CoexistenceSituationType,
    IncidentStatus,
)
from app.schemas.incident import (
    IncidentFollowUpPayload,
    IncidentFollowUpResponse,
    StudentIncidentCloseRequest,
    StudentIncidentCreateRequest,
    StudentIncidentListResponse,
    StudentIncidentResponse,
    StudentIncidentUpdateRequest,
)
from app.services.incident_service import CoexistenceIncidentService

router = APIRouter(prefix="/incidents", tags=["Coexistence Incidents"])


def _resolve_institution_id(
    auth: AuthContextDep,
    current_user: CurrentUserDep,
    institution_id_override: uuid.UUID | None = None,
) -> uuid.UUID:
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
    response_model=StudentIncidentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar situación de convivencia en Observador",
    description="Crea una anotación formal o situación Tipo I, II, III (Ley 1620) validando el alcance docente.",
    dependencies=[Depends(require_permission("incidents", "create"))],
)
async def create_incident(
    payload: StudentIncidentCreateRequest,
    db: SessionDep,
    auth: AuthContextDep,
    current_user: CurrentUserDep,
    client_ip: ClientIpDep,
    institution_id: Annotated[
        uuid.UUID | None,
        Query(description="Override for SuperAdmin only"),
    ] = None,
) -> StudentIncidentResponse:
    target_institution_id = _resolve_institution_id(auth, current_user, institution_id)
    correlation_id = correlation_id_ctx.get()

    service = CoexistenceIncidentService(session=db)
    incident = await service.create_incident(
        institution_id=target_institution_id,
        reporter_user=current_user,
        payload=payload,
        auth=auth,
        actor_ip=client_ip,
        correlation_id=correlation_id,
    )
    res = StudentIncidentResponse.model_validate(incident)
    await db.commit()
    return res


@router.get(
    "/{incident_id}",
    response_model=StudentIncidentResponse,
    status_code=status.HTTP_200_OK,
    summary="Consultar detalle de situación de convivencia",
    dependencies=[Depends(require_permission("incidents", "read"))],
)
async def get_incident(
    incident_id: uuid.UUID,
    db: SessionDep,
    auth: AuthContextDep,
    current_user: CurrentUserDep,
    institution_id: Annotated[
        uuid.UUID | None,
        Query(description="Override for SuperAdmin only"),
    ] = None,
) -> StudentIncidentResponse:
    target_institution_id = _resolve_institution_id(auth, current_user, institution_id)
    service = CoexistenceIncidentService(session=db)
    incident = await service.get_incident_by_id(
        incident_id=incident_id,
        institution_id=target_institution_id,
    )
    return StudentIncidentResponse.model_validate(incident)


@router.put(
    "/{incident_id}",
    response_model=StudentIncidentResponse,
    status_code=status.HTTP_200_OK,
    summary="Modificar situación de convivencia",
    dependencies=[Depends(require_permission("incidents", "update"))],
)
async def update_incident(
    incident_id: uuid.UUID,
    payload: StudentIncidentUpdateRequest,
    db: SessionDep,
    auth: AuthContextDep,
    current_user: CurrentUserDep,
    client_ip: ClientIpDep,
    institution_id: Annotated[
        uuid.UUID | None,
        Query(description="Override for SuperAdmin only"),
    ] = None,
) -> StudentIncidentResponse:
    target_institution_id = _resolve_institution_id(auth, current_user, institution_id)
    correlation_id = correlation_id_ctx.get()

    service = CoexistenceIncidentService(session=db)
    incident = await service.update_incident(
        incident_id=incident_id,
        institution_id=target_institution_id,
        caller_user=current_user,
        payload=payload,
        auth=auth,
        actor_ip=client_ip,
        correlation_id=correlation_id,
    )
    res = StudentIncidentResponse.model_validate(incident)
    await db.commit()
    return res


@router.post(
    "/{incident_id}/follow-ups",
    response_model=IncidentFollowUpResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar seguimiento a situación de convivencia",
    dependencies=[Depends(require_permission("incidents", "update"))],
)
async def add_incident_follow_up(
    incident_id: uuid.UUID,
    payload: IncidentFollowUpPayload,
    db: SessionDep,
    auth: AuthContextDep,
    current_user: CurrentUserDep,
    client_ip: ClientIpDep,
    institution_id: Annotated[
        uuid.UUID | None,
        Query(description="Override for SuperAdmin only"),
    ] = None,
) -> IncidentFollowUpResponse:
    target_institution_id = _resolve_institution_id(auth, current_user, institution_id)
    correlation_id = correlation_id_ctx.get()

    service = CoexistenceIncidentService(session=db)
    follow_up = await service.add_follow_up(
        incident_id=incident_id,
        institution_id=target_institution_id,
        author_user=current_user,
        payload=payload,
        auth=auth,
        actor_ip=client_ip,
        correlation_id=correlation_id,
    )
    res = IncidentFollowUpResponse.model_validate(follow_up)
    await db.commit()
    return res


@router.post(
    "/{incident_id}/close",
    response_model=StudentIncidentResponse,
    status_code=status.HTTP_200_OK,
    summary="Cerrar y resolver situación de convivencia",
    dependencies=[Depends(require_permission("incidents", "close"))],
)
async def close_incident(
    incident_id: uuid.UUID,
    payload: StudentIncidentCloseRequest,
    db: SessionDep,
    auth: AuthContextDep,
    current_user: CurrentUserDep,
    client_ip: ClientIpDep,
    institution_id: Annotated[
        uuid.UUID | None,
        Query(description="Override for SuperAdmin only"),
    ] = None,
) -> StudentIncidentResponse:
    target_institution_id = _resolve_institution_id(auth, current_user, institution_id)
    correlation_id = correlation_id_ctx.get()

    service = CoexistenceIncidentService(session=db)
    incident = await service.close_incident(
        incident_id=incident_id,
        institution_id=target_institution_id,
        closed_by_user=current_user,
        payload=payload,
        actor_ip=client_ip,
        correlation_id=correlation_id,
    )
    res = StudentIncidentResponse.model_validate(incident)
    await db.commit()
    return res


@router.get(
    "",
    response_model=StudentIncidentListResponse,
    status_code=status.HTTP_200_OK,
    summary="Listar situaciones de convivencia",
    dependencies=[Depends(require_permission("incidents", "read"))],
)
async def list_incidents(
    db: SessionDep,
    auth: AuthContextDep,
    current_user: CurrentUserDep,
    student_id: Annotated[uuid.UUID | None, Query()] = None,
    situation_type: Annotated[CoexistenceSituationType | None, Query()] = None,
    status_filter: Annotated[IncidentStatus | None, Query(alias="status")] = None,
    institution_id: Annotated[
        uuid.UUID | None,
        Query(description="Override for SuperAdmin only"),
    ] = None,
) -> StudentIncidentListResponse:
    target_institution_id = _resolve_institution_id(auth, current_user, institution_id)
    service = CoexistenceIncidentService(session=db)
    items = await service.list_incidents(
        institution_id=target_institution_id,
        caller_user=current_user,
        auth=auth,
        student_id=student_id,
        situation_type=situation_type,
        status=status_filter,
    )
    return StudentIncidentListResponse(
        items=[StudentIncidentResponse.model_validate(i) for i in items],
        total=len(items),
    )
