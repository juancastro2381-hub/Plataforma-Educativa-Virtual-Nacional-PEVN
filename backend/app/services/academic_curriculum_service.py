"""
PEVN Backend — Centralized Academic Curriculum Resolution Service (Phase 16E)

Authoritative business logic for resolving the complete curriculum subject matrix
for students and classroom groups.

Key Principles:
1. Every student's curriculum is defined by their valid institutional enrollment,
   grade level, and approved institutional study plan, NOT by the mere presence
   of existing grade records.
2. In Colombian statutory education (Ley 115 de 1994, Decreto 1290 de 2009), all
   statutory subjects belonging to the grade level curriculum are applicable to
   the enrolled student.
3. Active academic assignments (AcademicAssignment) enrich subjects with the
   designated teacher and group-specific weekly teaching intensity (I.H.).
4. Statutory subjects without an active teacher assignment remain visible in the
   curriculum matrix with pending teacher status, rather than being omitted.
5. Strict multi-tenant isolation by institution_id is enforced at all levels.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import (
    CrossTenantMismatchError,
    ReportCardAccessDeniedError,
)
from app.core.logging import get_logger
from app.models.academic_assignment import AcademicAssignment
from app.models.enrollment import Enrollment, EnrollmentStatus
from app.models.group import Group
from app.models.student import Student
from app.models.subject import KnowledgeArea, Subject
from app.models.teacher import Teacher

_logger = get_logger(__name__)


@dataclass(frozen=True)
class CurriculumSubjectItem:
    """
    Authoritative representation of a single subject within an academic curriculum.
    """

    subject_id: uuid.UUID
    subject_name: str
    knowledge_area_id: uuid.UUID | None
    knowledge_area_name: str
    is_mandatory: bool
    grade_id: uuid.UUID
    grade_name: str
    weekly_hours: int
    assignment_id: uuid.UUID | None = None
    teacher_id: uuid.UUID | None = None
    teacher_name: str | None = None
    teacher_email: str | None = None


@dataclass
class StudentCurriculumMatrix:
    """
    Authoritative resolution of a student's full curriculum matrix for an academic year.
    """

    student_id: uuid.UUID
    institution_id: uuid.UUID
    academic_year_id: uuid.UUID
    enrollment_id: uuid.UUID
    grade_id: uuid.UUID
    grade_name: str
    group_id: uuid.UUID
    group_name: str
    campus_id: uuid.UUID | None
    campus_name: str
    subjects: list[CurriculumSubjectItem]


class AcademicCurriculumService:
    """
    Centralized domain service responsible for determining the complete
    curriculum matrix applicable to a student or group.
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def resolve_student_curriculum(
        self,
        *,
        institution_id: uuid.UUID,
        student_id: uuid.UUID,
        academic_year_id: uuid.UUID,
    ) -> StudentCurriculumMatrix:
        """
        Resolve the complete applicable subject matrix for an enrolled student.

        1. Fetches and validates active enrollment for the specified year.
        2. Validates multi-tenant boundaries.
        3. Retrieves active teacher assignments for the student's group.
        4. Retrieves all statutory and institutional subjects approved for the student's grade.
        5. Merges assignments and statutory subjects into a complete canonical matrix.
        """
        # 1. Fetch Student & Multi-tenant boundary check
        st_stmt = select(Student).where(Student.id == student_id)
        student = (await self._session.execute(st_stmt)).scalars().first()
        if not student or student.institution_id != institution_id:
            raise CrossTenantMismatchError("Estudiante no encontrado en esta institución.")

        # 2. Fetch Enrollment with Group, Grade, and Campus
        enr_stmt = (
            select(Enrollment)
            .where(
                Enrollment.student_id == student_id,
                Enrollment.academic_year_id == academic_year_id,
                Enrollment.status.in_([EnrollmentStatus.ACTIVE, EnrollmentStatus.GRADUATED]),
            )
            .options(
                selectinload(Enrollment.group).selectinload(Group.grade),
                selectinload(Enrollment.group).selectinload(Group.campus),
            )
        )
        enrollment = (await self._session.execute(enr_stmt)).scalars().first()
        if not enrollment or not enrollment.group:
            raise ReportCardAccessDeniedError(
                "El estudiante no cuenta con una matrícula válida para este año escolar."
            )

        group = enrollment.group
        if group.campus and group.campus.institution_id != institution_id:
            raise CrossTenantMismatchError(
                "El grupo matriculado no pertenece a la institución educativa."
            )

        grade_id = group.grade_id
        grade_name = group.grade.name if group.grade else ""
        campus_id = group.campus.id if group.campus else None
        campus_name = group.campus.name if group.campus else "Sede Principal"

        # 3. Resolve Group Subjects
        curriculum_subjects = await self.resolve_group_curriculum(
            institution_id=institution_id,
            group_id=group.id,
            academic_year_id=academic_year_id,
            grade_id=grade_id,
            grade_name=grade_name,
        )

        return StudentCurriculumMatrix(
            student_id=student.id,
            institution_id=institution_id,
            academic_year_id=academic_year_id,
            enrollment_id=enrollment.id,
            grade_id=grade_id,
            grade_name=grade_name,
            group_id=group.id,
            group_name=group.name,
            campus_id=campus_id,
            campus_name=campus_name,
            subjects=curriculum_subjects,
        )

    async def resolve_group_curriculum(
        self,
        *,
        institution_id: uuid.UUID,
        group_id: uuid.UUID,
        academic_year_id: uuid.UUID,
        grade_id: uuid.UUID | None = None,
        grade_name: str | None = None,
    ) -> list[CurriculumSubjectItem]:
        """
        Resolve the complete applicable subject list for a group section.

        Combines:
        - Active academic assignments for the group section and academic year.
        - Statutory subjects configured for the group's grade level in the institution.
        """
        # Resolve group and grade if not preloaded
        if grade_id is None or grade_name is None:
            g_stmt = (
                select(Group)
                .where(Group.id == group_id)
                .options(selectinload(Group.grade), selectinload(Group.campus))
            )
            group = (await self._session.execute(g_stmt)).scalars().first()
            if not group or (group.campus and group.campus.institution_id != institution_id):
                raise CrossTenantMismatchError("El grupo no pertenece a la institución educativa.")
            grade_id = group.grade_id
            grade_name = group.grade.name if group.grade else ""

        # 1. Fetch active teacher assignments for the group
        as_stmt = (
            select(AcademicAssignment)
            .where(
                AcademicAssignment.group_id == group_id,
                AcademicAssignment.academic_year_id == academic_year_id,
                AcademicAssignment.is_active.is_(True),
            )
            .options(
                selectinload(AcademicAssignment.subject).selectinload(Subject.knowledge_area),
                selectinload(AcademicAssignment.teacher).selectinload(Teacher.user),
            )
        )
        assignments = list((await self._session.execute(as_stmt)).scalars().all())

        # 2. Fetch all statutory and institutional subjects for this grade
        sub_stmt = (
            select(Subject)
            .where(
                Subject.institution_id == institution_id,
                Subject.grade_id == grade_id,
            )
            .options(selectinload(Subject.knowledge_area))
        )
        statutory_subjects = list((await self._session.execute(sub_stmt)).scalars().all())

        # 3. Build Unified Matrix
        subjects_map: dict[uuid.UUID, CurriculumSubjectItem] = {}

        # First pass: Statutory subjects for the grade
        for s in statutory_subjects:
            area_name = s.knowledge_area.name if s.knowledge_area else "General"
            is_mand = s.knowledge_area.is_mandatory if s.knowledge_area else True
            subjects_map[s.id] = CurriculumSubjectItem(
                subject_id=s.id,
                subject_name=s.name,
                knowledge_area_id=s.knowledge_area_id,
                knowledge_area_name=area_name,
                is_mandatory=is_mand,
                grade_id=grade_id,
                grade_name=grade_name,
                weekly_hours=s.weekly_hours,
                assignment_id=None,
                teacher_id=None,
                teacher_name=None,
                teacher_email=None,
            )

        # Second pass: Overlay active assignments (provides assigned teacher and specific hours)
        for a in assignments:
            s = a.subject
            if not s:
                continue
            area_name = s.knowledge_area.name if s.knowledge_area else "General"
            is_mand = s.knowledge_area.is_mandatory if s.knowledge_area else True
            t_name = (
                f"{a.teacher.user.first_name} {a.teacher.user.last_name}".strip()
                if a.teacher and a.teacher.user
                else None
            )
            t_email = a.teacher.user.email if a.teacher and a.teacher.user else None

            subjects_map[s.id] = CurriculumSubjectItem(
                subject_id=s.id,
                subject_name=s.name,
                knowledge_area_id=s.knowledge_area_id,
                knowledge_area_name=area_name,
                is_mandatory=is_mand,
                grade_id=grade_id,
                grade_name=grade_name,
                weekly_hours=a.weekly_hours if a.weekly_hours > 0 else s.weekly_hours,
                assignment_id=a.id,
                teacher_id=a.teacher_id,
                teacher_name=t_name,
                teacher_email=t_email,
            )

        # 4. Canonical Sorting: Mandatory areas first, then Area name, then Subject name
        sorted_subjects = sorted(
            subjects_map.values(),
            key=lambda x: (
                0 if x.is_mandatory else 1,
                x.knowledge_area_name.lower(),
                x.subject_name.lower(),
            ),
        )

        _logger.debug(
            "Resolved curriculum for group %s: %d statutory subjects, %d assigned",
            group_id,
            len(statutory_subjects),
            len(assignments),
        )

        return sorted_subjects

