"""
PEVN Backend — Virtual Classrooms API Endpoints

REST Controller for virtual classroom scheduling, launching, participant join URL
generation, session termination, and attendance tracking, delegating business rules
to VirtualClassroomService and AttendanceService.
"""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Query, status

from app.api.deps import (
    AuthContextDep,
    ClientIpDep,
    CurrentUserDep,
    SessionDep,
)
from app.core.logging import correlation_id_ctx
from app.core.security.interfaces import SystemRole
from app.exceptions.errors import AuthorizationError
from app.models.virtual_classroom import (
    MeetingAttendance,
    MeetingParticipantRole,
    VirtualClassroomStatus,
)
from app.schemas.virtual_classroom import (
    JoinMeetingResponse,
    MeetingAttendanceListResponse,
    MeetingAttendanceResponse,
    VirtualClassroomCreateRequest,
    VirtualClassroomListResponse,
    VirtualClassroomResponse,
)
from app.services.attendance_service import AttendanceService
from app.services.virtual_classroom_service import VirtualClassroomService

router = APIRouter(prefix="/virtual-classrooms", tags=["Virtual Classrooms"])


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
    response_model=VirtualClassroomResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear aula virtual",
    description=(
        "Programa o crea una nueva sesión de aula virtual asociada o no a una "
        "asignación académica."
    ),
)
async def create_virtual_classroom(
    payload: VirtualClassroomCreateRequest,
    auth: AuthContextDep,
    current_user: CurrentUserDep,
    db: SessionDep,
    client_ip: ClientIpDep,
    institution_id: Annotated[uuid.UUID | None, Query()] = None,
) -> VirtualClassroomResponse:
    """Create a virtual classroom session within tenant boundaries."""
    inst_id = _resolve_institution_id(auth, current_user, institution_id)
    service = VirtualClassroomService(session=db)

    classroom = await service.create_virtual_classroom(
        institution_id=inst_id,
        host_user_id=current_user.id,
        title=payload.title,
        description=payload.description,
        academic_assignment_id=payload.academic_assignment_id,
        scheduled_start_time=payload.scheduled_start_time,
        scheduled_end_time=payload.scheduled_end_time,
        is_recording_enabled=payload.is_recording_enabled,
        is_breakout_enabled=payload.is_breakout_enabled,
        max_participants=payload.max_participants,
        provider_metadata=payload.provider_metadata,
        actor_id=current_user.id,
        actor_ip=client_ip,
        correlation_id=correlation_id_ctx.get(),
    )
    await db.commit()
    return VirtualClassroomResponse.model_validate(classroom)


@router.get(
    "",
    response_model=VirtualClassroomListResponse,
    summary="Listar aulas virtuales",
    description="Consulta aulas virtuales del tenant con filtros y paginación.",
)
async def list_virtual_classrooms(
    auth: AuthContextDep,
    current_user: CurrentUserDep,
    db: SessionDep,
    academic_assignment_id: Annotated[uuid.UUID | None, Query()] = None,
    classroom_status: Annotated[
        VirtualClassroomStatus | None, Query(alias="status")
    ] = None,
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    institution_id: Annotated[uuid.UUID | None, Query()] = None,
) -> VirtualClassroomListResponse:
    """List virtual classrooms within tenant scope."""
    inst_id = _resolve_institution_id(auth, current_user, institution_id)
    service = VirtualClassroomService(session=db)

    items, total = await service.list_virtual_classrooms(
        institution_id=inst_id,
        academic_assignment_id=academic_assignment_id,
        status=classroom_status,
        skip=skip,
        limit=limit,
    )
    return VirtualClassroomListResponse(
        items=[VirtualClassroomResponse.model_validate(c) for c in items],
        total=total,
        skip=skip,
        limit=limit,
    )


@router.get(
    "/{classroom_id}",
    response_model=VirtualClassroomResponse,
    summary="Consultar aula virtual",
    description="Obtiene el detalle de un aula virtual con aislamiento ciego.",
)
async def get_virtual_classroom(
    classroom_id: uuid.UUID,
    auth: AuthContextDep,
    current_user: CurrentUserDep,
    db: SessionDep,
    institution_id: Annotated[uuid.UUID | None, Query()] = None,
) -> VirtualClassroomResponse:
    """Retrieve virtual classroom by ID with tenant isolation."""
    inst_id = _resolve_institution_id(auth, current_user, institution_id)
    service = VirtualClassroomService(session=db)

    classroom = await service.get_virtual_classroom(
        classroom_id=classroom_id,
        institution_id=inst_id,
    )
    return VirtualClassroomResponse.model_validate(classroom)


@router.post(
    "/{classroom_id}/launch",
    response_model=VirtualClassroomResponse,
    summary="Iniciar sesión de aula virtual",
    description="Inicia la reunión en el proveedor y transiciona el estado a RUNNING.",
)
async def launch_virtual_classroom(
    classroom_id: uuid.UUID,
    auth: AuthContextDep,
    current_user: CurrentUserDep,
    db: SessionDep,
    client_ip: ClientIpDep,
    institution_id: Annotated[uuid.UUID | None, Query()] = None,
) -> VirtualClassroomResponse:
    """Launch scheduled virtual classroom session."""
    inst_id = _resolve_institution_id(auth, current_user, institution_id)
    service = VirtualClassroomService(session=db)

    classroom = await service.launch_virtual_classroom(
        classroom_id=classroom_id,
        institution_id=inst_id,
        actor_id=current_user.id,
        actor_ip=client_ip,
        correlation_id=correlation_id_ctx.get(),
    )
    await db.commit()
    return VirtualClassroomResponse.model_validate(classroom)


@router.post(
    "/{classroom_id}/join",
    response_model=JoinMeetingResponse,
    summary="Generar enlace de ingreso",
    description=(
        "Resuelve la autorización (docente moderador vs estudiante activo "
        "matriculado) y genera la URL firmada de entrada."
    ),
)
async def join_virtual_classroom(
    classroom_id: uuid.UUID,
    auth: AuthContextDep,
    current_user: CurrentUserDep,
    db: SessionDep,
    client_ip: ClientIpDep,
    redirect_url: Annotated[str | None, Query()] = None,
    institution_id: Annotated[uuid.UUID | None, Query()] = None,
) -> JoinMeetingResponse:
    """Generate signed join URL for authenticated user based on role and enrollment."""
    inst_id = _resolve_institution_id(auth, current_user, institution_id)
    service = VirtualClassroomService(session=db)

    roles = [r.value for r in auth.roles]
    join_url = await service.generate_join_url(
        classroom_id=classroom_id,
        institution_id=inst_id,
        user=current_user,
        user_roles=roles,
        redirect_url=redirect_url,
        actor_ip=client_ip,
        correlation_id=correlation_id_ctx.get(),
    )
    await db.commit()

    classroom = await service.get_virtual_classroom(
        classroom_id=classroom_id,
        institution_id=inst_id,
    )
    is_host = current_user.id == classroom.host_user_id
    is_admin = any(r in ("rector", "academic_coordinator", "superadmin") for r in roles)
    resolved_role = (
        MeetingParticipantRole.MODERATOR
        if (is_host or is_admin)
        else MeetingParticipantRole.VIEWER
    )

    return JoinMeetingResponse(
        virtual_classroom_id=classroom_id,
        join_url=join_url,
        role=resolved_role,
        meeting_title=classroom.title,
    )


@router.post(
    "/{classroom_id}/end",
    response_model=VirtualClassroomResponse,
    summary="Finalizar aula virtual",
    description="Termina la reunión activa, cierra asistencias y pasa a ENDED.",
)
async def end_virtual_classroom(
    classroom_id: uuid.UUID,
    auth: AuthContextDep,
    current_user: CurrentUserDep,
    db: SessionDep,
    client_ip: ClientIpDep,
    institution_id: Annotated[uuid.UUID | None, Query()] = None,
) -> VirtualClassroomResponse:
    """Terminate active virtual classroom session."""
    inst_id = _resolve_institution_id(auth, current_user, institution_id)
    service = VirtualClassroomService(session=db)

    roles = [r.value for r in auth.roles]
    classroom = await service.end_virtual_classroom(
        classroom_id=classroom_id,
        institution_id=inst_id,
        user_id=current_user.id,
        user_roles=roles,
        actor_ip=client_ip,
        correlation_id=correlation_id_ctx.get(),
    )
    await db.commit()
    return VirtualClassroomResponse.model_validate(classroom)


@router.get(
    "/{classroom_id}/attendances",
    response_model=MeetingAttendanceListResponse,
    summary="Listar asistencias de aula virtual",
    description="Consulta los registros de ingreso, salida y duración de la sesión.",
)
async def list_classroom_attendances(
    classroom_id: uuid.UUID,
    auth: AuthContextDep,
    current_user: CurrentUserDep,
    db: SessionDep,
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=200)] = 100,
    institution_id: Annotated[uuid.UUID | None, Query()] = None,
) -> MeetingAttendanceListResponse:
    """List attendance telemetry for a virtual classroom session."""
    inst_id = _resolve_institution_id(auth, current_user, institution_id)
    att_service = AttendanceService(session=db)

    items, total = await att_service.list_classroom_attendances(
        classroom_id=classroom_id,
        institution_id=inst_id,
        skip=skip,
        limit=limit,
    )

    def _map_attendance(a: MeetingAttendance) -> MeetingAttendanceResponse:
        full_name = (
            f"{a.user.first_name} {a.user.last_name}".strip() if a.user else None
        )
        email = a.user.email if a.user else None
        return MeetingAttendanceResponse(
            id=a.id,
            virtual_classroom_id=a.virtual_classroom_id,
            user_id=a.user_id,
            role=a.role,
            joined_at=a.joined_at,
            left_at=a.left_at,
            duration_seconds=a.duration_seconds,
            user_full_name=full_name,
            user_email=email,
        )

    return MeetingAttendanceListResponse(
        items=[_map_attendance(a) for a in items],
        total=total,
    )


@router.post(
    "/{classroom_id}/leave",
    response_model=MeetingAttendanceResponse | None,
    summary="Registrar salida de reunión",
    description="Marca la hora de desconexión del usuario y calcula la duración.",
)
async def leave_virtual_classroom(
    classroom_id: uuid.UUID,
    current_user: CurrentUserDep,
    db: SessionDep,
) -> MeetingAttendanceResponse | None:
    """Record participant leave event."""
    att_service = AttendanceService(session=db)
    log = await att_service.record_leave(
        classroom_id=classroom_id,
        user_id=current_user.id,
    )
    await db.commit()

    if not log:
        return None

    full_name = (
        f"{current_user.first_name} {current_user.last_name}".strip()
        or current_user.username
    )
    return MeetingAttendanceResponse(
        id=log.id,
        virtual_classroom_id=log.virtual_classroom_id,
        user_id=log.user_id,
        role=log.role,
        joined_at=log.joined_at,
        left_at=log.left_at,
        duration_seconds=log.duration_seconds,
        user_full_name=full_name,
        user_email=current_user.email,
    )
