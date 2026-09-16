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

from fastapi import APIRouter, Depends, File, Query, Request, Response, UploadFile, status
from fastapi.responses import FileResponse

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
    StudentActivityResourceListResponse,
    StudentAttendanceItemResponse,
    StudentAttendanceListResponse,
    StudentAttendanceSummary,
    StudentDashboardResponse,
    StudentGradeItemResponse,
    StudentGradesListResponse,
    StudentProfileResponse,
    StudentRecordingItemResponse,
    StudentRecordingsListResponse,
    StudentSubmissionAttemptResponse,
    StudentSubmissionDetailResponse,
    StudentSubmissionDraftUpdateRequest,
    StudentSubjectItemResponse,
    StudentSubjectsListResponse,
    StudentVirtualClassroomItemResponse,
    StudentVirtualClassroomsListResponse,
    SubmissionAttachmentItemResponse,
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


@router.get(
    "/activities/{activity_id}/resources",
    response_model=StudentActivityResourceListResponse,
    status_code=status.HTTP_200_OK,
    summary="Listar materiales / recursos de una actividad (Estudiante)",
    description="Lista los recursos pedagógicos autorizados asociados a la actividad del grupo del estudiante.",
    dependencies=[Depends(require_permission("activities", "read"))],
)
async def list_student_activity_resources(
    activity_id: uuid.UUID,
    current_user: CurrentUserDep,
    db: SessionDep,
) -> StudentActivityResourceListResponse:
    service = StudentPortalService(session=db)
    student = await service.get_student_by_user_id(current_user.id, current_user.institution_id)
    resources = await service.list_activity_resources(student, activity_id)
    return StudentActivityResourceListResponse(items=resources, total=len(resources))


@router.get(
    "/activities/{activity_id}/resources/{resource_id}/download",
    status_code=status.HTTP_200_OK,
    summary="Descargar archivo de recurso pedagógico (Estudiante)",
    description="Descarga de forma segura y autenticada el archivo adjunto de una actividad del estudiante.",
    dependencies=[Depends(require_permission("activities", "read"))],
)
async def download_student_activity_resource(
    activity_id: uuid.UUID,
    resource_id: uuid.UUID,
    current_user: CurrentUserDep,
    db: SessionDep,
    request: Request,
) -> FileResponse:
    service = StudentPortalService(session=db)
    student = await service.get_student_by_user_id(current_user.id, current_user.institution_id)
    resource, file_path = await service.get_resource_for_download(
        student,
        activity_id,
        resource_id,
        actor_id=str(current_user.id),
        actor_ip=request.client.host if request.client else "0.0.0.0",
    )
    filename = resource.original_filename or f"recurso_{resource.id}"
    return FileResponse(
        path=str(file_path),
        filename=filename,
        media_type=resource.mime_type or "application/octet-stream",
        content_disposition_type="attachment",
    )


# ===========================================================================
# 4.1 Student Submissions & Deliveries (Phase B3-H13)
# ===========================================================================

@router.get(
    "/activities/{activity_id}/submission",
    response_model=StudentSubmissionDetailResponse,
    status_code=status.HTTP_200_OK,
    summary="Detalle de entrega de actividad (Estudiante)",
    description="Consulta el estado de entrega, el borrador actual (o crea el primero), y el historial de intentos.",
    dependencies=[Depends(require_permission("submissions", "read"))],
)
async def get_student_submission(
    activity_id: uuid.UUID,
    current_user: CurrentUserDep,
    db: SessionDep,
) -> StudentSubmissionDetailResponse:
    service = StudentPortalService(session=db)
    student = await service.get_student_by_user_id(current_user.id, current_user.institution_id)
    detail = await service.get_submission_detail(student, activity_id)
    await db.commit()
    return detail


@router.post(
    "/activities/{activity_id}/submission/draft",
    response_model=StudentSubmissionAttemptResponse,
    status_code=status.HTTP_200_OK,
    summary="Guardar borrador de entrega (Estudiante)",
    description="Guarda el texto de respuesta en el borrador de entrega en curso sin presentarlo formalmente.",
    dependencies=[Depends(require_permission("submissions", "update"))],
)
async def save_student_submission_draft(
    activity_id: uuid.UUID,
    data: StudentSubmissionDraftUpdateRequest,
    current_user: CurrentUserDep,
    db: SessionDep,
) -> StudentSubmissionAttemptResponse:
    service = StudentPortalService(session=db)
    student = await service.get_student_by_user_id(current_user.id, current_user.institution_id)
    attempt = await service.save_submission_draft(student, activity_id, data)
    await db.commit()
    return attempt


@router.post(
    "/activities/{activity_id}/submission/files",
    response_model=SubmissionAttachmentItemResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Adjuntar archivo a borrador de entrega (Estudiante)",
    description="Carga y adjunta un archivo a la entrega en borrador (máximo 3 archivos, <= 10MB).",
    dependencies=[Depends(require_permission("submissions", "update"))],
)
async def upload_student_submission_file(
    activity_id: uuid.UUID,
    file: Annotated[UploadFile, File(...)],
    current_user: CurrentUserDep,
    db: SessionDep,
) -> SubmissionAttachmentItemResponse:
    service = StudentPortalService(session=db)
    student = await service.get_student_by_user_id(current_user.id, current_user.institution_id)
    content = await file.read()
    attachment = await service.upload_submission_file(
        student,
        activity_id,
        filename=file.filename or "archivo_entrega",
        content=content,
        declared_mime_type=file.content_type,
    )
    await db.commit()
    return attachment


@router.delete(
    "/activities/{activity_id}/submission/files/{attachment_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar archivo adjunto de borrador (Estudiante)",
    dependencies=[Depends(require_permission("submissions", "update"))],
)
async def delete_student_submission_file(
    activity_id: uuid.UUID,
    attachment_id: uuid.UUID,
    current_user: CurrentUserDep,
    db: SessionDep,
) -> Response:
    service = StudentPortalService(session=db)
    student = await service.get_student_by_user_id(current_user.id, current_user.institution_id)
    await service.delete_submission_file(student, activity_id, attachment_id)
    await db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/activities/{activity_id}/submission/submit",
    response_model=StudentSubmissionDetailResponse,
    status_code=status.HTTP_200_OK,
    summary="Presentar entrega de actividad académica (Estudiante)",
    description="Confirma y envía la entrega formal del estudiante. Evalúa tardanza en UTC.",
    dependencies=[Depends(require_permission("submissions", "create"))],
)
async def submit_student_activity(
    activity_id: uuid.UUID,
    current_user: CurrentUserDep,
    db: SessionDep,
    request: Request,
) -> StudentSubmissionDetailResponse:
    service = StudentPortalService(session=db)
    student = await service.get_student_by_user_id(current_user.id, current_user.institution_id)
    detail = await service.submit_activity(
        student,
        activity_id,
        actor_id=str(current_user.id),
        actor_ip=request.client.host if request.client else "0.0.0.0",
    )
    await db.commit()
    return detail


@router.get(
    "/activities/{activity_id}/submission/attachments/{attachment_id}/download",
    status_code=status.HTTP_200_OK,
    summary="Descargar archivo adjunto de entrega propia (Estudiante)",
    description="Descarga autenticada y segura de un archivo adjunto presentado por el estudiante.",
    dependencies=[Depends(require_permission("submissions", "read"))],
)
async def download_student_submission_attachment(
    activity_id: uuid.UUID,
    attachment_id: uuid.UUID,
    current_user: CurrentUserDep,
    db: SessionDep,
    request: Request,
) -> FileResponse:
    service = StudentPortalService(session=db)
    student = await service.get_student_by_user_id(current_user.id, current_user.institution_id)
    attachment, file_path = await service.get_submission_attachment_for_download(
        student,
        activity_id,
        attachment_id,
        actor_id=str(current_user.id),
        actor_ip=request.client.host if request.client else "0.0.0.0",
    )
    return FileResponse(
        path=str(file_path),
        filename=attachment.original_filename or f"entrega_{attachment.id}",
        media_type=attachment.mime_type or "application/octet-stream",
        content_disposition_type="attachment",
    )


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

