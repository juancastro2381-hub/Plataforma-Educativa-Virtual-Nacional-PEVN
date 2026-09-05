"""
PEVN Backend — Guardian Portal API Endpoints (Phase 14A)

REST Controller providing family follow-up and monitoring endpoints for authenticated guardians:
- GET /guardian/profile
- GET /guardian/students
- GET /guardian/students/{student_id}/overview
- GET /guardian/students/{student_id}/activities
- GET /guardian/students/{student_id}/grades
- GET /guardian/students/{student_id}/attendance
- GET /guardian/students/{student_id}/virtual-classrooms
- GET /guardian/students/{student_id}/virtual-classrooms/{classroom_id}
"""

from __future__ import annotations

import uuid
from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from app.api.deps import (
    ClientIpDep,
    CurrentUserDep,
    SessionDep,
    require_permission,
)
from app.schemas.communication import (
    CommunicationListResponse,
    CommunicationReceiptResponse,
    InstitutionalCommunicationResponse,
)
from app.schemas.guardian_portal import (
    GuardianChildActivitiesListResponse,
    GuardianChildAttendanceListResponse,
    GuardianChildGradesListResponse,
    GuardianChildOverviewResponse,
    GuardianChildVirtualClassroomsListResponse,
    GuardianChildrenListResponse,
    GuardianProfileResponse,
)
from app.schemas.incident import (
    StudentIncidentListResponse,
    StudentIncidentResponse,
)
from app.schemas.news import (
    InstitutionalNewsResponse,
    NewsListResponse,
)
from app.schemas.student_portal import StudentVirtualClassroomItemResponse
from app.services.communication_service import CommunicationService
from app.services.guardian_portal_service import GuardianPortalService
from app.services.incident_service import CoexistenceIncidentService
from app.services.news_service import NewsService

router = APIRouter(prefix="/guardian", tags=["Guardian Portal"])


# ===========================================================================
# 1. Guardian Profile
# ===========================================================================

@router.get(
    "/profile",
    response_model=GuardianProfileResponse,
    status_code=status.HTTP_200_OK,
    summary="Consultar perfil del acudiente autenticado",
    description="Devuelve la información de contacto y total de estudiantes tutorados vinculados.",
    dependencies=[Depends(require_permission("guardians", "read"))],
)
async def get_guardian_profile(
    current_user: CurrentUserDep,
    db: SessionDep,
) -> GuardianProfileResponse:
    service = GuardianPortalService(session=db)
    guardian = await service.get_guardian_by_user_id(current_user.id, current_user.institution_id)
    return await service.get_profile(guardian)


# ===========================================================================
# 2. Linked Children / Tutorados (Context Switcher)
# ===========================================================================

@router.get(
    "/students",
    response_model=GuardianChildrenListResponse,
    status_code=status.HTTP_200_OK,
    summary="Listar estudiantes autorizados (Selector de Hijos)",
    description="Devuelve la lista de estudiantes legalmente vinculados al acudiente en esta institución.",
    dependencies=[Depends(require_permission("students", "read"))],
)
async def list_guardian_students(
    current_user: CurrentUserDep,
    db: SessionDep,
) -> GuardianChildrenListResponse:
    service = GuardianPortalService(session=db)
    guardian = await service.get_guardian_by_user_id(current_user.id, current_user.institution_id)
    return await service.list_authorized_students(guardian)


# ===========================================================================
# 3. Child Academic Overview
# ===========================================================================

@router.get(
    "/students/{student_id}/overview",
    response_model=GuardianChildOverviewResponse,
    status_code=status.HTTP_200_OK,
    summary="Resumen académico y alertas del estudiante tutorado",
    description="Consolidado de tareas pendientes, promedio académico, asistencia y clases virtuales del hijo.",
    dependencies=[Depends(require_permission("students", "read"))],
)
async def get_child_overview(
    student_id: uuid.UUID,
    current_user: CurrentUserDep,
    db: SessionDep,
) -> GuardianChildOverviewResponse:
    service = GuardianPortalService(session=db)
    guardian = await service.get_guardian_by_user_id(current_user.id, current_user.institution_id)
    return await service.get_child_overview(guardian, student_id)


# ===========================================================================
# 4. Child Homework / Tasks Follow-up
# ===========================================================================

@router.get(
    "/students/{student_id}/activities",
    response_model=GuardianChildActivitiesListResponse,
    status_code=status.HTTP_200_OK,
    summary="Seguimiento de tareas y deberes escolares del estudiante",
    description="Lista de tareas del hijo con estado de entrega y calificación (Modo seguimiento / No entrega).",
    dependencies=[Depends(require_permission("activities", "read"))],
)
async def list_child_activities(
    student_id: uuid.UUID,
    current_user: CurrentUserDep,
    db: SessionDep,
    subject_id: Annotated[uuid.UUID | None, Query(description="Filtrar por asignatura")] = None,
    submission_status: Annotated[str | None, Query(description="Filtrar por estado: PENDING, OVERDUE, SUBMITTED, GRADED")] = None,
) -> GuardianChildActivitiesListResponse:
    service = GuardianPortalService(session=db)
    guardian = await service.get_guardian_by_user_id(current_user.id, current_user.institution_id)
    return await service.list_child_activities(
        guardian,
        student_id,
        subject_id=subject_id,
        submission_status=submission_status,
    )


# ===========================================================================
# 5. Child Grades & Evaluations
# ===========================================================================

@router.get(
    "/students/{student_id}/grades",
    response_model=GuardianChildGradesListResponse,
    status_code=status.HTTP_200_OK,
    summary="Consultar calificaciones del estudiante tutorado",
    description="Historial de evaluaciones, notas y observaciones pedagógicas docentes del hijo.",
    dependencies=[Depends(require_permission("grades", "read"))],
)
async def list_child_grades(
    student_id: uuid.UUID,
    current_user: CurrentUserDep,
    db: SessionDep,
    subject_id: Annotated[uuid.UUID | None, Query(description="Filtrar por asignatura")] = None,
) -> GuardianChildGradesListResponse:
    service = GuardianPortalService(session=db)
    guardian = await service.get_guardian_by_user_id(current_user.id, current_user.institution_id)
    return await service.list_child_grades(
        guardian,
        student_id,
        subject_id=subject_id,
    )


# ===========================================================================
# 6. Child Attendance
# ===========================================================================

@router.get(
    "/students/{student_id}/attendance",
    response_model=GuardianChildAttendanceListResponse,
    status_code=status.HTTP_200_OK,
    summary="Consultar asistencia escolar del estudiante tutorado",
    description="Registro diario de asistencias, fallas y justificaciones del hijo.",
    dependencies=[Depends(require_permission("attendance", "read"))],
)
async def list_child_attendance(
    student_id: uuid.UUID,
    current_user: CurrentUserDep,
    db: SessionDep,
    start_date: Annotated[date | None, Query(description="Fecha inicio")] = None,
    end_date: Annotated[date | None, Query(description="Fecha fin")] = None,
) -> GuardianChildAttendanceListResponse:
    service = GuardianPortalService(session=db)
    guardian = await service.get_guardian_by_user_id(current_user.id, current_user.institution_id)
    return await service.list_child_attendance(
        guardian,
        student_id,
        start_date=start_date,
        end_date=end_date,
    )


# ===========================================================================
# 7. Child Virtual Classrooms
# ===========================================================================

@router.get(
    "/students/{student_id}/virtual-classrooms",
    response_model=GuardianChildVirtualClassroomsListResponse,
    status_code=status.HTTP_200_OK,
    summary="Consultar agenda de clases virtuales del estudiante",
    description="Cronograma de sesiones virtuales programadas para el grupo del hijo.",
    dependencies=[Depends(require_permission("students", "read"))],
)
async def list_child_virtual_classrooms(
    student_id: uuid.UUID,
    current_user: CurrentUserDep,
    db: SessionDep,
) -> GuardianChildVirtualClassroomsListResponse:
    service = GuardianPortalService(session=db)
    guardian = await service.get_guardian_by_user_id(current_user.id, current_user.institution_id)
    return await service.list_child_virtual_classrooms(guardian, student_id)


@router.get(
    "/students/{student_id}/virtual-classrooms/{classroom_id}",
    response_model=StudentVirtualClassroomItemResponse,
    status_code=status.HTTP_200_OK,
    summary="Consultar detalle de agenda de sesión virtual",
    description="Detalle de horario y asignatura de la clase programada del hijo.",
    dependencies=[Depends(require_permission("students", "read"))],
)
async def get_child_virtual_classroom(
    student_id: uuid.UUID,
    classroom_id: uuid.UUID,
    current_user: CurrentUserDep,
    db: SessionDep,
) -> StudentVirtualClassroomItemResponse:
    service = GuardianPortalService(session=db)
    guardian = await service.get_guardian_by_user_id(current_user.id, current_user.institution_id)
    return await service.get_child_virtual_classroom(guardian, student_id, classroom_id)


# ===========================================================================
# 8. Institutional Communications, News & Coexistence (Phase 15)
# ===========================================================================

@router.get(
    "/communications",
    response_model=CommunicationListResponse,
    status_code=status.HTTP_200_OK,
    summary="Listar comunicados dirigidos al acudiente",
    dependencies=[Depends(require_permission("communications", "read"))],
)
async def list_guardian_communications(
    current_user: CurrentUserDep,
    db: SessionDep,
) -> CommunicationListResponse:
    portal_service = GuardianPortalService(session=db)
    guardian = await portal_service.get_guardian_by_user_id(current_user.id, current_user.institution_id)

    comm_service = CommunicationService(session=db)
    tuples = await comm_service.list_guardian_communications(
        guardian=guardian,
        user=current_user,
    )

    items = []
    unread_count = 0
    for comm, is_read, is_ack in tuples:
        resp = InstitutionalCommunicationResponse.model_validate(comm)
        resp.is_read = is_read
        resp.is_acknowledged = is_ack
        if not is_read:
            unread_count += 1
        items.append(resp)

    return CommunicationListResponse(
        items=items,
        total=len(items),
        unread_count=unread_count,
    )


@router.get(
    "/communications/{communication_id}",
    response_model=InstitutionalCommunicationResponse,
    status_code=status.HTTP_200_OK,
    summary="Consultar comunicado oficial y registrar lectura",
    dependencies=[Depends(require_permission("communications", "read"))],
)
async def get_guardian_communication(
    communication_id: uuid.UUID,
    current_user: CurrentUserDep,
    db: SessionDep,
) -> InstitutionalCommunicationResponse:
    portal_service = GuardianPortalService(session=db)
    guardian = await portal_service.get_guardian_by_user_id(current_user.id, current_user.institution_id)

    comm_service = CommunicationService(session=db)
    comm = await comm_service.get_communication_by_id(
        communication_id=communication_id,
        institution_id=guardian.institution_id,
        caller_user=current_user,
        register_read=True,
    )
    await db.commit()

    receipt = next((r for r in comm.receipts if r.user_id == current_user.id), None)
    resp = InstitutionalCommunicationResponse.model_validate(comm)
    resp.is_read = True
    resp.is_acknowledged = receipt.is_acknowledged if receipt else False
    resp.read_at = receipt.read_at if receipt else None
    resp.acknowledged_at = receipt.acknowledged_at if receipt else None
    return resp


@router.post(
    "/communications/{communication_id}/acknowledge",
    response_model=CommunicationReceiptResponse,
    status_code=status.HTTP_200_OK,
    summary="Confirmar acuse de recibo de comunicado por el acudiente",
    dependencies=[Depends(require_permission("communications", "read"))],
)
async def acknowledge_guardian_communication(
    communication_id: uuid.UUID,
    current_user: CurrentUserDep,
    db: SessionDep,
    client_ip: ClientIpDep,
) -> CommunicationReceiptResponse:
    portal_service = GuardianPortalService(session=db)
    guardian = await portal_service.get_guardian_by_user_id(current_user.id, current_user.institution_id)

    comm_service = CommunicationService(session=db)
    receipt = await comm_service.acknowledge_communication(
        communication_id=communication_id,
        institution_id=guardian.institution_id,
        user=current_user,
        client_ip=client_ip,
    )
    await db.commit()
    return CommunicationReceiptResponse.model_validate(receipt)


@router.get(
    "/news",
    response_model=NewsListResponse,
    status_code=status.HTTP_200_OK,
    summary="Listar noticias institucionales para el acudiente",
    dependencies=[Depends(require_permission("news", "read"))],
)
async def list_guardian_news(
    current_user: CurrentUserDep,
    db: SessionDep,
) -> NewsListResponse:
    portal_service = GuardianPortalService(session=db)
    guardian = await portal_service.get_guardian_by_user_id(current_user.id, current_user.institution_id)

    news_service = NewsService(session=db)
    items = await news_service.list_news(
        institution_id=guardian.institution_id,
    )
    return NewsListResponse(
        items=[InstitutionalNewsResponse.model_validate(n) for n in items],
        total=len(items),
    )


@router.get(
    "/students/{student_id}/incidents",
    response_model=StudentIncidentListResponse,
    status_code=status.HTTP_200_OK,
    summary="Consultar Observador y situaciones de convivencia de su hijo",
    description="Devuelve las anotaciones de convivencia del estudiante legalmente vinculado si están autorizadas para acudientes.",
    dependencies=[Depends(require_permission("incidents", "read"))],
)
async def list_guardian_child_incidents(
    student_id: uuid.UUID,
    current_user: CurrentUserDep,
    db: SessionDep,
) -> StudentIncidentListResponse:
    portal_service = GuardianPortalService(session=db)
    guardian = await portal_service.get_guardian_by_user_id(current_user.id, current_user.institution_id)

    incident_service = CoexistenceIncidentService(session=db)
    incidents = await incident_service.list_guardian_student_incidents(
        guardian=guardian,
        student_id=student_id,
    )
    return StudentIncidentListResponse(
        items=[StudentIncidentResponse.model_validate(i) for i in incidents],
        total=len(incidents),
    )

