"""
PEVN Backend — Student Portal API Endpoints (Phase 14A)

REST Controller providing self-service academic and classroom endpoints for authenticated students:
- GET /student/profile
- GET /student/dashboard
- GET /student/subjects
- GET /student/activities
- GET /student/activities/{activity_id}
- GET /student/grades
- GET /student/attendance
- GET /student/virtual-classrooms
- GET /student/virtual-classrooms/{classroom_id}
- GET /student/virtual-classrooms/{classroom_id}/recordings
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
from app.schemas.incident import (
    StudentIncidentListResponse,
    StudentIncidentResponse,
)
from app.schemas.news import (
    InstitutionalNewsResponse,
    NewsListResponse,
)
from app.schemas.student_portal import (
    StudentActivitiesListResponse,
    StudentActivityItemResponse,
    StudentAttendanceListResponse,
    StudentDashboardResponse,
    StudentGradesListResponse,
    StudentProfileResponse,
    StudentRecordingsListResponse,
    StudentSubjectsListResponse,
    StudentVirtualClassroomItemResponse,
    StudentVirtualClassroomsListResponse,
)
from app.services.communication_service import CommunicationService
from app.services.incident_service import CoexistenceIncidentService
from app.services.news_service import NewsService
from app.services.student_portal_service import StudentPortalService

router = APIRouter(prefix="/student", tags=["Student Portal"])


# ===========================================================================
# 1. Student Profile & Academic Context
# ===========================================================================

@router.get(
    "/profile",
    response_model=StudentProfileResponse,
    status_code=status.HTTP_200_OK,
    summary="Consultar perfil del estudiante autenticado",
    description="Devuelve los datos de identidad, institución, sede, grado y grupo activo del estudiante.",
    dependencies=[Depends(require_permission("students", "read"))],
)
async def get_student_profile(
    current_user: CurrentUserDep,
    db: SessionDep,
) -> StudentProfileResponse:
    service = StudentPortalService(session=db)
    student = await service.get_student_by_user_id(current_user.id, current_user.institution_id)
    return await service.get_profile(student)


# ===========================================================================
# 2. Student Dashboard
# ===========================================================================

@router.get(
    "/dashboard",
    response_model=StudentDashboardResponse,
    status_code=status.HTTP_200_OK,
    summary="Dashboard principal del estudiante",
    description="Devuelve el resumen consolidado de materias, tareas pendientes, próximas clases virtuales y asistencia.",
    dependencies=[Depends(require_permission("students", "read"))],
)
async def get_student_dashboard(
    current_user: CurrentUserDep,
    db: SessionDep,
) -> StudentDashboardResponse:
    service = StudentPortalService(session=db)
    student = await service.get_student_by_user_id(current_user.id, current_user.institution_id)
    return await service.get_dashboard(student)


# ===========================================================================
# 3. Enrolled Subjects (Plan de Estudios)
# ===========================================================================

@router.get(
    "/subjects",
    response_model=StudentSubjectsListResponse,
    status_code=status.HTTP_200_OK,
    summary="Consultar asignaturas matriculadas",
    description="Lista las asignaturas, intensidad horaria y docentes a cargo para el grupo del estudiante.",
    dependencies=[Depends(require_permission("subjects", "read"))],
)
async def list_student_subjects(
    current_user: CurrentUserDep,
    db: SessionDep,
) -> StudentSubjectsListResponse:
    service = StudentPortalService(session=db)
    student = await service.get_student_by_user_id(current_user.id, current_user.institution_id)
    return await service.list_subjects(student)


# ===========================================================================
# 4. Activities / Tasks / Homework
# ===========================================================================

@router.get(
    "/activities",
    response_model=StudentActivitiesListResponse,
    status_code=status.HTTP_200_OK,
    summary="Listar tareas y actividades académicas",
    description="Lista actividades publicadas para el salón del estudiante con estado de entrega y calificación.",
    dependencies=[Depends(require_permission("activities", "read"))],
)
async def list_student_activities(
    current_user: CurrentUserDep,
    db: SessionDep,
    subject_id: Annotated[uuid.UUID | None, Query(description="Filtrar por asignatura")] = None,
    submission_status: Annotated[str | None, Query(description="Filtrar por estado: PENDING, OVERDUE, SUBMITTED, GRADED")] = None,
) -> StudentActivitiesListResponse:
    service = StudentPortalService(session=db)
    student = await service.get_student_by_user_id(current_user.id, current_user.institution_id)
    return await service.list_activities(
        student,
        subject_id=subject_id,
        submission_status=submission_status,
    )


@router.get(
    "/activities/{activity_id}",
    response_model=StudentActivityItemResponse,
    status_code=status.HTTP_200_OK,
    summary="Consultar detalle de actividad académica",
    description="Obtiene las instrucciones, enlaces y calificación de una tarea autorizada para el estudiante.",
    dependencies=[Depends(require_permission("activities", "read"))],
)
async def get_student_activity_detail(
    activity_id: uuid.UUID,
    current_user: CurrentUserDep,
    db: SessionDep,
) -> StudentActivityItemResponse:
    service = StudentPortalService(session=db)
    student = await service.get_student_by_user_id(current_user.id, current_user.institution_id)
    return await service.get_activity_detail(student, activity_id)


# ===========================================================================
# 5. Grades & Evaluations
# ===========================================================================

@router.get(
    "/grades",
    response_model=StudentGradesListResponse,
    status_code=status.HTTP_200_OK,
    summary="Consultar calificaciones del estudiante",
    description="Devuelve el historial de evaluaciones calificadas con retroalimentación del docente.",
    dependencies=[Depends(require_permission("grades", "read"))],
)
async def list_student_grades(
    current_user: CurrentUserDep,
    db: SessionDep,
    subject_id: Annotated[uuid.UUID | None, Query(description="Filtrar por asignatura")] = None,
) -> StudentGradesListResponse:
    service = StudentPortalService(session=db)
    student = await service.get_student_by_user_id(current_user.id, current_user.institution_id)
    return await service.list_grades(student, subject_id=subject_id)


# ===========================================================================
# 6. Daily Attendance
# ===========================================================================

@router.get(
    "/attendance",
    response_model=StudentAttendanceListResponse,
    status_code=status.HTTP_200_OK,
    summary="Consultar registro de asistencia escolar",
    description="Devuelve el historial de asistencias, inasistencias y porcentaje de asistencia.",
    dependencies=[Depends(require_permission("attendance", "read"))],
)
async def list_student_attendance(
    current_user: CurrentUserDep,
    db: SessionDep,
    start_date: Annotated[date | None, Query(description="Fecha inicio")] = None,
    end_date: Annotated[date | None, Query(description="Fecha fin")] = None,
) -> StudentAttendanceListResponse:
    service = StudentPortalService(session=db)
    student = await service.get_student_by_user_id(current_user.id, current_user.institution_id)
    return await service.list_attendance(student, start_date=start_date, end_date=end_date)


# ===========================================================================
# 7. Virtual Classrooms & Recordings
# ===========================================================================

@router.get(
    "/virtual-classrooms",
    response_model=StudentVirtualClassroomsListResponse,
    status_code=status.HTTP_200_OK,
    summary="Listar aulas virtuales disponibles",
    description="Devuelve las sesiones de clase virtual programadas para el grupo del estudiante.",
    dependencies=[Depends(require_permission("virtual_classrooms", "read"))],
)
async def list_student_virtual_classrooms(
    current_user: CurrentUserDep,
    db: SessionDep,
) -> StudentVirtualClassroomsListResponse:
    service = StudentPortalService(session=db)
    student = await service.get_student_by_user_id(current_user.id, current_user.institution_id)
    return await service.list_virtual_classrooms(student)


@router.get(
    "/virtual-classrooms/{classroom_id}",
    response_model=StudentVirtualClassroomItemResponse,
    status_code=status.HTTP_200_OK,
    summary="Consultar aula virtual para ingreso",
    description="Devuelve la información de sesión para unirse a la clase en vivo.",
    dependencies=[Depends(require_permission("virtual_classrooms", "read"))],
)
async def get_student_virtual_classroom(
    classroom_id: uuid.UUID,
    current_user: CurrentUserDep,
    db: SessionDep,
) -> StudentVirtualClassroomItemResponse:
    service = StudentPortalService(session=db)
    student = await service.get_student_by_user_id(current_user.id, current_user.institution_id)
    return await service.get_virtual_classroom(student, classroom_id)


@router.get(
    "/virtual-classrooms/{classroom_id}/recordings",
    response_model=StudentRecordingsListResponse,
    status_code=status.HTTP_200_OK,
    summary="Consultar grabaciones de una clase virtual",
    description="Lista las grabaciones disponibles para una sesión autorizada del estudiante.",
    dependencies=[Depends(require_permission("recordings", "read"))],
)
async def list_student_recordings(
    classroom_id: uuid.UUID,
    current_user: CurrentUserDep,
    db: SessionDep,
) -> StudentRecordingsListResponse:
    service = StudentPortalService(session=db)
    student = await service.get_student_by_user_id(current_user.id, current_user.institution_id)
    return await service.list_recordings(student, classroom_id)


# ===========================================================================
# 8. Institutional Communications, News & Coexistence (Phase 15)
# ===========================================================================

@router.get(
    "/communications",
    response_model=CommunicationListResponse,
    status_code=status.HTTP_200_OK,
    summary="Listar comunicados dirigidos al estudiante",
    dependencies=[Depends(require_permission("communications", "read"))],
)
async def list_student_communications(
    current_user: CurrentUserDep,
    db: SessionDep,
) -> CommunicationListResponse:
    portal_service = StudentPortalService(session=db)
    student = await portal_service.get_student_by_user_id(current_user.id, current_user.institution_id)

    comm_service = CommunicationService(session=db)
    tuples = await comm_service.list_student_communications(
        student=student,
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
async def get_student_communication(
    communication_id: uuid.UUID,
    current_user: CurrentUserDep,
    db: SessionDep,
) -> InstitutionalCommunicationResponse:
    portal_service = StudentPortalService(session=db)
    student = await portal_service.get_student_by_user_id(current_user.id, current_user.institution_id)

    comm_service = CommunicationService(session=db)
    comm = await comm_service.get_communication_by_id(
        communication_id=communication_id,
        institution_id=student.institution_id,
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
    summary="Confirmar acuse de recibo de comunicado",
    dependencies=[Depends(require_permission("communications", "read"))],
)
async def acknowledge_student_communication(
    communication_id: uuid.UUID,
    current_user: CurrentUserDep,
    db: SessionDep,
    client_ip: ClientIpDep,
) -> CommunicationReceiptResponse:
    portal_service = StudentPortalService(session=db)
    student = await portal_service.get_student_by_user_id(current_user.id, current_user.institution_id)

    comm_service = CommunicationService(session=db)
    receipt = await comm_service.acknowledge_communication(
        communication_id=communication_id,
        institution_id=student.institution_id,
        user=current_user,
        client_ip=client_ip,
    )
    await db.commit()
    return CommunicationReceiptResponse.model_validate(receipt)


@router.get(
    "/news",
    response_model=NewsListResponse,
    status_code=status.HTTP_200_OK,
    summary="Listar noticias institucionales para el estudiante",
    dependencies=[Depends(require_permission("news", "read"))],
)
async def list_student_news(
    current_user: CurrentUserDep,
    db: SessionDep,
) -> NewsListResponse:
    portal_service = StudentPortalService(session=db)
    student = await portal_service.get_student_by_user_id(current_user.id, current_user.institution_id)

    news_service = NewsService(session=db)
    items = await news_service.list_news(
        institution_id=student.institution_id,
    )
    return NewsListResponse(
        items=[InstitutionalNewsResponse.model_validate(n) for n in items],
        total=len(items),
    )


@router.get(
    "/incidents",
    response_model=StudentIncidentListResponse,
    status_code=status.HTTP_200_OK,
    summary="Consultar Observador del estudiante propio",
    description="Devuelve las anotaciones de convivencia escolar visibles para el estudiante (DECISION-15-01).",
    dependencies=[Depends(require_permission("incidents", "read"))],
)
async def list_student_incidents(
    current_user: CurrentUserDep,
    db: SessionDep,
) -> StudentIncidentListResponse:
    portal_service = StudentPortalService(session=db)
    student = await portal_service.get_student_by_user_id(current_user.id, current_user.institution_id)

    incident_service = CoexistenceIncidentService(session=db)
    incidents = await incident_service.list_student_incidents(student=student)
    return StudentIncidentListResponse(
        items=[StudentIncidentResponse.model_validate(i) for i in incidents],
        total=len(incidents),
    )

