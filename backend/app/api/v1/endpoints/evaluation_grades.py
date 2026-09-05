"""
PEVN Backend - Evaluation Grades, Recoveries & Report Cards API Endpoints (Phase 16C)

REST controller for:
  - GET  /evaluations/period-sheet               -> evaluations:read
  - POST /evaluations/period-grades              -> evaluations:grade
  - POST /evaluations/grades/{grade_id}/recoveries -> evaluations:recovery
  - POST /evaluations/periods/{period_id}/close  -> evaluations:close_period
  - POST /evaluations/periods/{period_id}/unlock -> evaluations:reopen_period
  - GET  /evaluations/report-cards/student/{student_id} -> report_cards:read
  - GET  /evaluations/report-cards/student/{student_id}/year-end -> report_cards:read
  - GET  /evaluations/report-cards/group/{group_id}/matrix -> report_cards:read_group

Multi-tenant: institution_id is always resolved from the authenticated context.
Teacher scope and IDOR guards are strictly enforced.
"""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import select

from app.api.deps import (
    AuditServiceDep,
    AuthContextDep,
    CurrentUserDep,
    SessionDep,
    require_permission,
)
from app.core.exceptions import ReportCardAccessDeniedError
from app.core.security.interfaces import SystemRole
from app.exceptions.errors import AuthorizationError
from app.models.guardian import Guardian, StudentGuardian
from app.models.student import Student
from app.models.teacher import Teacher
from app.schemas.evaluation import (
    ClosePeriodResponse,
    GroupConsolidationMatrixResponse,
    PeriodSheetResponse,
    RecordRecoveryGradeRequest,
    RecoveryGradeResponse,
    SavePeriodGradesRequest,
    SavePeriodGradesResponse,
    StudentReportCardResponse,
    UnlockPeriodRequest,
    UnlockPeriodResponse,
    YearEndReportCardResponse,
)
from app.services.evaluation_service import EvaluationService
from app.services.report_card_service import ReportCardService

router = APIRouter(prefix="/evaluations", tags=["Evaluations & Grades"])

DIRECTIVE_ROLES = {
    SystemRole.SUPERADMIN,
    SystemRole.NATIONAL_ADMIN,
    SystemRole.RECTOR,
    SystemRole.INSTITUTION_ADMIN,
    SystemRole.ACADEMIC_COORDINATOR,
    "coordinator",
}


def _resolve_institution_id(
    auth: AuthContextDep,
    current_user: CurrentUserDep,
    institution_id_override: uuid.UUID | None = None,
) -> uuid.UUID:
    """Resolve institution_id from authenticated context."""
    if (
        SystemRole.SUPERADMIN in auth.roles
        or SystemRole.NATIONAL_ADMIN in auth.roles
        or auth.scope.is_national()
    ) and institution_id_override:
        return institution_id_override
    if current_user.institution_id:
        return current_user.institution_id
    raise AuthorizationError("Contexto institucional no disponible.")


async def _resolve_teacher_scope(
    db: SessionDep,
    auth: AuthContextDep,
    current_user: CurrentUserDep,
    institution_id: uuid.UUID,
) -> tuple[uuid.UUID | None, bool]:
    """
    Returns (teacher_id, is_directive).
    If user has directive role, is_directive=True and teacher_id=None.
    Otherwise resolves Teacher profile for current_user.
    """
    # Check if user has any directive role
    user_roles_set = set(auth.roles)
    is_directive = bool(user_roles_set.intersection(DIRECTIVE_ROLES))

    if is_directive:
        return None, True

    # Teacher role: find teacher entity
    stmt = select(Teacher).where(
        Teacher.user_id == current_user.id,
        Teacher.institution_id == institution_id,
    )
    teacher = (await db.execute(stmt)).scalars().first()
    if not teacher:
        raise AuthorizationError(
            "Perfil docente no encontrado para este usuario en la institucion."
        )
    return teacher.id, False


async def _verify_student_report_card_access(
    db: SessionDep,
    auth: AuthContextDep,
    current_user: CurrentUserDep,
    institution_id: uuid.UUID,
    student_id: uuid.UUID,
) -> None:
    """
    IDOR Security Guard:
    - Students may ONLY view their own report card.
    - Guardians may ONLY view report cards of linked children.
    - Teachers and Directives within the tenant may view student report cards.
    """
    user_roles_set = set(auth.roles)

    # SuperAdmin / NationalAdmin
    if (
        SystemRole.SUPERADMIN in user_roles_set
        or SystemRole.NATIONAL_ADMIN in user_roles_set
        or auth.scope.is_national()
    ):
        return

    # Directives and Teachers have institutional access
    if user_roles_set.intersection(DIRECTIVE_ROLES) or SystemRole.TEACHER in user_roles_set:
        return

    # Student check: must match current user
    if SystemRole.STUDENT in user_roles_set:
        st_stmt = select(Student).where(
            Student.user_id == current_user.id,
            Student.institution_id == institution_id,
        )
        student = (await db.execute(st_stmt)).scalars().first()
        if not student or student.id != student_id:
            raise ReportCardAccessDeniedError(
                "Acceso denegado: el estudiante solo puede consultar su propio boletin."
            )
        return

    # Guardian check: must be linked in student_guardians
    if "guardian" in user_roles_set or SystemRole.GUARDIAN in user_roles_set if hasattr(SystemRole, "GUARDIAN") else "guardian" in user_roles_set:
        g_stmt = select(Guardian).where(
            Guardian.user_id == current_user.id,
            Guardian.institution_id == institution_id,
        )
        guardian = (await db.execute(g_stmt)).scalars().first()
        if not guardian:
            raise ReportCardAccessDeniedError("Perfil de acudiente no encontrado.")

        link_stmt = select(StudentGuardian).where(
            StudentGuardian.guardian_id == guardian.id,
            StudentGuardian.student_id == student_id,
        )
        link = (await db.execute(link_stmt)).scalars().first()
        if not link:
            raise ReportCardAccessDeniedError(
                "Acceso denegado: el estudiante no esta vinculado a este acudiente."
            )
        return

    raise ReportCardAccessDeniedError("No tiene permisos para acceder a este boletin.")


# ===========================================================================
# 1. Period Consolidation Sheet (Sabana de Calificaciones)
# ===========================================================================


@router.get(
    "/period-sheet",
    response_model=PeriodSheetResponse,
    status_code=status.HTTP_200_OK,
    summary="Consultar sabana de calificaciones del periodo",
    description=(
        "Obtiene la sabana de consolidacion de calificaciones para un grupo, asignatura y periodo. "
        "Valida alcance docente o directivo."
    ),
    dependencies=[Depends(require_permission("evaluations", "read"))],
)
async def get_period_sheet(
    period_id: Annotated[uuid.UUID, Query(description="ID del periodo academico")],
    group_id: Annotated[uuid.UUID, Query(description="ID del grupo")],
    subject_id: Annotated[uuid.UUID, Query(description="ID de la asignatura")],
    db: SessionDep,
    auth: AuthContextDep,
    current_user: CurrentUserDep,
    institution_id: Annotated[
        uuid.UUID | None,
        Query(description="Override institucional (solo SuperAdmin / NationalAdmin)"),
    ] = None,
) -> PeriodSheetResponse:
    target_institution_id = _resolve_institution_id(auth, current_user, institution_id)
    teacher_id, is_directive = await _resolve_teacher_scope(
        db, auth, current_user, target_institution_id
    )
    svc = EvaluationService(session=db)
    sheet = await svc.get_period_sheet(
        institution_id=target_institution_id,
        period_id=period_id,
        group_id=group_id,
        subject_id=subject_id,
        teacher_id=teacher_id,
        is_directive=is_directive,
    )
    return PeriodSheetResponse.model_validate(sheet)


# ===========================================================================
# 2. Save Consolidated Period Grades
# ===========================================================================


@router.post(
    "/period-grades",
    response_model=SavePeriodGradesResponse,
    status_code=status.HTTP_200_OK,
    summary="Asentar calificaciones consolidadas del periodo",
    description=(
        "Guarda las calificaciones del periodo para un grupo y asignatura. "
        "Exige justificacion pedagogica obligatoria si la nota definitiva difiere de la calculada (DECISION-16-03)."
    ),
    dependencies=[Depends(require_permission("evaluations", "grade"))],
)
@router.post(
    "/period-sheet/save",
    response_model=SavePeriodGradesResponse,
    status_code=status.HTTP_200_OK,
    include_in_schema=False,
    dependencies=[Depends(require_permission("evaluations", "grade"))],
)
async def save_period_grades(
    payload: SavePeriodGradesRequest,
    db: SessionDep,
    auth: AuthContextDep,
    current_user: CurrentUserDep,
    institution_id: Annotated[
        uuid.UUID | None,
        Query(description="Override institucional (solo SuperAdmin / NationalAdmin)"),
    ] = None,
) -> SavePeriodGradesResponse:
    target_institution_id = _resolve_institution_id(auth, current_user, institution_id)
    teacher_id, is_directive = await _resolve_teacher_scope(
        db, auth, current_user, target_institution_id
    )
    svc = EvaluationService(session=db)
    items_dicts = [item.model_dump() for item in payload.items]
    achievements_dicts = (
        [a.model_dump() for a in payload.achievements]
        if payload.achievements
        else None
    )
    saved = await svc.save_period_grades(
        institution_id=target_institution_id,
        period_id=payload.period_id,
        group_id=payload.group_id,
        subject_id=payload.subject_id,
        teacher_id=teacher_id,
        items=items_dicts,
        achievements=achievements_dicts,
        user_id=current_user.id,
        is_directive=is_directive,
    )
    await db.commit()
    return SavePeriodGradesResponse(
        saved_count=len(saved),
        period_id=payload.period_id,
        group_id=payload.group_id,
        subject_id=payload.subject_id,
    )


# ===========================================================================
# 3. Recovery / Remediation Grade Recording
# ===========================================================================


@router.post(
    "/grades/{grade_id}/recoveries",
    response_model=RecoveryGradeResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar recuperacion o nivelacion",
    description=(
        "Asienta una nota de recuperacion/nivelacion. "
        "Aplica el tope institucional SIEE (recovery cap) y preserva la nota inicial de forma inmutable."
    ),
    dependencies=[Depends(require_permission("evaluations", "recovery"))],
)
@router.post(
    "/grades/{grade_id}/recovery",
    response_model=RecoveryGradeResponse,
    status_code=status.HTTP_201_CREATED,
    include_in_schema=False,
    dependencies=[Depends(require_permission("evaluations", "recovery"))],
)
async def record_recovery_grade(
    grade_id: uuid.UUID,
    payload: RecordRecoveryGradeRequest,
    db: SessionDep,
    auth: AuthContextDep,
    current_user: CurrentUserDep,
    institution_id: Annotated[
        uuid.UUID | None,
        Query(description="Override institucional (solo SuperAdmin / NationalAdmin)"),
    ] = None,
) -> RecoveryGradeResponse:
    target_institution_id = _resolve_institution_id(auth, current_user, institution_id)
    teacher_id, is_directive = await _resolve_teacher_scope(
        db, auth, current_user, target_institution_id
    )
    svc = EvaluationService(session=db)
    recovery = await svc.record_recovery_grade(
        institution_id=target_institution_id,
        grade_id=grade_id,
        recovery_score=payload.recovery_score,
        recovery_date=payload.recovery_date,
        act_number=payload.act_number,
        observations=payload.observations,
        teacher_id=teacher_id or current_user.id,
        user_id=current_user.id,
        is_directive=is_directive,
    )
    await db.commit()
    return RecoveryGradeResponse.model_validate(recovery)


# ===========================================================================
# 4. Period Closure and Reopening Workflows
# ===========================================================================


@router.post(
    "/periods/{period_id}/close",
    response_model=ClosePeriodResponse,
    status_code=status.HTTP_200_OK,
    summary="Cerrar y sellar periodo academico",
    description="Cierra oficialmente el periodo academico y bloquea todas las calificaciones de forma inmutable.",
    dependencies=[Depends(require_permission("evaluations", "close_period"))],
)
async def close_academic_period(
    period_id: uuid.UUID,
    db: SessionDep,
    auth: AuthContextDep,
    current_user: CurrentUserDep,
    institution_id: Annotated[
        uuid.UUID | None,
        Query(description="Override institucional (solo SuperAdmin / NationalAdmin)"),
    ] = None,
) -> ClosePeriodResponse:
    target_institution_id = _resolve_institution_id(auth, current_user, institution_id)
    svc = EvaluationService(session=db)
    period = await svc.close_period(
        institution_id=target_institution_id,
        period_id=period_id,
        user_id=current_user.id,
    )
    await db.commit()
    return ClosePeriodResponse(
        period_id=period.id,
        is_closed=period.is_closed,
    )


@router.post(
    "/periods/{period_id}/unlock",
    response_model=UnlockPeriodResponse,
    status_code=status.HTTP_200_OK,
    summary="Reabrir periodo academico cerrado",
    description="Reabre un periodo cerrado con justificacion formal obligatoria y registro en auditoria.",
    dependencies=[Depends(require_permission("evaluations", "reopen_period"))],
)
async def unlock_academic_period(
    period_id: uuid.UUID,
    payload: UnlockPeriodRequest,
    db: SessionDep,
    auth: AuthContextDep,
    current_user: CurrentUserDep,
    institution_id: Annotated[
        uuid.UUID | None,
        Query(description="Override institucional (solo SuperAdmin / NationalAdmin)"),
    ] = None,
) -> UnlockPeriodResponse:
    target_institution_id = _resolve_institution_id(auth, current_user, institution_id)
    svc = EvaluationService(session=db)
    period = await svc.unlock_period(
        institution_id=target_institution_id,
        period_id=period_id,
        user_id=current_user.id,
        reason=payload.reason,
    )
    await db.commit()
    return UnlockPeriodResponse(
        period_id=period.id,
        is_closed=period.is_closed,
    )


# ===========================================================================
# 5. Student & Group Report Cards (Boletines y Sabanas de Notas)
# ===========================================================================


@router.get(
    "/report-cards/student/{student_id}",
    response_model=StudentReportCardResponse,
    status_code=status.HTTP_200_OK,
    summary="Consultar boletin periodico de calificaciones",
    description=(
        "Genera el boletin oficial de calificaciones de un periodo para el estudiante. "
        "Aplica control de acceso anti-IDOR estricto (Estudiante / Acudiente / Directivos)."
    ),
    dependencies=[Depends(require_permission("report_cards", "read"))],
)
async def get_student_report_card(
    student_id: uuid.UUID,
    period_id: Annotated[uuid.UUID, Query(description="ID del periodo academico")],
    db: SessionDep,
    auth: AuthContextDep,
    current_user: CurrentUserDep,
    institution_id: Annotated[
        uuid.UUID | None,
        Query(description="Override institucional (solo SuperAdmin / NationalAdmin)"),
    ] = None,
) -> StudentReportCardResponse:
    target_institution_id = _resolve_institution_id(auth, current_user, institution_id)
    await _verify_student_report_card_access(
        db, auth, current_user, target_institution_id, student_id
    )
    svc = ReportCardService(session=db)
    card = await svc.get_student_report_card(
        institution_id=target_institution_id,
        student_id=student_id,
        period_id=period_id,
        actor_user_id=current_user.id,
    )
    return StudentReportCardResponse.model_validate(card)


@router.get(
    "/report-cards/student/{student_id}/year-end",
    response_model=YearEndReportCardResponse,
    status_code=status.HTTP_200_OK,
    summary="Consultar boletin final acumulado de fin de ano",
    description=(
        "Genera el informe acumulado anual con ponderacion de periodos y dictamen de promocion. "
        "Aplica control de acceso anti-IDOR estricto."
    ),
    dependencies=[Depends(require_permission("report_cards", "read"))],
)
async def get_student_year_end_report_card(
    student_id: uuid.UUID,
    academic_year_id: Annotated[uuid.UUID, Query(description="ID del ano lectivo")],
    db: SessionDep,
    auth: AuthContextDep,
    current_user: CurrentUserDep,
    institution_id: Annotated[
        uuid.UUID | None,
        Query(description="Override institucional (solo SuperAdmin / NationalAdmin)"),
    ] = None,
) -> YearEndReportCardResponse:
    target_institution_id = _resolve_institution_id(auth, current_user, institution_id)
    await _verify_student_report_card_access(
        db, auth, current_user, target_institution_id, student_id
    )
    svc = ReportCardService(session=db)
    card = await svc.get_student_final_report_card(
        institution_id=target_institution_id,
        student_id=student_id,
        academic_year_id=academic_year_id,
        actor_user_id=current_user.id,
    )
    return YearEndReportCardResponse.model_validate(card)


@router.get(
    "/report-cards/group/{group_id}/matrix",
    response_model=GroupConsolidationMatrixResponse,
    status_code=status.HTTP_200_OK,
    summary="Consultar sabana de notas consolidada y ranking del grupo",
    description=(
        "Genera la matriz completa de calificaciones por asignatura y ranking del grupo. "
        "Uso exclusivo para Directivos y Docentes de la institucion."
    ),
    dependencies=[Depends(require_permission("report_cards", "read_group"))],
)
async def get_group_consolidation_matrix(
    group_id: uuid.UUID,
    period_id: Annotated[uuid.UUID, Query(description="ID del periodo academico")],
    db: SessionDep,
    auth: AuthContextDep,
    current_user: CurrentUserDep,
    institution_id: Annotated[
        uuid.UUID | None,
        Query(description="Override institucional (solo SuperAdmin / NationalAdmin)"),
    ] = None,
) -> GroupConsolidationMatrixResponse:
    target_institution_id = _resolve_institution_id(auth, current_user, institution_id)
    svc = ReportCardService(session=db)
    matrix = await svc.get_group_consolidation_matrix(
        institution_id=target_institution_id,
        group_id=group_id,
        period_id=period_id,
    )
    return GroupConsolidationMatrixResponse.model_validate(matrix)
