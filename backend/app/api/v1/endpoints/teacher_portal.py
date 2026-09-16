"""
PEVN Backend — Teacher Portal API Endpoints (Phase 13D.5)

REST Controller providing the dedicated operational workspace for educators:
- GET /teacher/dashboard
- GET /teacher/assignments
- GET /teacher/groups
- GET /teacher/groups/{group_id}/roster
- GET /teacher/activities
- POST /teacher/activities
- GET /teacher/activities/{activity_id}
- PATCH /teacher/activities/{activity_id}
- POST /teacher/activities/{activity_id}/publish
- POST /teacher/activities/{activity_id}/close
- DELETE /teacher/activities/{activity_id}
- GET /teacher/activities/{activity_id}/grades
- PUT /teacher/activities/{activity_id}/grades
- GET /teacher/groups/{group_id}/attendance
- POST /teacher/groups/{group_id}/attendance
- GET /teacher/planning
- POST /teacher/planning
- PATCH /teacher/planning/{plan_id}
- DELETE /teacher/planning/{plan_id}
"""

from __future__ import annotations

import uuid
from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, Query, Request, Response, UploadFile, status
from fastapi.responses import FileResponse

from app.api.deps import (
    ClientIpDep,
    CurrentUserDep,
    SessionDep,
    require_permission,
)
from app.models.academic_activity import (
    AcademicActivity,
    ActivityDeliveryType,
    ActivityStatus,
    SubmissionStatus,
)
from app.schemas.communication import (
    CommunicationListResponse,
    CommunicationReceiptResponse,
    InstitutionalCommunicationResponse,
)
from app.schemas.news import (
    InstitutionalNewsResponse,
    NewsListResponse,
)
from app.schemas.teacher_portal import (
    AcademicActivityCreateRequest,
    AcademicActivityListResponse,
    AcademicActivityResponse,
    AcademicActivityUpdateRequest,
    AcademicPlanCreateRequest,
    AcademicPlanListResponse,
    AcademicPlanResponse,
    AcademicPlanUpdateRequest,
    ActivityGradeBatchUpdateRequest,
    ActivityGradesListResponse,
    ActivityResourceCreateUrlRequest,
    ActivityResourceListResponse,
    ActivityResourceResponse,
    DailyAttendanceBatchRequest,
    DailyAttendanceListResponse,
    TeacherAssignmentsListResponse,
    TeacherDashboardSummaryResponse,
    TeacherGroupRosterResponse,
    TeacherGroupsListResponse,
    TeacherSubmissionDetailResponse,
    TeacherSubmissionReturnRequest,
    TeacherSubmissionsListResponse,
)
from app.services.communication_service import CommunicationService
from app.services.news_service import NewsService
from app.services.teacher_portal_service import TeacherPortalService

router = APIRouter(prefix="/teacher", tags=["Teacher Portal"])


# ===========================================================================
# 1. Teacher Dashboard Summary
# ===========================================================================

@router.get(
    "/dashboard",
    response_model=TeacherDashboardSummaryResponse,
    status_code=status.HTTP_200_OK,
    summary="Dashboard operativo del docente",
    description="Devuelve métricas KPI y resumen de carga académica para el docente autenticado.",
    dependencies=[Depends(require_permission("academic_assignments", "read"))],
)
async def get_teacher_dashboard(
    current_user: CurrentUserDep,
    db: SessionDep,
) -> TeacherDashboardSummaryResponse:
    service = TeacherPortalService(session=db)
    teacher = await service.get_teacher_profile(current_user.id, current_user.institution_id)
    return await service.get_dashboard_summary(teacher)


# ===========================================================================
# 2. My Academic Load (Assignments)
# ===========================================================================

@router.get(
    "/assignments",
    response_model=TeacherAssignmentsListResponse,
    status_code=status.HTTP_200_OK,
    summary="Consultar carga académica del docente",
    description="Devuelve únicamente las asignaciones académicas activas del docente autenticado.",
    dependencies=[Depends(require_permission("academic_assignments", "read"))],
)
async def list_teacher_assignments(
    current_user: CurrentUserDep,
    db: SessionDep,
    is_active: bool = True,
) -> TeacherAssignmentsListResponse:
    service = TeacherPortalService(session=db)
    teacher = await service.get_teacher_profile(current_user.id, current_user.institution_id)
    return await service.list_teacher_assignments(teacher, is_active=is_active)


# ===========================================================================
# 3. My Groups & Student Rosters
# ===========================================================================

@router.get(
    "/groups",
    response_model=TeacherGroupsListResponse,
    status_code=status.HTTP_200_OK,
    summary="Listar grupos asignados al docente",
    description="Devuelve los grupos/salones donde el docente tiene carga académica activa.",
    dependencies=[Depends(require_permission("groups", "read"))],
)
async def list_teacher_groups(
    current_user: CurrentUserDep,
    db: SessionDep,
) -> TeacherGroupsListResponse:
    service = TeacherPortalService(session=db)
    teacher = await service.get_teacher_profile(current_user.id, current_user.institution_id)
    return await service.list_teacher_groups(teacher)


@router.get(
    "/groups/{group_id}/roster",
    response_model=TeacherGroupRosterResponse,
    status_code=status.HTTP_200_OK,
    summary="Consultar lista de estudiantes de un grupo asignado",
    description="Devuelve la planilla de estudiantes matriculados en el grupo. Requiere asignación activa del docente.",
    dependencies=[
        Depends(require_permission("groups", "read")),
        Depends(require_permission("students", "read")),
    ],
)
async def get_group_roster(
    group_id: uuid.UUID,
    current_user: CurrentUserDep,
    db: SessionDep,
) -> TeacherGroupRosterResponse:
    service = TeacherPortalService(session=db)
    teacher = await service.get_teacher_profile(current_user.id, current_user.institution_id)
    return await service.get_group_roster(teacher, group_id)


# ===========================================================================
# 4. Academic Activities
# ===========================================================================

def format_activity_response(a: AcademicActivity) -> AcademicActivityResponse:
    """Helper to consistently format AcademicActivity with computed metrics and nested resources."""
    submitted_students = set()
    if getattr(a, "submissions", None):
        for s in a.submissions:
            if s.status in (
                SubmissionStatus.SUBMITTED,
                SubmissionStatus.LATE,
                SubmissionStatus.RETURNED,
                SubmissionStatus.GRADED,
            ):
                submitted_students.add(s.student_id)

    resources_list = []
    if getattr(a, "resources", None):
        for r in a.resources:
            resources_list.append(
                ActivityResourceResponse(
                    id=r.id,
                    activity_id=r.activity_id,
                    institution_id=r.institution_id,
                    resource_type=r.resource_type,
                    title=r.title,
                    url=r.url,
                    original_filename=r.original_filename,
                    file_size_bytes=r.file_size_bytes,
                    mime_type=r.mime_type,
                    created_at=r.created_at,
                    updated_at=r.updated_at,
                )
            )

    total_graded = sum(1 for g in a.grades if g.score is not None) if getattr(a, "grades", None) else 0

    return AcademicActivityResponse(
        id=a.id,
        institution_id=a.institution_id,
        teacher_id=a.teacher_id,
        teacher_name=f"{a.teacher.user.first_name} {a.teacher.user.last_name}" if a.teacher and a.teacher.user else None,
        subject_id=a.subject_id,
        subject_name=a.subject.name if a.subject else None,
        group_id=a.group_id,
        group_name=a.group.name if a.group else None,
        academic_year_id=a.academic_year_id,
        academic_year_name=a.academic_year.name if a.academic_year else None,
        title=a.title,
        description=a.description,
        activity_type=a.activity_type,
        delivery_type=a.delivery_type or ActivityDeliveryType.FILE,
        status=a.status,
        publication_date=a.publication_date,
        due_date=a.due_date,
        max_score=a.max_score,
        instructions=a.instructions,
        resource_url=a.resource_url,
        total_submissions=len(submitted_students),
        total_graded=total_graded,
        resources=resources_list,
        created_at=a.created_at,
        updated_at=a.updated_at,
    )


@router.get(
    "/activities",
    response_model=AcademicActivityListResponse,
    status_code=status.HTTP_200_OK,
    summary="Listar actividades académicas del docente",
    dependencies=[Depends(require_permission("activities", "read"))],
)
async def list_teacher_activities(
    current_user: CurrentUserDep,
    db: SessionDep,
    group_id: uuid.UUID | None = None,
    subject_id: uuid.UUID | None = None,
    activity_status: ActivityStatus | None = Query(default=None, alias="status"),
) -> AcademicActivityListResponse:
    service = TeacherPortalService(session=db)
    teacher = await service.get_teacher_profile(current_user.id, current_user.institution_id)
    records = await service.list_activities(
        teacher,
        group_id=group_id,
        subject_id=subject_id,
        status=activity_status,
    )
    items = [format_activity_response(a) for a in records]
    return AcademicActivityListResponse(items=items, total=len(items))


@router.post(
    "/activities",
    response_model=AcademicActivityResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear nueva actividad académica",
    description="Crea una actividad asociada a una asignación académica activa del docente.",
    dependencies=[Depends(require_permission("activities", "create"))],
)
async def create_teacher_activity(
    data: AcademicActivityCreateRequest,
    current_user: CurrentUserDep,
    db: SessionDep,
    request: Request,
) -> AcademicActivityResponse:
    service = TeacherPortalService(session=db)
    teacher = await service.get_teacher_profile(current_user.id, current_user.institution_id)
    activity = await service.create_activity(
        teacher,
        data,
        actor_id=str(current_user.id),
        actor_ip=request.client.host if request.client else "0.0.0.0",
    )
    await db.commit()
    return format_activity_response(activity)


@router.get(
    "/activities/{activity_id}",
    response_model=AcademicActivityResponse,
    status_code=status.HTTP_200_OK,
    summary="Detalle de actividad académica",
    dependencies=[Depends(require_permission("activities", "read"))],
)
async def get_teacher_activity(
    activity_id: uuid.UUID,
    current_user: CurrentUserDep,
    db: SessionDep,
) -> AcademicActivityResponse:
    service = TeacherPortalService(session=db)
    teacher = await service.get_teacher_profile(current_user.id, current_user.institution_id)
    activity = await service.get_activity(teacher, activity_id)
    return format_activity_response(activity)


@router.patch(
    "/activities/{activity_id}",
    response_model=AcademicActivityResponse,
    status_code=status.HTTP_200_OK,
    summary="Modificar actividad académica",
    dependencies=[Depends(require_permission("activities", "update"))],
)
async def update_teacher_activity(
    activity_id: uuid.UUID,
    data: AcademicActivityUpdateRequest,
    current_user: CurrentUserDep,
    db: SessionDep,
    request: Request,
) -> AcademicActivityResponse:
    service = TeacherPortalService(session=db)
    teacher = await service.get_teacher_profile(current_user.id, current_user.institution_id)
    activity = await service.update_activity(
        teacher,
        activity_id,
        data,
        actor_id=str(current_user.id),
        actor_ip=request.client.host if request.client else "0.0.0.0",
    )
    await db.commit()
    return format_activity_response(activity)


@router.post(
    "/activities/{activity_id}/publish",
    response_model=AcademicActivityResponse,
    status_code=status.HTTP_200_OK,
    summary="Publicar actividad académica",
    description="Pasa la actividad a estado PUBLISHED y habilita las casillas de evaluación de los estudiantes.",
    dependencies=[Depends(require_permission("activities", "publish"))],
)
async def publish_teacher_activity(
    activity_id: uuid.UUID,
    current_user: CurrentUserDep,
    db: SessionDep,
    request: Request,
) -> AcademicActivityResponse:
    service = TeacherPortalService(session=db)
    teacher = await service.get_teacher_profile(current_user.id, current_user.institution_id)
    activity = await service.publish_activity(
        teacher,
        activity_id,
        actor_id=str(current_user.id),
        actor_ip=request.client.host if request.client else "0.0.0.0",
    )
    await db.commit()
    return format_activity_response(activity)


@router.post(
    "/activities/{activity_id}/close",
    response_model=AcademicActivityResponse,
    status_code=status.HTTP_200_OK,
    summary="Cerrar actividad académica",
    dependencies=[Depends(require_permission("activities", "close"))],
)
async def close_teacher_activity(
    activity_id: uuid.UUID,
    current_user: CurrentUserDep,
    db: SessionDep,
    request: Request,
) -> AcademicActivityResponse:
    service = TeacherPortalService(session=db)
    teacher = await service.get_teacher_profile(current_user.id, current_user.institution_id)
    activity = await service.close_activity(
        teacher,
        activity_id,
        actor_id=str(current_user.id),
        actor_ip=request.client.host if request.client else "0.0.0.0",
    )
    await db.commit()
    return format_activity_response(activity)


@router.delete(
    "/activities/{activity_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar actividad académica",
    dependencies=[Depends(require_permission("activities", "delete"))],
)
async def delete_teacher_activity(
    activity_id: uuid.UUID,
    current_user: CurrentUserDep,
    db: SessionDep,
    request: Request,
) -> None:
    service = TeacherPortalService(session=db)
    teacher = await service.get_teacher_profile(current_user.id, current_user.institution_id)
    await service.delete_activity(
        teacher,
        activity_id,
        actor_id=str(current_user.id),
        actor_ip=request.client.host if request.client else "0.0.0.0",
    )


# ===========================================================================
# 4.1. Pedagogical Activity Resources (B3-H11)
# ===========================================================================

@router.get(
    "/activities/{activity_id}/resources",
    response_model=ActivityResourceListResponse,
    status_code=status.HTTP_200_OK,
    summary="Listar materiales / recursos de una actividad pedagógica",
    dependencies=[Depends(require_permission("activities", "read"))],
)
async def list_teacher_activity_resources(
    activity_id: uuid.UUID,
    current_user: CurrentUserDep,
    db: SessionDep,
) -> ActivityResourceListResponse:
    service = TeacherPortalService(session=db)
    teacher = await service.get_teacher_profile(current_user.id, current_user.institution_id)
    resources = await service.list_activity_resources(teacher, activity_id)
    return ActivityResourceListResponse(items=resources, total=len(resources))


@router.post(
    "/activities/{activity_id}/resources",
    response_model=ActivityResourceResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Adjuntar material pedagógico (Multipart Form: Archivo o URL)",
    dependencies=[Depends(require_permission("activities", "update"))],
)
async def create_teacher_activity_resource(
    activity_id: uuid.UUID,
    title: Annotated[str, Form()],
    current_user: CurrentUserDep,
    db: SessionDep,
    request: Request,
    resource_type: Annotated[str, Form()] = "URL",
    url: Annotated[str | None, Form()] = None,
    description: Annotated[str | None, Form()] = None,
    file: Annotated[UploadFile | None, File()] = None,
) -> ActivityResourceResponse:
    service = TeacherPortalService(session=db)
    teacher = await service.get_teacher_profile(current_user.id, current_user.institution_id)
    actor_id = str(current_user.id)
    actor_ip = request.client.host if request.client else "0.0.0.0"

    norm_type = resource_type.strip().upper()
    if norm_type == "FILE" or file is not None:
        if not file:
            from fastapi import HTTPException
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Se requiere adjuntar un archivo para recursos de tipo FILE",
            )
        file_bytes = await file.read()
        resource = await service.create_file_resource(
            teacher=teacher,
            activity_id=activity_id,
            title=title,
            original_filename=file.filename or "archivo",
            content=file_bytes,
            declared_mime_type=file.content_type,
            actor_id=actor_id,
            actor_ip=actor_ip,
        )
    else:
        if not url:
            from fastapi import HTTPException
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Se requiere la URL del recurso",
            )
        resource = await service.create_url_resource(
            teacher=teacher,
            activity_id=activity_id,
            title=title,
            url=url,
            actor_id=actor_id,
            actor_ip=actor_ip,
        )

    await db.commit()
    return resource


@router.post(
    "/activities/{activity_id}/resources/url",
    response_model=ActivityResourceResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Adjuntar recurso pedagógico de tipo URL (JSON)",
    dependencies=[Depends(require_permission("activities", "update"))],
)
async def create_teacher_activity_url_resource(
    activity_id: uuid.UUID,
    data: ActivityResourceCreateUrlRequest,
    current_user: CurrentUserDep,
    db: SessionDep,
    request: Request,
) -> ActivityResourceResponse:
    service = TeacherPortalService(session=db)
    teacher = await service.get_teacher_profile(current_user.id, current_user.institution_id)
    resource = await service.create_url_resource(
        teacher=teacher,
        activity_id=activity_id,
        title=data.title,
        url=str(data.url),
        actor_id=str(current_user.id),
        actor_ip=request.client.host if request.client else "0.0.0.0",
    )
    await db.commit()
    return resource


@router.delete(
    "/activities/{activity_id}/resources/{resource_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar recurso pedagógico de una actividad",
    dependencies=[Depends(require_permission("activities", "update"))],
)
async def delete_teacher_activity_resource(
    activity_id: uuid.UUID,
    resource_id: uuid.UUID,
    current_user: CurrentUserDep,
    db: SessionDep,
    request: Request,
) -> None:
    service = TeacherPortalService(session=db)
    teacher = await service.get_teacher_profile(current_user.id, current_user.institution_id)
    await service.delete_resource(
        teacher,
        activity_id,
        resource_id,
        actor_id=str(current_user.id),
        actor_ip=request.client.host if request.client else "0.0.0.0",
    )
    await db.commit()


@router.get(
    "/activities/{activity_id}/resources/{resource_id}/download",
    status_code=status.HTTP_200_OK,
    summary="Descargar archivo de recurso pedagógico (Docente)",
    dependencies=[Depends(require_permission("activities", "read"))],
)
async def download_teacher_activity_resource(
    activity_id: uuid.UUID,
    resource_id: uuid.UUID,
    current_user: CurrentUserDep,
    db: SessionDep,
    request: Request,
) -> FileResponse:
    service = TeacherPortalService(session=db)
    teacher = await service.get_teacher_profile(current_user.id, current_user.institution_id)
    resource, file_path = await service.get_resource_for_download(
        teacher,
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
# 4.2. Student Submissions Review & Returns (Phase B3-H13)
# ===========================================================================

@router.get(
    "/activities/{activity_id}/submissions",
    response_model=TeacherSubmissionsListResponse,
    status_code=status.HTTP_200_OK,
    summary="Listar entregas de estudiantes de una actividad (Docente)",
    description="Consulta la lista de estudiantes del grupo con su estado de entrega actual, fecha y adjuntos.",
    dependencies=[Depends(require_permission("submissions", "read"))],
)
async def list_teacher_activity_submissions(
    activity_id: uuid.UUID,
    current_user: CurrentUserDep,
    db: SessionDep,
) -> TeacherSubmissionsListResponse:
    service = TeacherPortalService(session=db)
    teacher = await service.get_teacher_profile(current_user.id, current_user.institution_id)
    return await service.list_activity_submissions(teacher, activity_id)


@router.get(
    "/activities/{activity_id}/submissions/{student_id}",
    response_model=TeacherSubmissionDetailResponse,
    status_code=status.HTTP_200_OK,
    summary="Detalle de entrega e historial de intentos de un estudiante (Docente)",
    description="Consulta todos los intentos históricos, respuestas, adjuntos y nota oficial de un estudiante.",
    dependencies=[Depends(require_permission("submissions", "read"))],
)
async def get_teacher_student_submission(
    activity_id: uuid.UUID,
    student_id: uuid.UUID,
    current_user: CurrentUserDep,
    db: SessionDep,
) -> TeacherSubmissionDetailResponse:
    service = TeacherPortalService(session=db)
    teacher = await service.get_teacher_profile(current_user.id, current_user.institution_id)
    return await service.get_student_submission_detail(teacher, activity_id, student_id)


@router.post(
    "/activities/{activity_id}/submissions/{student_id}/return",
    response_model=TeacherSubmissionDetailResponse,
    status_code=status.HTTP_200_OK,
    summary="Devolver entrega de estudiante para corrección pedagógica (Docente)",
    description="Pasa la última entrega a estado RETURNED, registra retroalimentación y restablece la nota a PENDING.",
    dependencies=[Depends(require_permission("submissions", "return"))],
)
async def return_teacher_student_submission(
    activity_id: uuid.UUID,
    student_id: uuid.UUID,
    data: TeacherSubmissionReturnRequest,
    current_user: CurrentUserDep,
    db: SessionDep,
    request: Request,
) -> TeacherSubmissionDetailResponse:
    service = TeacherPortalService(session=db)
    teacher = await service.get_teacher_profile(current_user.id, current_user.institution_id)
    result = await service.return_student_submission(
        teacher,
        activity_id,
        student_id,
        data.return_feedback,
        actor_id=str(current_user.id),
        actor_ip=request.client.host if request.client else "0.0.0.0",
    )
    await db.commit()
    return result


@router.get(
    "/activities/{activity_id}/submissions/{student_id}/attachments/{attachment_id}/download",
    status_code=status.HTTP_200_OK,
    summary="Descargar archivo adjunto de entrega de estudiante (Docente)",
    description="Descarga de forma segura y autorizada el archivo de entrega de un estudiante.",
    dependencies=[Depends(require_permission("submissions", "read"))],
)
async def download_teacher_submission_attachment(
    activity_id: uuid.UUID,
    student_id: uuid.UUID,
    attachment_id: uuid.UUID,
    current_user: CurrentUserDep,
    db: SessionDep,
    request: Request,
) -> FileResponse:
    service = TeacherPortalService(session=db)
    teacher = await service.get_teacher_profile(current_user.id, current_user.institution_id)
    attachment, file_path = await service.get_student_attachment_for_download(
        teacher,
        activity_id,
        student_id,
        attachment_id,
        actor_id=str(current_user.id),
        actor_ip=request.client.host if request.client else "0.0.0.0",
    )
    return FileResponse(
        path=str(file_path),
        filename=attachment.original_filename,
        media_type=attachment.mime_type or "application/octet-stream",
        content_disposition_type="attachment",
    )


# ===========================================================================
# 5. Activity Grades & Evaluations
# ===========================================================================

@router.get(
    "/activities/{activity_id}/grades",
    response_model=ActivityGradesListResponse,
    status_code=status.HTTP_200_OK,
    summary="Planilla de calificaciones de una actividad",
    dependencies=[Depends(require_permission("grades", "read"))],
)
async def get_activity_grades(
    activity_id: uuid.UUID,
    current_user: CurrentUserDep,
    db: SessionDep,
) -> ActivityGradesListResponse:
    service = TeacherPortalService(session=db)
    teacher = await service.get_teacher_profile(current_user.id, current_user.institution_id)
    return await service.list_activity_grades(teacher, activity_id)


@router.put(
    "/activities/{activity_id}/grades",
    response_model=ActivityGradesListResponse,
    status_code=status.HTTP_200_OK,
    summary="Ingresar / actualizar calificaciones por lote",
    dependencies=[Depends(require_permission("grades", "write"))],
)
async def batch_update_activity_grades(
    activity_id: uuid.UUID,
    data: ActivityGradeBatchUpdateRequest,
    current_user: CurrentUserDep,
    db: SessionDep,
    request: Request,
) -> ActivityGradesListResponse:
    service = TeacherPortalService(session=db)
    teacher = await service.get_teacher_profile(current_user.id, current_user.institution_id)
    res = await service.batch_grade_activity(
        teacher,
        activity_id,
        data,
        actor_id=str(current_user.id),
        actor_ip=request.client.host if request.client else "0.0.0.0",
    )
    await db.commit()
    return res


# ===========================================================================
# 6. Daily Classroom Attendance
# ===========================================================================

@router.get(
    "/groups/{group_id}/attendance",
    response_model=DailyAttendanceListResponse,
    status_code=status.HTTP_200_OK,
    summary="Consultar planilla de asistencia de un grupo y fecha",
    dependencies=[Depends(require_permission("attendance", "read"))],
)
async def get_daily_attendance(
    group_id: uuid.UUID,
    attendance_date: date,
    current_user: CurrentUserDep,
    db: SessionDep,
    subject_id: uuid.UUID | None = None,
) -> DailyAttendanceListResponse:
    service = TeacherPortalService(session=db)
    teacher = await service.get_teacher_profile(current_user.id, current_user.institution_id)
    return await service.list_daily_attendance(
        teacher,
        group_id=group_id,
        attendance_date=attendance_date,
        subject_id=subject_id,
    )


@router.post(
    "/groups/{group_id}/attendance",
    response_model=DailyAttendanceListResponse,
    status_code=status.HTTP_200_OK,
    summary="Registrar asistencia diaria de estudiantes",
    dependencies=[Depends(require_permission("attendance", "write"))],
)
async def record_daily_attendance(
    group_id: uuid.UUID,
    data: DailyAttendanceBatchRequest,
    current_user: CurrentUserDep,
    db: SessionDep,
    request: Request,
) -> DailyAttendanceListResponse:
    service = TeacherPortalService(session=db)
    teacher = await service.get_teacher_profile(current_user.id, current_user.institution_id)
    res = await service.record_daily_attendance(
        teacher,
        group_id=group_id,
        data=data,
        actor_id=str(current_user.id),
        actor_ip=request.client.host if request.client else "0.0.0.0",
    )
    await db.commit()
    return res


# ===========================================================================
# 7. Curricular Planning
# ===========================================================================

@router.get(
    "/planning",
    response_model=AcademicPlanListResponse,
    status_code=status.HTTP_200_OK,
    summary="Listar planeaciones curriculares del docente",
    dependencies=[Depends(require_permission("planning", "read"))],
)
async def list_teacher_plans(
    current_user: CurrentUserDep,
    db: SessionDep,
    group_id: uuid.UUID | None = None,
    subject_id: uuid.UUID | None = None,
) -> AcademicPlanListResponse:
    service = TeacherPortalService(session=db)
    teacher = await service.get_teacher_profile(current_user.id, current_user.institution_id)
    plans = await service.list_academic_plans(teacher, group_id=group_id, subject_id=subject_id)
    items = [
        AcademicPlanResponse(
            id=p.id,
            institution_id=p.institution_id,
            teacher_id=p.teacher_id,
            teacher_name=f"{p.teacher.user.first_name} {p.teacher.user.last_name}" if p.teacher and p.teacher.user else None,
            subject_id=p.subject_id,
            subject_name=p.subject.name if p.subject else None,
            group_id=p.group_id,
            group_name=p.group.name if p.group else None,
            academic_year_id=p.academic_year_id,
            academic_year_name=p.academic_year.name if p.academic_year else None,
            unit_name=p.unit_name,
            competencies=p.competencies,
            learning_objectives=p.learning_objectives,
            methodology=p.methodology,
            evaluation_criteria=p.evaluation_criteria,
            resources=p.resources,
            status=p.status,
            start_date=p.start_date,
            end_date=p.end_date,
            created_at=p.created_at,
            updated_at=p.updated_at,
        )
        for p in plans
    ]
    return AcademicPlanListResponse(items=items, total=len(items))


@router.post(
    "/planning",
    response_model=AcademicPlanResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear planeación curricular",
    dependencies=[Depends(require_permission("planning", "create"))],
)
async def create_teacher_plan(
    data: AcademicPlanCreateRequest,
    current_user: CurrentUserDep,
    db: SessionDep,
    request: Request,
) -> AcademicPlanResponse:
    service = TeacherPortalService(session=db)
    teacher = await service.get_teacher_profile(current_user.id, current_user.institution_id)
    plan = await service.create_academic_plan(
        teacher,
        data,
        actor_id=str(current_user.id),
        actor_ip=request.client.host if request.client else "0.0.0.0",
    )
    await db.commit()
    return AcademicPlanResponse(
        id=plan.id,
        institution_id=plan.institution_id,
        teacher_id=plan.teacher_id,
        teacher_name=f"{plan.teacher.user.first_name} {plan.teacher.user.last_name}" if plan.teacher and plan.teacher.user else None,
        subject_id=plan.subject_id,
        subject_name=plan.subject.name if plan.subject else None,
        group_id=plan.group_id,
        group_name=plan.group.name if plan.group else None,
        academic_year_id=plan.academic_year_id,
        academic_year_name=plan.academic_year.name if plan.academic_year else None,
        unit_name=plan.unit_name,
        competencies=plan.competencies,
        learning_objectives=plan.learning_objectives,
        methodology=plan.methodology,
        evaluation_criteria=plan.evaluation_criteria,
        resources=plan.resources,
        status=plan.status,
        start_date=plan.start_date,
        end_date=plan.end_date,
        created_at=plan.created_at,
        updated_at=plan.updated_at,
    )


@router.patch(
    "/planning/{plan_id}",
    response_model=AcademicPlanResponse,
    status_code=status.HTTP_200_OK,
    summary="Actualizar planeación curricular",
    dependencies=[Depends(require_permission("planning", "update"))],
)
async def update_teacher_plan(
    plan_id: uuid.UUID,
    data: AcademicPlanUpdateRequest,
    current_user: CurrentUserDep,
    db: SessionDep,
    request: Request,
) -> AcademicPlanResponse:
    service = TeacherPortalService(session=db)
    teacher = await service.get_teacher_profile(current_user.id, current_user.institution_id)
    plan = await service.update_academic_plan(
        teacher,
        plan_id,
        data,
        actor_id=str(current_user.id),
        actor_ip=request.client.host if request.client else "0.0.0.0",
    )
    await db.commit()
    return AcademicPlanResponse(
        id=plan.id,
        institution_id=plan.institution_id,
        teacher_id=plan.teacher_id,
        teacher_name=f"{plan.teacher.user.first_name} {plan.teacher.user.last_name}" if plan.teacher and plan.teacher.user else None,
        subject_id=plan.subject_id,
        subject_name=plan.subject.name if plan.subject else None,
        group_id=plan.group_id,
        group_name=plan.group.name if plan.group else None,
        academic_year_id=plan.academic_year_id,
        academic_year_name=plan.academic_year.name if plan.academic_year else None,
        unit_name=plan.unit_name,
        competencies=plan.competencies,
        learning_objectives=plan.learning_objectives,
        methodology=plan.methodology,
        evaluation_criteria=plan.evaluation_criteria,
        resources=plan.resources,
        status=plan.status,
        start_date=plan.start_date,
        end_date=plan.end_date,
        created_at=plan.created_at,
        updated_at=plan.updated_at,
    )


@router.delete(
    "/planning/{plan_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar planeación curricular",
    dependencies=[Depends(require_permission("planning", "delete"))],
)
async def delete_teacher_plan(
    plan_id: uuid.UUID,
    current_user: CurrentUserDep,
    db: SessionDep,
    request: Request,
) -> None:
    service = TeacherPortalService(session=db)
    teacher = await service.get_teacher_profile(current_user.id, current_user.institution_id)
    await service.delete_academic_plan(
        teacher,
        plan_id,
        actor_id=str(current_user.id),
        actor_ip=request.client.host if request.client else "0.0.0.0",
    )
    await db.commit()


# ===========================================================================
# 8. Institutional Communications & News (Phase 15 / B2)
# ===========================================================================

@router.get(
    "/communications",
    response_model=CommunicationListResponse,
    status_code=status.HTTP_200_OK,
    summary="Listar comunicados dirigidos al docente",
    dependencies=[Depends(require_permission("communications", "read"))],
)
async def list_teacher_communications(
    current_user: CurrentUserDep,
    db: SessionDep,
) -> CommunicationListResponse:
    portal_service = TeacherPortalService(session=db)
    teacher = await portal_service.get_teacher_profile(current_user.id, current_user.institution_id)

    comm_service = CommunicationService(session=db)
    tuples = await comm_service.list_teacher_communications(
        teacher=teacher,
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
    summary="Consultar comunicado oficial para el docente y registrar lectura",
    dependencies=[Depends(require_permission("communications", "read"))],
)
async def get_teacher_communication(
    communication_id: uuid.UUID,
    current_user: CurrentUserDep,
    db: SessionDep,
) -> InstitutionalCommunicationResponse:
    portal_service = TeacherPortalService(session=db)
    teacher = await portal_service.get_teacher_profile(current_user.id, current_user.institution_id)

    comm_service = CommunicationService(session=db)
    comm = await comm_service.get_communication_by_id(
        communication_id=communication_id,
        institution_id=teacher.institution_id,
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
    summary="Confirmar acuse de recibo de comunicado por el docente",
    dependencies=[Depends(require_permission("communications", "read"))],
)
async def acknowledge_teacher_communication(
    communication_id: uuid.UUID,
    current_user: CurrentUserDep,
    db: SessionDep,
    client_ip: ClientIpDep,
) -> CommunicationReceiptResponse:
    portal_service = TeacherPortalService(session=db)
    teacher = await portal_service.get_teacher_profile(current_user.id, current_user.institution_id)

    comm_service = CommunicationService(session=db)
    receipt = await comm_service.acknowledge_communication(
        communication_id=communication_id,
        institution_id=teacher.institution_id,
        user=current_user,
        client_ip=client_ip,
    )
    await db.commit()
    return CommunicationReceiptResponse.model_validate(receipt)


@router.get(
    "/news",
    response_model=NewsListResponse,
    status_code=status.HTTP_200_OK,
    summary="Listar noticias institucionales para el docente",
    dependencies=[Depends(require_permission("news", "read"))],
)
async def list_teacher_news(
    current_user: CurrentUserDep,
    db: SessionDep,
) -> NewsListResponse:
    portal_service = TeacherPortalService(session=db)
    teacher = await portal_service.get_teacher_profile(current_user.id, current_user.institution_id)

    news_service = NewsService(session=db)
    items = await news_service.list_news(
        institution_id=teacher.institution_id,
    )
    return NewsListResponse(
        items=[InstitutionalNewsResponse.model_validate(n) for n in items],
        total=len(items),
    )

