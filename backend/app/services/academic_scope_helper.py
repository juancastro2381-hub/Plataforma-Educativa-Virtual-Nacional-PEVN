"""
PEVN Backend — Academic Scope Authorization Helper

Derives teacher academic scope boundaries based on:
1. Directive Roles: Full institutional visibility (Superadmin, National Admin,
   Institution Admin, Rector, Coordinator, Academic Coordinator).
2. Teacher Scope: Bounded strictly to active AcademicAssignment records
   and Group Director designations.
"""

from __future__ import annotations

import uuid
from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security.interfaces import AuthorizationContext, SystemRole
from app.models.academic_assignment import AcademicAssignment
from app.models.group import Group
from app.models.institution import Campus
from app.models.teacher import Teacher

DIRECTIVE_ROLES: frozenset[SystemRole] = frozenset(
    {
        SystemRole.SUPERADMIN,
        SystemRole.NATIONAL_ADMIN,
        SystemRole.DEPARTMENT_ADMIN,
        SystemRole.MUNICIPALITY_ADMIN,
        SystemRole.INSTITUTION_ADMIN,
        SystemRole.RECTOR,
        SystemRole.COORDINATOR,
        SystemRole.ACADEMIC_COORDINATOR,
    }
)


def is_directive_actor(
    auth: AuthorizationContext | None = None,
    user: User | None = None,
) -> bool:
    """
    Evaluate whether the actor has institutional/directive visibility.
    If neither auth nor user is provided (internal system/service calls), returns True.
    """
    if auth is None and user is None:
        return True

    if auth:
        if auth.scope.is_national() or SystemRole.SUPERADMIN in auth.roles:
            return True
        if any(r in DIRECTIVE_ROLES for r in auth.roles):
            return True

    if user and getattr(user, "user_roles", None):
        for ur in user.user_roles:
            if ur.role and ur.role.name in {r.value for r in DIRECTIVE_ROLES}:
                return True

    return False


async def get_teacher_authorized_group_ids(
    session: AsyncSession,
    *,
    user_id: uuid.UUID,
    institution_id: uuid.UUID,
) -> list[uuid.UUID]:
    """
    Resolve all authorized group IDs for a teacher within an institution.

    Combines:
    1. Groups from active AcademicAssignment records (teacher_id == teacher.id and is_active == True).
    2. Groups where the teacher is designated as group director (group_director_teacher_id == teacher.id).
    """
    # 1. Resolve Teacher ID from User
    t_stmt = select(Teacher.id).where(
        Teacher.user_id == user_id,
        Teacher.institution_id == institution_id,
    )
    teacher_id = (await session.execute(t_stmt)).scalar_one_or_none()
    if not teacher_id:
        return []

    # 2. Group IDs from active AcademicAssignment
    asg_stmt = select(AcademicAssignment.group_id).where(
        AcademicAssignment.teacher_id == teacher_id,
        AcademicAssignment.is_active == True,  # noqa: E712
    )
    asg_group_ids = (await session.execute(asg_stmt)).scalars().all()

    # 3. Group IDs from Group.group_director_teacher_id
    dir_stmt = (
        select(Group.id)
        .join(Campus, Group.campus_id == Campus.id)
        .where(
            Group.group_director_teacher_id == teacher_id,
            Campus.institution_id == institution_id,
        )
    )
    dir_group_ids = (await session.execute(dir_stmt)).scalars().all()

    return list(set(asg_group_ids) | set(dir_group_ids))
