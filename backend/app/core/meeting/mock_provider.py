"""
PEVN Backend — Mock Meeting Provider

In-memory, deterministic implementation of IMeetingProvider for local development,
integration tests, and testing without requiring a live BigBlueButton cluster.
"""

from __future__ import annotations

import urllib.parse
import uuid
from datetime import UTC, datetime

from app.core.meeting.exceptions import (
    MeetingNotFoundError,
    MeetingProviderAuthError,
    MeetingProviderConnectionError,
)
from app.core.meeting.interfaces import (
    EndMeetingOptions,
    IMeetingProvider,
    JoinMeetingOptions,
    MeetingCreateOptions,
    MeetingInfo,
    RecordingInfo,
)


class MockMeetingProvider(IMeetingProvider):
    """
    Stateful in-memory mock meeting provider.

    Maintains meeting records, participant joins, and recording metadata.
    Provides hooks for testing failure scenarios.
    """

    def __init__(
        self, base_url: str = "https://mock.pevn.local/virtual-classroom"
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self._meetings: dict[str, MeetingCreateOptions] = {}
        self._running_state: dict[str, bool] = {}
        self._participants: dict[str, list[JoinMeetingOptions]] = {}
        self._recordings: dict[str, list[RecordingInfo]] = {}

        # Test simulation flags
        self.simulate_network_error: bool = False
        self.simulate_auth_error: bool = False
        self.simulate_not_found_on_query: bool = False

    def reset(self) -> None:
        """Clear all in-memory mock state."""
        self._meetings.clear()
        self._running_state.clear()
        self._participants.clear()
        self._recordings.clear()
        self.simulate_network_error = False
        self.simulate_auth_error = False
        self.simulate_not_found_on_query = False

    def _check_simulated_errors(self) -> None:
        if self.simulate_network_error:
            raise MeetingProviderConnectionError(
                "Simulated network timeout/connection error."
            )
        if self.simulate_auth_error:
            raise MeetingProviderAuthError("Simulated provider authentication failure.")

    async def create_meeting(self, options: MeetingCreateOptions) -> MeetingInfo:
        self._check_simulated_errors()

        self._meetings[options.meeting_id] = options
        self._running_state[options.meeting_id] = False
        self._participants[options.meeting_id] = []

        # If recording is enabled, pre-provision a mock recording
        if options.is_recording_enabled:
            rec_id = f"mock-rec-{uuid.uuid4().hex[:8]}"
            self._recordings[options.meeting_id] = [
                RecordingInfo(
                    record_id=rec_id,
                    meeting_id=options.meeting_id,
                    title=options.title,
                    playback_url=f"{self.base_url}/playback/{rec_id}",
                    duration_seconds=3600,
                    file_size_bytes=104857600,
                    is_published=True,
                    recorded_at=datetime.now(tz=UTC),
                )
            ]

        return MeetingInfo(
            meeting_id=options.meeting_id,
            title=options.title,
            is_running=False,
            participant_count=0,
            moderator_count=0,
            create_time=int(datetime.now(tz=UTC).timestamp()),
            metadata={"provider": "mock"},
        )

    async def generate_join_url(self, options: JoinMeetingOptions) -> str:
        self._check_simulated_errors()

        if options.meeting_id not in self._meetings:
            raise MeetingNotFoundError(
                f"Meeting '{options.meeting_id}' does not exist in mock provider."
            )

        # Mark meeting as running once someone joins
        self._running_state[options.meeting_id] = True
        self._participants.setdefault(options.meeting_id, []).append(options)

        query = urllib.parse.urlencode(
            {
                "meetingID": options.meeting_id,
                "fullName": options.user_name,
                "role": options.role,
                "userID": options.user_id,
            }
        )
        return f"{self.base_url}/join?{query}"

    async def end_meeting(self, options: EndMeetingOptions) -> bool:
        self._check_simulated_errors()

        if options.meeting_id not in self._meetings:
            raise MeetingNotFoundError(f"Meeting '{options.meeting_id}' not found.")

        self._running_state[options.meeting_id] = False
        return True

    async def is_meeting_running(self, meeting_id: str) -> bool:
        self._check_simulated_errors()

        if self.simulate_not_found_on_query:
            return False

        return self._running_state.get(meeting_id, False)

    async def get_meeting_info(
        self, meeting_id: str, moderator_password: str
    ) -> MeetingInfo:
        self._check_simulated_errors()

        if meeting_id not in self._meetings or self.simulate_not_found_on_query:
            raise MeetingNotFoundError(f"Meeting '{meeting_id}' not found.")

        meeting = self._meetings[meeting_id]
        participants = self._participants.get(meeting_id, [])
        is_running = self._running_state.get(meeting_id, False)

        mod_count = sum(1 for p in participants if p.role == "MODERATOR")

        return MeetingInfo(
            meeting_id=meeting_id,
            title=meeting.title,
            is_running=is_running,
            participant_count=len(participants),
            moderator_count=mod_count,
            create_time=int(datetime.now(tz=UTC).timestamp()),
            has_been_forcibly_ended=not is_running and len(participants) > 0,
        )

    async def get_recordings(self, meeting_id: str) -> list[RecordingInfo]:
        self._check_simulated_errors()

        if self.simulate_not_found_on_query:
            return []

        return self._recordings.get(meeting_id, [])
