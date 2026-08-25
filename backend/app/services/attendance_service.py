"""
PEVN Backend — Attendance Domain Service

Authoritative business logic for tracking participant join/leave events,
calculating active session duration, and recording virtual classroom attendance.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.audit.interfaces import IAuditService
from app.audit.service import audit_service
from app.core.exceptions import VirtualClassroomNotFoundError
from app.core.logging import get_logger
from app.models.virtual_classroom import (
    MeetingAttendance,
    MeetingParticipantRole,
    VirtualClassroom,
)

_logger = get_logger(__name__)


class AttendanceService:
    """
    Domain service for tracking participant session attendance and active durations.
    """

    def __init__(
        self,
        session: AsyncSession,
        audit: IAuditService = audit_service,
    ) -> None:
        self._session = session
        self._audit = audit

    async def record_join(
        self,
        *,
        classroom_id: uuid.UUID,
        user_id: uuid.UUID,
        role: MeetingParticipantRole = MeetingParticipantRole.VIEWER,
    ) -> MeetingAttendance:
        """
        Records a participant join event with an open leave timestamp.
        """
        attendance = MeetingAttendance(
            virtual_classroom_id=classroom_id,
            user_id=user_id,
            role=role,
            joined_at=datetime.now(tz=UTC),
            left_at=None,
            duration_seconds=None,
        )
        self._session.add(attendance)
        await self._session.flush()
        return attendance

    async def record_leave(
        self,
        *,
        classroom_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> MeetingAttendance | None:
        """
        Records a participant leave event and calculates duration in seconds.
        """
        query = (
            select(MeetingAttendance)
            .where(
                MeetingAttendance.virtual_classroom_id == classroom_id,
                MeetingAttendance.user_id == user_id,
                MeetingAttendance.left_at.is_(None),
            )
            .order_by(MeetingAttendance.joined_at.desc())
        )
        res = await self._session.execute(query)
        attendance = res.scalars().first()

        if not attendance:
            return None

        leave_time = datetime.now(tz=UTC)
        attendance.left_at = leave_time

        # Ensure joined_at is timezone-aware for delta calculation
        joined_time = attendance.joined_at
        if joined_time.tzinfo is None:
            joined_time = joined_time.replace(tzinfo=UTC)

        delta = (leave_time - joined_time).total_seconds()
        attendance.duration_seconds = max(0, int(delta))

        await self._session.flush()
        return attendance

    async def close_open_attendances(
        self,
        *,
        classroom_id: uuid.UUID,
    ) -> int:
        """
        Closes all remaining open attendance logs when a session formally concludes.
        """
        query = select(MeetingAttendance).where(
            MeetingAttendance.virtual_classroom_id == classroom_id,
            MeetingAttendance.left_at.is_(None),
        )
        res = await self._session.execute(query)
        open_logs = list(res.scalars().all())

        now = datetime.now(tz=UTC)
        for log in open_logs:
            log.left_at = now
            joined_time = log.joined_at
            if joined_time.tzinfo is None:
                joined_time = joined_time.replace(tzinfo=UTC)
            delta = (now - joined_time).total_seconds()
            log.duration_seconds = max(0, int(delta))

        await self._session.flush()
        return len(open_logs)

    async def list_classroom_attendances(
        self,
        *,
        classroom_id: uuid.UUID,
        institution_id: uuid.UUID,
        skip: int = 0,
        limit: int = 100,
    ) -> tuple[list[MeetingAttendance], int]:
        """
        Lists attendance records for a virtual classroom within tenant scope.
        """
        # Validate classroom ownership
        classroom_query = select(VirtualClassroom).where(
            VirtualClassroom.id == classroom_id,
            VirtualClassroom.institution_id == institution_id,
        )
        c_res = await self._session.execute(classroom_query)
        classroom = c_res.scalars().first()

        if not classroom:
            raise VirtualClassroomNotFoundError()

        count_query = select(func.count(MeetingAttendance.id)).where(
            MeetingAttendance.virtual_classroom_id == classroom_id
        )
        count_res = await self._session.execute(count_query)
        total = count_res.scalar() or 0

        query = (
            select(MeetingAttendance)
            .options(selectinload(MeetingAttendance.user))
            .where(MeetingAttendance.virtual_classroom_id == classroom_id)
            .order_by(MeetingAttendance.joined_at.asc())
            .offset(skip)
            .limit(limit)
        )
        res = await self._session.execute(query)
        items = list(res.scalars().all())

        return items, total
