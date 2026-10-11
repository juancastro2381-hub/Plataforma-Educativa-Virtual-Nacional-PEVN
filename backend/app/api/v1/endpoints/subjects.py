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
    ClientIpDep,
    CurrentUserDep,
    SessionDep,
    require_permission,
    resolve_institution_id,
)
from app.audit.interfaces import AuditEvent, AuditEventType
from app.audit.service import audit_service
from app.core.exceptions import AcademicDomainError, CrossTenantMismatchError
from app.core.logging import correlation_id_ctx
from app.core.security.interfaces import SystemRole
from app.exceptions.errors import AuthorizationError
from app.models.grade import EducationalLevel, Grade
from app.models.subject import KnowledgeArea, Subject
from app.schemas.academic import (
    KnowledgeAreaListResponse,
    KnowledgeAreaResponse,
    SubjectCreateRequest,
    SubjectListResponse,
    SubjectResponse,
)

router = APIRouter(prefix="/subjects", tags=["Subjects"])
knowledge_areas_router = APIRouter(prefix="/knowledge-areas", tags=["Knowledge Areas"])

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


async def _resolve_institution_id(
    db: SessionDep,
    auth: AuthContextDep,
    current_user: CurrentUserDep,
    institution_id_override: uuid.UUID | None = None,
) -> uuid.UUID:
    """Resolve active institution context adhering to tenant isolation."""
    return await resolve_institution_id(
        db=db,
        auth=auth,
        current_user=current_user,
        institution_id_override=institution_id_override,
    )


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
    target_institution_id = await _resolve_institution_id(db, auth, current_user, institution_id)

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


@router.get(
    "/knowledge-areas",
    response_model=KnowledgeAreaListResponse,
    status_code=status.HTTP_200_OK,
    summary="Listar áreas de conocimiento",
    description="Devuelve las áreas fundamentales del currículo nacional y las institucionales.",
    dependencies=[Depends(require_permission("subjects", "read"))],
)
@knowledge_areas_router.get(
    "",
    response_model=KnowledgeAreaListResponse,
    status_code=status.HTTP_200_OK,
    summary="Listar áreas de conocimiento (directo)",
    description="Devuelve las áreas fundamentales del currículo nacional y las institucionales.",
    dependencies=[Depends(require_permission("subjects", "read"))],
)
async def list_knowledge_areas(
    db: SessionDep,
    auth: AuthContextDep,
    current_user: CurrentUserDep,
    institution_id: Annotated[uuid.UUID | None, Query(description="Override for SuperAdmin only")] = None,
) -> KnowledgeAreaListResponse:
    """List curricular knowledge areas accessible to the institutional context."""
    target_institution_id = await _resolve_institution_id(db, auth, current_user, institution_id)
    query = (
        select(KnowledgeArea)
        .where(
            (KnowledgeArea.institution_id.is_(None)) | (KnowledgeArea.institution_id == target_institution_id)
        )
        .order_by(KnowledgeArea.name.asc())
    )
    result = await db.execute(query)
    kas = list(result.scalars().all())
    return KnowledgeAreaListResponse(
        items=[KnowledgeAreaResponse.model_validate(k) for k in kas],
        total=len(kas),
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
    client_ip: ClientIpDep,
    institution_id: Annotated[uuid.UUID | None, Query(description="Override for SuperAdmin only")] = None,
) -> SubjectResponse:
    """Create a new curricular subject."""
    target_institution_id = await _resolve_institution_id(db, auth, current_user, institution_id)
    clean_name = payload.name.strip()

    # Validate Knowledge Area
    ka = (await db.execute(select(KnowledgeArea).where(KnowledgeArea.id == payload.knowledge_area_id))).scalar_one_or_none()
    if not ka:
        raise AcademicDomainError("Área de conocimiento no encontrada.")

    # Validate Grade
    gr = (await db.execute(select(Grade).where(Grade.id == payload.grade_id))).scalar_one_or_none()
    if not gr:
        raise AcademicDomainError("Grado curricular no encontrado.")

    # Duplicate name check for same grade in this institution
    existing_stmt = select(Subject.id).where(
        Subject.institution_id == target_institution_id,
        Subject.grade_id == payload.grade_id,
        Subject.name.ilike(clean_name),
    )
    existing = (await db.execute(existing_stmt)).scalar_one_or_none()
    if existing:
        raise AcademicDomainError(
            f"Ya existe una asignatura con el nombre '{clean_name}' para el grado {gr.name} en esta institución."
        )

    subject = Subject(
        institution_id=target_institution_id,
        knowledge_area_id=payload.knowledge_area_id,
        grade_id=payload.grade_id,
        name=clean_name,
        weekly_hours=payload.weekly_hours,
    )
    db.add(subject)
    await db.flush()

    correlation_id = correlation_id_ctx.get()
    await audit_service.record(
        AuditEvent(
            event_type=AuditEventType.SUBJECT_CREATED,
            actor_id=str(current_user.id),
            actor_ip=client_ip,
            target_id=str(subject.id),
            target_type="Subject",
            institution_id=str(target_institution_id),
            correlation_id=correlation_id,
            metadata={
                "name": subject.name,
                "grade_id": str(payload.grade_id),
                "knowledge_area_id": str(payload.knowledge_area_id),
                "weekly_hours": payload.weekly_hours,
            },
        ),
        session=db,
    )

    await db.commit()
    await db.refresh(subject)
    return SubjectResponse.model_validate(subject)

