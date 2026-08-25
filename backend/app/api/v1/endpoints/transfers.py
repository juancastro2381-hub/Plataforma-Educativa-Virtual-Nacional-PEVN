"""
PEVN Backend — Transfers API Endpoints

REST Controller for student classroom transfers (Traslados de Grupo),
executing atomic group changes with locked capacity checks and immutable audit logging,
delegating business rules to TransferService.
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
)
from app.core.logging import correlation_id_ctx
from app.core.security.interfaces import SystemRole
from app.exceptions.errors import AuthorizationError
from app.models.enrollment import Enrollment, GroupTransferHistory
from app.models.student import Student
from app.schemas.academic import (
    EnrollmentResponse,
    GroupTransferHistoryListResponse,
    GroupTransferHistoryResponse,
    GroupTransferRequest,
    TransferExecutionResponse,
)
from app.services.transfer_service import TransferService

router = APIRouter(prefix="/transfers", tags=["Transfers"])


def _resolve_institution_id(
    auth: AuthContextDep,
    current_user: CurrentUserDep,
    institution_id_override: uuid.UUID | None = None,
) -> uuid.UUID:
    """Resolve active institution context adhering to tenant isolation."""
    if SystemRole.SUPERADMIN in auth.roles and institution_id_override:
        return institution_id_override
    if current_user.institution_id:
        return current_user.institution_id
    raise AuthorizationError("Contexto institucional no disponible.")


@router.post(
    "",
    response_model=TransferExecutionResponse,
    status_code=status.HTTP_200_OK,
    summary="Trasladar estudiante de grupo",
    description="Ejecuta un traslado de salón atómico con bloqueo pesimista.",
    dependencies=[Depends(require_permission("enrollments", "transfer"))],
)
async def transfer_student_group(
    payload: GroupTransferRequest,
    db: SessionDep,
    auth: AuthContextDep,
    current_user: CurrentUserDep,
    client_ip: ClientIpDep,
    institution_id: Annotated[
        uuid.UUID | None,
        Query(description="Override for SuperAdmin only"),
    ] = None,
) -> TransferExecutionResponse:
    target_institution_id = _resolve_institution_id(auth, current_user, institution_id)
    correlation_id = correlation_id_ctx.get()

    service = TransferService(session=db)
    enrollment, history = await service.transfer_student_group(
        enrollment_id=payload.enrollment_id,
        target_group_id=payload.target_group_id,
        institution_id=target_institution_id,
        transferred_by_user_id=current_user.id,
        reason=payload.reason,
        actor_id=current_user.id,
        actor_ip=client_ip,
        correlation_id=correlation_id,
    )
    await db.commit()
    await db.refresh(enrollment)
    await db.refresh(history)

    return TransferExecutionResponse(
        enrollment=EnrollmentResponse.model_validate(enrollment),
        transfer_history=GroupTransferHistoryResponse.model_validate(history),
    )


@router.get(
    "/enrollments/{enrollment_id}/history",
    response_model=GroupTransferHistoryListResponse,
    status_code=status.HTTP_200_OK,
    summary="Consultar historial de traslados de una matrícula",
    description="Lista todos los traslados de salón de una matrícula.",
    dependencies=[Depends(require_permission("enrollments", "read"))],
)
async def get_transfer_history(
    enrollment_id: uuid.UUID,
    db: SessionDep,
    auth: AuthContextDep,
    current_user: CurrentUserDep,
    institution_id: Annotated[
        uuid.UUID | None,
        Query(description="Override for SuperAdmin only"),
    ] = None,
) -> GroupTransferHistoryListResponse:
    target_institution_id = _resolve_institution_id(auth, current_user, institution_id)

    query = (
        select(GroupTransferHistory)
        .join(Enrollment, GroupTransferHistory.enrollment_id == Enrollment.id)
        .join(Student, Enrollment.student_id == Student.id)
        .where(
            GroupTransferHistory.enrollment_id == enrollment_id,
            Student.institution_id == target_institution_id,
        )
        .order_by(GroupTransferHistory.created_at.desc())
    )
    result = await db.execute(query)
    records = list(result.scalars().all())

    return GroupTransferHistoryListResponse(
        items=[GroupTransferHistoryResponse.model_validate(r) for r in records],
        total=len(records),
    )
