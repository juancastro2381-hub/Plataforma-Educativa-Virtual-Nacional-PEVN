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

from fastapi import APIRouter, Depends, Query, Request, Response, status

from app.api.deps import (
    CurrentUserDep,
    SessionDep,
    require_permission,
)
from app.models.academic_activity import ActivityStatus
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
    DailyAttendanceBatchRequest,
    DailyAttendanceListResponse,
    TeacherAssignmentsListResponse,
    TeacherDashboardSummaryResponse,
    TeacherGroupRosterResponse,
    TeacherGroupsListResponse,
)
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
    items = [
        AcademicActivityResponse(
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
            status=a.status,
            publication_date=a.publication_date,
            due_date=a.due_date,
            max_score=a.max_score,
            instructions=a.instructions,
            resource_url=a.resource_url,
            total_submissions=len(a.grades) if a.grades else 0,
            total_graded=sum(1 for g in a.grades if g.score is not None) if a.grades else 0,
            created_at=a.created_at,
            updated_at=a.updated_at,
        )
        for a in records
    ]
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
    return AcademicActivityResponse(
        id=activity.id,
        institution_id=activity.institution_id,
        teacher_id=activity.teacher_id,
        teacher_name=f"{activity.teacher.user.first_name} {activity.teacher.user.last_name}" if activity.teacher and activity.teacher.user else None,
        subject_id=activity.subject_id,
        subject_name=activity.subject.name if activity.subject else None,
        group_id=activity.group_id,
        group_name=activity.group.name if activity.group else None,
        academic_year_id=activity.academic_year_id,
        academic_year_name=activity.academic_year.name if activity.academic_year else None,
        title=activity.title,
        description=activity.description,
        activity_type=activity.activity_type,
        status=activity.status,
        publication_date=activity.publication_date,
        due_date=activity.due_date,
        max_score=activity.max_score,
        instructions=activity.instructions,
        resource_url=activity.resource_url,
        total_submissions=0,
        total_graded=0,
        created_at=activity.created_at,
        updated_at=activity.updated_at,
    )


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
    return AcademicActivityResponse(
        id=activity.id,
        institution_id=activity.institution_id,
        teacher_id=activity.teacher_id,
        teacher_name=f"{activity.teacher.user.first_name} {activity.teacher.user.last_name}" if activity.teacher and activity.teacher.user else None,
        subject_id=activity.subject_id,
        subject_name=activity.subject.name if activity.subject else None,
        group_id=activity.group_id,
        group_name=activity.group.name if activity.group else None,
        academic_year_id=activity.academic_year_id,
        academic_year_name=activity.academic_year.name if activity.academic_year else None,
        title=activity.title,
        description=activity.description,
        activity_type=activity.activity_type,
        status=activity.status,
        publication_date=activity.publication_date,
        due_date=activity.due_date,
        max_score=activity.max_score,
        instructions=activity.instructions,
        resource_url=activity.resource_url,
        total_submissions=len(activity.grades) if activity.grades else 0,
        total_graded=sum(1 for g in activity.grades if g.score is not None) if activity.grades else 0,
        created_at=activity.created_at,
        updated_at=activity.updated_at,
    )


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
    return AcademicActivityResponse(
        id=activity.id,
        institution_id=activity.institution_id,
        teacher_id=activity.teacher_id,
        teacher_name=f"{activity.teacher.user.first_name} {activity.teacher.user.last_name}" if activity.teacher and activity.teacher.user else None,
        subject_id=activity.subject_id,
        subject_name=activity.subject.name if activity.subject else None,
        group_id=activity.group_id,
        group_name=activity.group.name if activity.group else None,
        academic_year_id=activity.academic_year_id,
        academic_year_name=activity.academic_year.name if activity.academic_year else None,
        title=activity.title,
        description=activity.description,
        activity_type=activity.activity_type,
        status=activity.status,
        publication_date=activity.publication_date,
        due_date=activity.due_date,
        max_score=activity.max_score,
        instructions=activity.instructions,
        resource_url=activity.resource_url,
        total_submissions=len(activity.grades) if activity.grades else 0,
        total_graded=sum(1 for g in activity.grades if g.score is not None) if activity.grades else 0,
        created_at=activity.created_at,
        updated_at=activity.updated_at,
    )


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
    return AcademicActivityResponse(
        id=activity.id,
        institution_id=activity.institution_id,
        teacher_id=activity.teacher_id,
        teacher_name=f"{activity.teacher.user.first_name} {activity.teacher.user.last_name}" if activity.teacher and activity.teacher.user else None,
        subject_id=activity.subject_id,
        subject_name=activity.subject.name if activity.subject else None,
        group_id=activity.group_id,
        group_name=activity.group.name if activity.group else None,
        academic_year_id=activity.academic_year_id,
        academic_year_name=activity.academic_year.name if activity.academic_year else None,
        title=activity.title,
        description=activity.description,
        activity_type=activity.activity_type,
        status=activity.status,
        publication_date=activity.publication_date,
        due_date=activity.due_date,
        max_score=activity.max_score,
        instructions=activity.instructions,
        resource_url=activity.resource_url,
        total_submissions=len(activity.grades) if activity.grades else 0,
        total_graded=sum(1 for g in activity.grades if g.score is not None) if activity.grades else 0,
        created_at=activity.created_at,
        updated_at=activity.updated_at,
    )


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
    return AcademicActivityResponse(
        id=activity.id,
        institution_id=activity.institution_id,
        teacher_id=activity.teacher_id,
        teacher_name=f"{activity.teacher.user.first_name} {activity.teacher.user.last_name}" if activity.teacher and activity.teacher.user else None,
        subject_id=activity.subject_id,
        subject_name=activity.subject.name if activity.subject else None,
        group_id=activity.group_id,
        group_name=activity.group.name if activity.group else None,
        academic_year_id=activity.academic_year_id,
        academic_year_name=activity.academic_year.name if activity.academic_year else None,
        title=activity.title,
        description=activity.description,
        activity_type=activity.activity_type,
        status=activity.status,
        publication_date=activity.publication_date,
        due_date=activity.due_date,
        max_score=activity.max_score,
        instructions=activity.instructions,
        resource_url=activity.resource_url,
        total_submissions=len(activity.grades) if activity.grades else 0,
        total_graded=sum(1 for g in activity.grades if g.score is not None) if activity.grades else 0,
        created_at=activity.created_at,
        updated_at=activity.updated_at,
    )


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
    return await service.batch_grade_activity(
        teacher,
        activity_id,
        data,
        actor_id=str(current_user.id),
        actor_ip=request.client.host if request.client else "0.0.0.0",
    )


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
    return await service.record_daily_attendance(
        teacher,
        group_id=group_id,
        data=data,
        actor_id=str(current_user.id),
        actor_ip=request.client.host if request.client else "0.0.0.0",
    )


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
