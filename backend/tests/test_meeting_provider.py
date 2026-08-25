"""
PEVN Backend — Phase 4 Step 2: Meeting Provider & BigBlueButton Client Tests

Validates IMeetingProvider contract, BBBAdapter request construction,
cryptographic checksum signing, MockMeetingProvider state transitions,
factory resolution, and failure recovery.
"""

from __future__ import annotations

import hashlib
import urllib.parse

import httpx
import pytest

from app.core.config import Settings
from app.core.meeting import (
    BBBAdapter,
    EndMeetingOptions,
    IMeetingProvider,
    JoinMeetingOptions,
    MeetingCreateOptions,
    MeetingNotFoundError,
    MeetingProviderAuthError,
    MeetingProviderConfigError,
    MeetingProviderConnectionError,
    MeetingProviderResponseError,
    MockMeetingProvider,
    get_meeting_provider,
)

# =============================================================================
# 1. Cryptographic Checksum & Signature Unit Tests
# =============================================================================


def test_bbb_adapter_sha1_checksum_calculation() -> None:
    """Verifies deterministic SHA-1 checksum signing against known vector."""
    api_url = "https://bbb.pevn.gov.co/bigbluebutton/api"
    secret = "pevn_test_salt_87391"
    adapter = BBBAdapter(
        api_url=api_url, shared_secret=secret, signing_algorithm="sha1"
    )

    call_name = "create"
    query_str = "meetingID=sala-10-A&name=Matematicas+Decimo"
    expected_payload = f"{call_name}{query_str}{secret}".encode()
    expected_checksum = hashlib.sha1(expected_payload).hexdigest()  # noqa: S324

    actual_checksum = adapter.calculate_checksum(call_name, query_str)
    assert actual_checksum == expected_checksum


def test_bbb_adapter_sha256_checksum_calculation() -> None:
    """Verifies deterministic SHA-256 checksum signing."""
    api_url = "https://bbb.pevn.gov.co/bigbluebutton/api"
    secret = "pevn_test_salt_87391"
    adapter = BBBAdapter(
        api_url=api_url, shared_secret=secret, signing_algorithm="sha256"
    )

    call_name = "getMeetingInfo"
    query_str = "meetingID=sala-10-A"
    expected_payload = f"{call_name}{query_str}{secret}".encode()
    expected_checksum = hashlib.sha256(expected_payload).hexdigest()

    actual_checksum = adapter.calculate_checksum(call_name, query_str)
    assert actual_checksum == expected_checksum


def test_bbb_adapter_build_api_url_formatting() -> None:
    """Verifies complete query string construction with checksum appended."""
    api_url = "https://bbb.pevn.gov.co/bigbluebutton/api"
    secret = "my_secret_key"
    adapter = BBBAdapter(api_url=api_url, shared_secret=secret)

    params = {
        "meetingID": "room-01",
        "fullName": "Carlos Gomez",
        "role": "MODERATOR",
    }
    url = adapter.build_api_url("join", params)

    assert url.startswith(f"{api_url}/join?")
    assert "meetingID=room-01" in url
    assert "fullName=Carlos+Gomez" in url
    assert "role=MODERATOR" in url
    assert "checksum=" in url

    # Parse and verify checksum
    parsed = urllib.parse.urlparse(url)
    query_dict = urllib.parse.parse_qs(parsed.query)
    assert "checksum" in query_dict
    assert len(query_dict["checksum"][0]) == 40  # SHA-1 hex length


def test_bbb_adapter_secret_protection_in_repr() -> None:
    """Verifies shared secret is never exposed in object representation or logs."""
    adapter = BBBAdapter(
        api_url="https://bbb.pevn.gov.co/bigbluebutton/api",
        shared_secret="super_secret_salt_12345",
    )
    repr_str = repr(adapter)
    assert "super_secret_salt_12345" not in repr_str
    assert "[PROTECTED]" in repr_str


def test_bbb_adapter_config_validation() -> None:
    """Verifies adapter fails fast when misconfigured."""
    with pytest.raises(MeetingProviderConfigError, match="BBB_API_URL"):
        BBBAdapter(api_url="", shared_secret="secret")

    with pytest.raises(
        MeetingProviderConfigError, match="Algoritmo de firma no soportado"
    ):
        BBBAdapter(
            api_url="https://bbb.example.com",
            shared_secret="secret",
            signing_algorithm="md5",
        )


# =============================================================================
# 2. BBBAdapter Async HTTP Client & Response Parsing Tests (Mocked Transport)
# =============================================================================


class MockTransport(httpx.AsyncBaseTransport):
    """Custom HTTP transport that returns simulated BigBlueButton XML responses."""

    def __init__(self, responses: dict[str, tuple[int, str]]) -> None:
        self.responses = responses

    async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
        for pattern, (status, body) in self.responses.items():
            if pattern in str(request.url):
                return httpx.Response(
                    status_code=status,
                    text=body,
                    headers={"Content-Type": "application/xml"},
                    request=request,
                )
        return httpx.Response(status_code=404, text="Not Found", request=request)


@pytest.mark.asyncio
async def test_bbb_adapter_create_meeting_success() -> None:
    """Tests successful meeting creation and XML response parsing."""
    mock_xml = """<?xml version="1.0"?>
    <response>
        <returncode>SUCCESS</returncode>
        <meetingID>pevn-room-101</meetingID>
        <internalMeetingID>bbb-internal-999</internalMeetingID>
        <createTime>1700000000</createTime>
    </response>"""

    transport = MockTransport({"/create": (200, mock_xml)})
    async with httpx.AsyncClient(transport=transport) as client:
        adapter = BBBAdapter(
            api_url="https://bbb.mock/api",
            shared_secret="test_secret",
            http_client=client,
        )

        options = MeetingCreateOptions(
            meeting_id="pevn-room-101",
            title="Clase de Física",
            moderator_password="mod_password_1",
            attendee_password="att_password_1",
            is_recording_enabled=True,
            max_participants=40,
        )
        info = await adapter.create_meeting(options)

        assert info.meeting_id == "pevn-room-101"
        assert info.title == "Clase de Física"
        assert info.create_time == 1700000000
        assert info.metadata.get("bbb_internal_id") == "bbb-internal-999"


@pytest.mark.asyncio
async def test_bbb_adapter_get_meeting_info_and_is_running() -> None:
    """Tests fetching live meeting telemetry and active running state."""
    mock_info_xml = """<?xml version="1.0"?>
    <response>
        <returncode>SUCCESS</returncode>
        <meetingName>Biología General</meetingName>
        <meetingID>pevn-bio-01</meetingID>
        <running>true</running>
        <participantCount>28</participantCount>
        <moderatorCount>2</moderatorCount>
        <createTime>1700001000</createTime>
        <hasBeenForciblyEnded>false</hasBeenForciblyEnded>
    </response>"""

    mock_running_xml = """<?xml version="1.0"?>
    <response>
        <returncode>SUCCESS</returncode>
        <running>true</running>
    </response>"""

    transport = MockTransport(
        {
            "/getMeetingInfo": (200, mock_info_xml),
            "/isMeetingRunning": (200, mock_running_xml),
        }
    )

    async with httpx.AsyncClient(transport=transport) as client:
        adapter = BBBAdapter(
            api_url="https://bbb.mock/api",
            shared_secret="test_secret",
            http_client=client,
        )

        is_running = await adapter.is_meeting_running("pevn-bio-01")
        assert is_running is True

        info = await adapter.get_meeting_info("pevn-bio-01", "mod_pwd")
        assert info.meeting_id == "pevn-bio-01"
        assert info.title == "Biología General"
        assert info.is_running is True
        assert info.participant_count == 28
        assert info.moderator_count == 2


@pytest.mark.asyncio
async def test_bbb_adapter_get_recordings_success() -> None:
    """Tests parsing recording assets and playback URLs."""
    mock_rec_xml = """<?xml version="1.0"?>
    <response>
        <returncode>SUCCESS</returncode>
        <recordings>
            <recording>
                <recordID>rec-xyz-999</recordID>
                <name>Sesión de Química Orgánica</name>
                <published>true</published>
                <startTime>1700000000000</startTime>
                <playback>
                    <format>
                        <type>presentation</type>
                        <url>https://bbb.mock/playback/presentation/2.3/rec-xyz-999</url>
                        <length>45</length>
                    </format>
                </playback>
            </recording>
        </recordings>
    </response>"""

    transport = MockTransport({"/getRecordings": (200, mock_rec_xml)})
    async with httpx.AsyncClient(transport=transport) as client:
        adapter = BBBAdapter(
            api_url="https://bbb.mock/api",
            shared_secret="test_secret",
            http_client=client,
        )

        recordings = await adapter.get_recordings("pevn-qui-01")
        assert len(recordings) == 1
        assert recordings[0].record_id == "rec-xyz-999"
        assert recordings[0].title == "Sesión de Química Orgánica"
        assert recordings[0].duration_seconds == 2700  # 45 mins * 60
        assert recordings[0].playback_url.startswith("https://bbb.mock/playback")


@pytest.mark.asyncio
async def test_bbb_adapter_end_meeting_success() -> None:
    """Tests meeting termination."""
    mock_end_xml = """<?xml version="1.0"?>
    <response>
        <returncode>SUCCESS</returncode>
        <messageKey>sentEndMeetingRequest</messageKey>
    </response>"""

    transport = MockTransport({"/end": (200, mock_end_xml)})
    async with httpx.AsyncClient(transport=transport) as client:
        adapter = BBBAdapter(
            api_url="https://bbb.mock/api",
            shared_secret="test_secret",
            http_client=client,
        )

        ended = await adapter.end_meeting(
            EndMeetingOptions(meeting_id="pevn-01", moderator_password="mod_pwd")
        )
        assert ended is True


@pytest.mark.asyncio
async def test_bbb_adapter_error_mapping() -> None:
    """Tests mapping of BigBlueButton error XML returncodes to domain exceptions."""
    xml_not_found = """<?xml version="1.0"?>
    <response>
        <returncode>FAILED</returncode>
        <messageKey>notFound</messageKey>
        <message>We could not find a meeting with that ID.</message>
    </response>"""

    xml_checksum_err = """<?xml version="1.0"?>
    <response>
        <returncode>FAILED</returncode>
        <messageKey>checksumError</messageKey>
        <message>You did not pass the checksum security check.</message>
    </response>"""

    xml_generic_err = """<?xml version="1.0"?>
    <response>
        <returncode>FAILED</returncode>
        <messageKey>maxParticipantsReached</messageKey>
        <message>The room is full.</message>
    </response>"""

    transport = MockTransport(
        {
            "/notFound": (200, xml_not_found),
            "/checksumErr": (200, xml_checksum_err),
            "/genericErr": (200, xml_generic_err),
            "/serverError": (500, "Internal Server Error"),
        }
    )

    async with httpx.AsyncClient(transport=transport) as client:
        adapter = BBBAdapter(
            api_url="https://bbb.mock/api",
            shared_secret="test_secret",
            http_client=client,
        )

        with pytest.raises(MeetingNotFoundError):
            await adapter._send_request("notFound", {})

        with pytest.raises(MeetingProviderAuthError):
            await adapter._send_request("checksumErr", {})

        with pytest.raises(MeetingProviderResponseError, match="The room is full"):
            await adapter._send_request("genericErr", {})

        with pytest.raises(MeetingProviderConnectionError, match="HTTP 500"):
            await adapter._send_request("serverError", {})


# =============================================================================
# 3. MockMeetingProvider State & Lifecycle Tests
# =============================================================================


@pytest.mark.asyncio
async def test_mock_meeting_provider_lifecycle() -> None:
    """Tests complete in-memory mock lifecycle: create, join, running, end, recordings."""
    mock = MockMeetingProvider()
    assert isinstance(mock, IMeetingProvider)

    # 1. Create meeting
    options = MeetingCreateOptions(
        meeting_id="mock-101",
        title="Matemáticas Básicas",
        moderator_password="mod",
        attendee_password="att",
        is_recording_enabled=True,
    )
    info = await mock.create_meeting(options)
    assert info.meeting_id == "mock-101"
    assert info.is_running is False

    # 2. Join meeting
    join_opt = JoinMeetingOptions(
        meeting_id="mock-101",
        user_name="Profesor Gomez",
        password="mod",
        user_id="usr-teacher-1",
        role="MODERATOR",
    )
    join_url = await mock.generate_join_url(join_opt)
    assert "https://mock.pevn.local/virtual-classroom/join" in join_url
    assert "meetingID=mock-101" in join_url

    # Verify meeting is now running
    is_running = await mock.is_meeting_running("mock-101")
    assert is_running is True

    # 3. Telemetry
    meeting_info = await mock.get_meeting_info("mock-101", "mod")
    assert meeting_info.is_running is True
    assert meeting_info.participant_count == 1
    assert meeting_info.moderator_count == 1

    # 4. Recordings
    recordings = await mock.get_recordings("mock-101")
    assert len(recordings) == 1
    assert recordings[0].meeting_id == "mock-101"

    # 5. End meeting
    ended = await mock.end_meeting(
        EndMeetingOptions(meeting_id="mock-101", moderator_password="mod")
    )
    assert ended is True
    assert await mock.is_meeting_running("mock-101") is False


@pytest.mark.asyncio
async def test_mock_meeting_provider_simulated_errors() -> None:
    """Tests simulated error injection on MockMeetingProvider."""
    mock = MockMeetingProvider()

    mock.simulate_network_error = True
    with pytest.raises(MeetingProviderConnectionError):
        await mock.create_meeting(
            MeetingCreateOptions(
                meeting_id="m1",
                title="T1",
                moderator_password="m",
                attendee_password="a",
            )
        )

    mock.reset()
    mock.simulate_auth_error = True
    with pytest.raises(MeetingProviderAuthError):
        await mock.create_meeting(
            MeetingCreateOptions(
                meeting_id="m1",
                title="T1",
                moderator_password="m",
                attendee_password="a",
            )
        )


# =============================================================================
# 4. Meeting Provider Factory Tests
# =============================================================================


def test_meeting_provider_factory_resolution() -> None:
    """Tests factory resolves MockMeetingProvider or BBBAdapter based on settings."""
    settings_mock = Settings(MEETING_PROVIDER_TYPE="mock")
    provider_mock = get_meeting_provider(settings_mock)
    assert isinstance(provider_mock, MockMeetingProvider)

    settings_bbb = Settings(
        MEETING_PROVIDER_TYPE="bbb",
        BBB_API_URL="https://bbb.example.com/api",
        BBB_SHARED_SECRET="supersecret",
    )
    provider_bbb = get_meeting_provider(settings_bbb)
    assert isinstance(provider_bbb, BBBAdapter)
    assert provider_bbb.api_url == "https://bbb.example.com/api"
