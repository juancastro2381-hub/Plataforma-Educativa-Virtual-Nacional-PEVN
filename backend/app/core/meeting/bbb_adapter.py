"""
PEVN Backend — BigBlueButton (BBB) Provider Adapter

Implements the IMeetingProvider protocol to interface with a remote BigBlueButton
cluster using cryptographic checksum signing and async HTTP communication.
"""

from __future__ import annotations

import hashlib
import logging
import urllib.parse
import xml.etree.ElementTree as ET
from datetime import UTC, datetime
from http import HTTPStatus
from typing import Any

import httpx

from app.core.meeting.exceptions import (
    MeetingNotFoundError,
    MeetingProviderAuthError,
    MeetingProviderConfigError,
    MeetingProviderConnectionError,
    MeetingProviderResponseError,
)
from app.core.meeting.interfaces import (
    EndMeetingOptions,
    IMeetingProvider,
    JoinMeetingOptions,
    MeetingCreateOptions,
    MeetingInfo,
    RecordingInfo,
)

logger = logging.getLogger(__name__)


class BBBAdapter(IMeetingProvider):
    """
    BigBlueButton Concrete Meeting Provider Adapter.

    Translates domain-neutral meeting requests into signed BigBlueButton API calls.
    """

    def __init__(
        self,
        api_url: str,
        shared_secret: str,
        signing_algorithm: str = "sha1",
        timeout_seconds: float = 10.0,
        http_client: httpx.AsyncClient | None = None,
    ) -> None:
        """
        Initialize the BigBlueButton adapter.

        :param api_url: Base BigBlueButton API URL.
        :param shared_secret: Secret security salt configured on the server.
        :param signing_algorithm: Hash algorithm ("sha1" or "sha256").
        :param timeout_seconds: HTTP client timeout in seconds.
        :param http_client: Optional injected httpx.AsyncClient (for testing).
        """
        if not api_url:
            raise MeetingProviderConfigError("BBB_API_URL no puede estar vacío.")

        self.api_url = api_url.rstrip("/")
        self._shared_secret = shared_secret
        self.signing_algorithm = signing_algorithm.lower()
        self.timeout_seconds = timeout_seconds
        self._custom_client = http_client

        if self.signing_algorithm not in ("sha1", "sha256"):
            raise MeetingProviderConfigError(
                f"Algoritmo de firma no soportado: {signing_algorithm}. "
                "Use 'sha1' o 'sha256'."
            )

    def __repr__(self) -> str:
        """Secure representation hiding the secret salt."""
        return (
            f"<BBBAdapter api_url='{self.api_url}' "
            f"algorithm='{self.signing_algorithm}' secret='[PROTECTED]'>"
        )

    # -------------------------------------------------------------------------
    # Cryptographic Checksum & URL Construction
    # -------------------------------------------------------------------------

    def calculate_checksum(self, call_name: str, query_string: str) -> str:
        """
        Calculates the cryptographic checksum required by BigBlueButton:
        checksum = HASH(call_name + query_string + shared_secret)
        """
        if not self._shared_secret:
            raise MeetingProviderConfigError(
                "BBB_SHARED_SECRET no está configurado. "
                "Verifique las variables de entorno."
            )

        payload = f"{call_name}{query_string}{self._shared_secret}".encode()

        if self.signing_algorithm == "sha256":
            return hashlib.sha256(payload).hexdigest()
        return hashlib.sha1(payload).hexdigest()  # noqa: S324

    def build_api_url(self, call_name: str, params: dict[str, Any]) -> str:
        """
        Builds a signed BigBlueButton API endpoint URL with parameters and checksum.
        """
        clean_params = {
            k: str(v) for k, v in params.items() if v is not None and v != ""
        }
        query_string = urllib.parse.urlencode(clean_params)
        checksum = self.calculate_checksum(call_name, query_string)

        sep = "&" if query_string else ""
        return f"{self.api_url}/{call_name}?{query_string}{sep}checksum={checksum}"

    # -------------------------------------------------------------------------
    # HTTP Client & XML Parsing Helper
    # -------------------------------------------------------------------------

    async def _send_request(self, call_name: str, params: dict[str, Any]) -> ET.Element:
        """
        Sends an HTTP GET request to the BBB server and parses the XML response.
        """
        target_url = self.build_api_url(call_name, params)

        try:
            if self._custom_client is not None:
                response = await self._custom_client.get(
                    target_url, timeout=self.timeout_seconds
                )
            else:
                async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                    response = await client.get(target_url)

            if response.status_code >= HTTPStatus.BAD_REQUEST:
                raise MeetingProviderConnectionError(
                    f"El servidor BBB respondió con código HTTP {response.status_code}."
                )

            root = ET.fromstring(response.text)  # noqa: S314
        except httpx.RequestError as exc:
            logger.error("BBB communication error: %s", exc)
            raise MeetingProviderConnectionError(
                "Error de red al conectar con el servidor BigBlueButton."
            ) from exc
        except ET.ParseError as exc:
            logger.error("Invalid XML response from BBB: %s", exc)
            raise MeetingProviderResponseError(
                "Respuesta XML no válida devuelta por BigBlueButton."
            ) from exc

        returncode = root.findtext("returncode")
        if returncode != "SUCCESS":
            message_key = root.findtext("messageKey") or ""
            message = root.findtext("message") or f"BBB API Error: {message_key}"

            if message_key in ("notFound", "invalidMeetingIdentifier", "noRecordings"):
                raise MeetingNotFoundError(message)
            if message_key in ("checksumError", "invalidSecret"):
                raise MeetingProviderAuthError(message)

            raise MeetingProviderResponseError(message)

        return root

    # -------------------------------------------------------------------------
    # IMeetingProvider Implementation
    # -------------------------------------------------------------------------

    async def create_meeting(self, options: MeetingCreateOptions) -> MeetingInfo:
        """Provision a new meeting on the BigBlueButton server."""
        params: dict[str, Any] = {
            "name": options.title,
            "meetingID": options.meeting_id,
            "moderatorPW": options.moderator_password,
            "attendeePW": options.attendee_password,
            "record": "true" if options.is_recording_enabled else "false",
            "autoStartRecording": "false",
            "allowStartStopRecording": (
                "true" if options.is_recording_enabled else "false"
            ),
            "maxParticipants": options.max_participants,
        }

        if options.welcome_message:
            params["welcome"] = options.welcome_message
        if options.logout_url:
            params["logoutURL"] = options.logout_url

        for k, v in options.metadata.items():
            params[f"meta_{k}"] = v

        root = await self._send_request("create", params)

        create_time_str = root.findtext("createTime")
        create_time = (
            int(create_time_str)
            if create_time_str and create_time_str.isdigit()
            else None
        )

        return MeetingInfo(
            meeting_id=options.meeting_id,
            title=options.title,
            is_running=False,
            participant_count=0,
            moderator_count=0,
            create_time=create_time,
            metadata={"bbb_internal_id": root.findtext("internalMeetingID") or ""},
        )

    async def generate_join_url(self, options: JoinMeetingOptions) -> str:
        """Construct a signed participant join URL."""
        params: dict[str, Any] = {
            "meetingID": options.meeting_id,
            "fullName": options.user_name,
            "password": options.password,
            "userID": options.user_id,
            "role": options.role,
            "redirect": "true",
        }

        if options.redirect_url:
            params["logoutURL"] = options.redirect_url

        return self.build_api_url("join", params)

    async def end_meeting(self, options: EndMeetingOptions) -> bool:
        """Terminate an active meeting session."""
        params = {
            "meetingID": options.meeting_id,
            "password": options.moderator_password,
        }
        await self._send_request("end", params)
        return True

    async def is_meeting_running(self, meeting_id: str) -> bool:
        """Check whether a meeting is currently running."""
        params = {"meetingID": meeting_id}
        try:
            root = await self._send_request("isMeetingRunning", params)
            running_text = root.findtext("running")
            return running_text is not None and running_text.lower() == "true"
        except MeetingNotFoundError:
            return False

    async def get_meeting_info(
        self, meeting_id: str, moderator_password: str
    ) -> MeetingInfo:
        """Fetch session telemetry and active participant counts."""
        params = {
            "meetingID": meeting_id,
            "password": moderator_password,
        }
        root = await self._send_request("getMeetingInfo", params)

        title = root.findtext("meetingName") or ""
        running_text = root.findtext("running") or "false"
        is_running = running_text.lower() == "true"
        participant_count = int(root.findtext("participantCount") or 0)
        moderator_count = int(root.findtext("moderatorCount") or 0)
        create_time_str = root.findtext("createTime")
        create_time = (
            int(create_time_str)
            if create_time_str and create_time_str.isdigit()
            else None
        )
        has_ended = (root.findtext("hasBeenForciblyEnded") or "false").lower() == "true"

        return MeetingInfo(
            meeting_id=meeting_id,
            title=title,
            is_running=is_running,
            participant_count=participant_count,
            moderator_count=moderator_count,
            create_time=create_time,
            has_been_forcibly_ended=has_ended,
        )

    async def get_recordings(self, meeting_id: str) -> list[RecordingInfo]:
        """Fetch all recording assets associated with a meeting ID."""
        params = {"meetingID": meeting_id}
        try:
            root = await self._send_request("getRecordings", params)
        except MeetingNotFoundError:
            return []

        recordings: list[RecordingInfo] = []
        recordings_node = root.find("recordings")
        if recordings_node is None:
            return []

        for rec_node in recordings_node.findall("recording"):
            record_id = rec_node.findtext("recordID") or ""
            title = rec_node.findtext("name") or ""
            is_published = (rec_node.findtext("published") or "true").lower() == "true"
            start_time_str = rec_node.findtext("startTime")
            recorded_at = (
                datetime.fromtimestamp(int(start_time_str) / 1000.0, tz=UTC)
                if start_time_str and start_time_str.isdigit()
                else None
            )

            # Find playback format URL & duration
            playback_node = rec_node.find("playback")
            playback_url = ""
            duration_seconds = 0
            if playback_node is not None:
                format_node = playback_node.find("format")
                if format_node is not None:
                    playback_url = format_node.findtext("url") or ""
                    length_str = format_node.findtext("length")
                    duration_seconds = (
                        int(length_str) * 60
                        if length_str and length_str.isdigit()
                        else 0
                    )

            recordings.append(
                RecordingInfo(
                    record_id=record_id,
                    meeting_id=meeting_id,
                    title=title,
                    playback_url=playback_url,
                    duration_seconds=duration_seconds,
                    is_published=is_published,
                    recorded_at=recorded_at,
                )
            )

        return recordings
