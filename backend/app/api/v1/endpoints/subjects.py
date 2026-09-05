"""
PEVN Backend — Subjects API Endpoints

REST Controller for institutional curricular subjects (Plan de Estudios / Asignaturas),
supporting standardized statutory curriculum auto-seeding and institution-specific subject management.
Protected by RBAC permissions 'subjects:read' and 'subjects:create'.
"""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.api.deps import (
    AuthContextDep,
    CurrentUserDep,
    SessionDep,
    require_permission,
)
from app.core.exceptions import AcademicDomainError, CrossTenantMismatchError
from app.core.security.interfaces import SystemRole
from app.exceptions.errors import AuthorizationError
from app.models.grade import EducationalLevel, Grade
from app.models.subject import KnowledgeArea, Subject
from app.schemas.academic import (
    SubjectCreateRequest,
    SubjectListResponse,
    SubjectResponse,
)

router = APIRouter(prefix="/subjects", tags=["Subjects"])

# Statutory Colombian curriculum specifications
STANDARD_SUBJECT_SPECS = [
    ("Matemáticas", "Matemáticas", 4),
    ("Humanidades, Lengua Castellana e Idiomas Extranjeros", "Lengua Castellana", 4),
    ("Humanidades, Lengua Castellana e Idiomas Extranjeros", "Inglés", 3),
    ("Ciencias Naturales y Educación Ambiental", "Ciencias Naturales y Educación Ambiental", 4),
    ("Ciencias Sociales, Historia, Geografía y Democracia", "Ciencias Sociales", 3),
    ("Educación Artística y Cultural", "Educación Artística", 2),
    ("Educación Ética y en Valores Humanos", "Ética y Valores", 1),
    ("Educación Física, Recreación y Deportes", "Educación Física, Recreación y Deporte", 2),
    ("Tecnología e Informática", "Tecnología e Informática", 2),
    ("Educación Religiosa", "Educación Religiosa", 1),
]

MEDIA_SUBJECT_SPECS = [
    ("Matemáticas", "Cálculo y Trigonometría", 4),
    ("Humanidades, Lengua Castellana e Idiomas Extranjeros", "Lengua Castellana y Literatura", 4),
    ("Humanidades, Lengua Castellana e Idiomas Extranjeros", "Inglés Avanzado", 3),
    ("Ciencias Naturales y Educación Ambiental", "Física", 3),
    ("Ciencias Naturales y Educación Ambiental", "Química", 3),
    ("Ciencias Sociales, Historia, Geografía y Democracia", "Filosofía y Ciencias Políticas", 3),
    ("Ciencias Sociales, Historia, Geografía y Democracia", "Ciencias Económicas", 2),
    ("Educación Artística y Cultural", "Educación Artística", 2),
    ("Educación Ética y en Valores Humanos", "Ética y Valores", 1),
    ("Educación Física, Recreación y Deportes", "Educación Física, Recreación y Deporte", 2),
    ("Tecnología e Informática", "Tecnología e Informática", 2),
    ("Educación Religiosa", "Educación Religiosa", 1),
]


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


async def _seed_statutory_subjects_if_needed(
    db: SessionDep,
    institution_id: uuid.UUID,
) -> None:
    """Auto-seed statutory Colombian curriculum subjects if the institution has none."""
    stmt_count = select(Subject.id).where(Subject.institution_id == institution_id).limit(1)
    existing_any = (await db.execute(stmt_count)).scalar_one_or_none()
    if existing_any is not None:
        return

    kas = (await db.execute(select(KnowledgeArea))).scalars().all()
    ka_by_name = {ka.name.strip().lower(): ka.id for ka in kas}

    grades = (await db.execute(select(Grade).order_by(Grade.ordinal_order))).scalars().all()

    for g in grades:
        specs = MEDIA_SUBJECT_SPECS if g.level == EducationalLevel.MEDIA else STANDARD_SUBJECT_SPECS
        for ka_spec_name, sub_name, hours in specs:
            target_key = ka_spec_name.strip().lower()
            ka_id = ka_by_name.get(target_key)
            if not ka_id:
                for k_name, kid in ka_by_name.items():
                    if target_key in k_name or k_name in target_key:
                        ka_id = kid
                        break
            if not ka_id:
                continue

            sub = Subject(
                institution_id=institution_id,
                knowledge_area_id=ka_id,
                grade_id=g.id,
                name=f"{sub_name} - {g.name}",
                weekly_hours=hours,
            )
            db.add(sub)

    await db.commit()


@router.get(
    "",
    response_model=SubjectListResponse,
    status_code=status.HTTP_200_OK,
    summary="Listar asignaturas curriculares",
    description="Devuelve las asignaturas del plan de estudios de la institución con filtros opcionales.",
    dependencies=[Depends(require_permission("subjects", "read"))],
)
async def list_subjects(
    db: SessionDep,
    auth: AuthContextDep,
    current_user: CurrentUserDep,
    grade_id: Annotated[uuid.UUID | None, Query(description="Filtrar por grado")] = None,
    knowledge_area_id: Annotated[uuid.UUID | None, Query(description="Filtrar por área de conocimiento")] = None,
    institution_id: Annotated[uuid.UUID | None, Query(description="Override for SuperAdmin only")] = None,
) -> SubjectListResponse:
    """List curricular subjects adhering to multi-tenant isolation."""
    target_institution_id = _resolve_institution_id(auth, current_user, institution_id)

    # Ensure statutory curriculum is bootstrapped for this institution
    await _seed_statutory_subjects_if_needed(db, target_institution_id)

    query = (
        select(Subject)
        .where(Subject.institution_id == target_institution_id)
        .options(selectinload(Subject.grade), selectinload(Subject.knowledge_area))
        .order_by(Subject.name.asc())
    )

    if grade_id is not None:
        query = query.where(Subject.grade_id == grade_id)
    if knowledge_area_id is not None:
        query = query.where(Subject.knowledge_area_id == knowledge_area_id)

    result = await db.execute(query)
    subjects = list(result.scalars().all())

    return SubjectListResponse(
        items=[SubjectResponse.model_validate(s) for s in subjects],
        total=len(subjects),
    )


@router.post(
    "",
    response_model=SubjectResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear asignatura curricular institucional",
    description="Registra una nueva asignatura en el plan de estudios de la institución.",
    dependencies=[Depends(require_permission("subjects", "create"))],
)
async def create_subject(
    payload: SubjectCreateRequest,
    db: SessionDep,
    auth: AuthContextDep,
    current_user: CurrentUserDep,
    institution_id: Annotated[uuid.UUID | None, Query(description="Override for SuperAdmin only")] = None,
) -> SubjectResponse:
    """Create a new curricular subject."""
    target_institution_id = _resolve_institution_id(auth, current_user, institution_id)

    # Validate Knowledge Area
    ka = (await db.execute(select(KnowledgeArea).where(KnowledgeArea.id == payload.knowledge_area_id))).scalar_one_or_none()
    if not ka:
        raise AcademicDomainError("Área de conocimiento no encontrada.")

    # Validate Grade
    gr = (await db.execute(select(Grade).where(Grade.id == payload.grade_id))).scalar_one_or_none()
    if not gr:
        raise AcademicDomainError("Grado curricular no encontrado.")

    subject = Subject(
        institution_id=target_institution_id,
        knowledge_area_id=payload.knowledge_area_id,
        grade_id=payload.grade_id,
        name=payload.name.strip(),
        weekly_hours=payload.weekly_hours,
    )
    db.add(subject)
    await db.commit()
    await db.refresh(subject)
    return SubjectResponse.model_validate(subject)
