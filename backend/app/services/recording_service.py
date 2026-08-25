"""
PEVN Backend — Recording Domain Service

Authoritative business logic for discovering, synchronizing, publishing,
and managing virtual classroom recording assets with multi-tenant isolation.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.audit.interfaces import AuditEvent, AuditEventType, IAuditService
from app.audit.service import audit_service
from app.core.exceptions import (
    RecordingNotFoundError,
    VirtualClassroomNotFoundError,
)
from app.core.logging import get_logger
from app.core.meeting import IMeetingProvider, get_meeting_provider
from app.models.virtual_classroom import MeetingRecording, VirtualClassroom

_logger = get_logger(__name__)


class RecordingService:
    """
    Domain service orchestrating recording discovery, metadata persistence,
    and access control.
    """

    def __init__(
        self,
        session: AsyncSession,
        provider: IMeetingProvider | None = None,
        audit: IAuditService = audit_service,
    ) -> None:
        self._session = session
        self._provider: IMeetingProvider = provider or get_meeting_provider()
        self._audit = audit

    async def sync_recordings_from_provider(
        self,
        *,
        classroom_id: uuid.UUID,
        institution_id: uuid.UUID,
        actor_id: uuid.UUID | str | None = None,
        actor_ip: str = "0.0.0.0",  # noqa: S104
        correlation_id: str | None = None,
    ) -> list[MeetingRecording]:
        """
        Queries provider for newly generated recordings and persists metadata locally.
        """
        # Validate classroom ownership
        query = select(VirtualClassroom).where(
            VirtualClassroom.id == classroom_id,
            VirtualClassroom.institution_id == institution_id,
        )
        res = await self._session.execute(query)
        classroom = res.scalars().first()

        if not classroom:
            raise VirtualClassroomNotFoundError()

        # Query provider recordings
        provider_recordings = await self._provider.get_recordings(
            classroom.bbb_meeting_id
        )

        synced_records: list[MeetingRecording] = []
        for rec in provider_recordings:
            # Check if recording is already stored
            rec_query = select(MeetingRecording).where(
                MeetingRecording.bbb_record_id == rec.record_id
            )
            r_res = await self._session.execute(rec_query)
            existing_rec = r_res.scalars().first()

            if existing_rec is None:
                new_rec = MeetingRecording(
                    institution_id=institution_id,
                    virtual_classroom_id=classroom_id,
                    bbb_record_id=rec.record_id,
                    playback_url=rec.playback_url,
                    duration_seconds=rec.duration_seconds,
                    file_size_bytes=rec.file_size_bytes,
                    is_published=rec.is_published,
                    recording_metadata=rec.metadata,
                    recorded_at=rec.recorded_at or datetime.now(tz=UTC),
                )
                self._session.add(new_rec)
                synced_records.append(new_rec)
            else:
                synced_records.append(existing_rec)

        await self._session.flush()

        await self._audit.record(
            AuditEvent(
                event_type=AuditEventType.RECORDING_SYNCED,
                actor_id=str(actor_id) if actor_id else None,
                actor_ip=actor_ip,
                target_id=str(classroom_id),
                target_type="VirtualClassroom",
                institution_id=str(institution_id),
                correlation_id=correlation_id,
                metadata={"synced_count": len(synced_records)},
            ),
            session=self._session,
        )

        return synced_records

    async def publish_recording(
        self,
        *,
        recording_id: uuid.UUID,
        institution_id: uuid.UUID,
        is_published: bool,
        actor_id: uuid.UUID | str | None = None,
        actor_ip: str = "0.0.0.0",  # noqa: S104
        correlation_id: str | None = None,
    ) -> MeetingRecording:
        """
        Updates recording visibility / publication status for student access.
        """
        query = select(MeetingRecording).where(
            MeetingRecording.id == recording_id,
            MeetingRecording.institution_id == institution_id,
        )
        res = await self._session.execute(query)
        recording = res.scalars().first()

        if not recording:
            raise RecordingNotFoundError()

        recording.is_published = is_published
        await self._session.flush()

        await self._audit.record(
            AuditEvent(
                event_type=AuditEventType.RECORDING_PUBLISHED,
                actor_id=str(actor_id) if actor_id else None,
                actor_ip=actor_ip,
                target_id=str(recording_id),
                target_type="MeetingRecording",
                institution_id=str(institution_id),
                correlation_id=correlation_id,
                metadata={"is_published": is_published},
            ),
            session=self._session,
        )

        return recording

    async def delete_recording(
        self,
        *,
        recording_id: uuid.UUID,
        institution_id: uuid.UUID,
        actor_id: uuid.UUID | str | None = None,
        actor_ip: str = "0.0.0.0",  # noqa: S104
        correlation_id: str | None = None,
    ) -> bool:
        """
        Deletes a recording metadata record within tenant boundary.
        """
        query = select(MeetingRecording).where(
            MeetingRecording.id == recording_id,
            MeetingRecording.institution_id == institution_id,
        )
        res = await self._session.execute(query)
        recording = res.scalars().first()

        if not recording:
            raise RecordingNotFoundError()

        await self._session.delete(recording)
        await self._session.flush()

        await self._audit.record(
            AuditEvent(
                event_type=AuditEventType.RECORDING_DELETED,
                actor_id=str(actor_id) if actor_id else None,
                actor_ip=actor_ip,
                target_id=str(recording_id),
                target_type="MeetingRecording",
                institution_id=str(institution_id),
                correlation_id=correlation_id,
            ),
            session=self._session,
        )

        return True

    async def list_recordings(
        self,
        *,
        classroom_id: uuid.UUID,
        institution_id: uuid.UUID,
        user_roles: list[str],
        skip: int = 0,
        limit: int = 50,
    ) -> tuple[list[MeetingRecording], int]:
        """
        Lists recording assets for a classroom. Students only see published recordings.
        """
        # Validate classroom ownership
        c_query = select(VirtualClassroom).where(
            VirtualClassroom.id == classroom_id,
            VirtualClassroom.institution_id == institution_id,
        )
        c_res = await self._session.execute(c_query)
        classroom = c_res.scalars().first()

        if not classroom:
            raise VirtualClassroomNotFoundError()

        filters = [
            MeetingRecording.virtual_classroom_id == classroom_id,
            MeetingRecording.institution_id == institution_id,
        ]

        is_staff = any(
            r in ("rector", "academic_coordinator", "teacher", "superadmin")
            for r in user_roles
        )
        if not is_staff:
            filters.append(MeetingRecording.is_published.is_(True))

        count_query = select(func.count(MeetingRecording.id)).where(*filters)
        count_res = await self._session.execute(count_query)
        total = count_res.scalar() or 0

        query = (
            select(MeetingRecording)
            .where(*filters)
            .order_by(MeetingRecording.recorded_at.desc())
            .offset(skip)
            .limit(limit)
        )
        res = await self._session.execute(query)
        items = list(res.scalars().all())

        return items, total
