"""
PEVN Backend — Virtual Classrooms Resilience & BBB Independence Integration Tests

Validates:
1. Classroom listing succeeds independently of BigBlueButton configuration (HTTP 200).
2. Empty classroom collections return HTTP 200 with appropriate metadata.
3. Existing scheduled classrooms in DB remain visible without BBB.
4. Scheduling / creating classrooms persists in DB without requiring active BBB connectivity.
5. Live meeting operations (join, launch) return controlled HTTP 503 BBB_NOT_CONFIGURED when unconfigured.
6. Provider network outages return controlled 503 instead of unhandled 500.
7. Database exceptions are not silently suppressed into empty collections.
8. Role-based access control (RBAC) and tenant isolation remain strictly enforced.
"""

from __future__ import annotations

import uuid
from typing import Any
from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.meeting.exceptions import BBBNotConfiguredError, MeetingProviderConnectionError
from app.core.meeting.factory import MeetingProviderStatus, check_meeting_provider_status
from app.models.virtual_classroom import VirtualClassroom, VirtualClassroomStatus
from tests.test_virtual_classroom_api import vc_api_fixture


@pytest.mark.asyncio
async def test_01_classroom_listing_succeeds_without_bbb_configuration(
    client: AsyncClient,
    vc_api_fixture: dict[str, Any],
) -> None:
    """Classroom listing must succeed with HTTP 200 even when BBB is unconfigured."""
    settings = get_settings()
    orig_provider = settings.MEETING_PROVIDER_TYPE
    orig_secret = settings.BBB_SHARED_SECRET
    settings.MEETING_PROVIDER_TYPE = "bbb"
    settings.BBB_SHARED_SECRET = ""

    try:
        teacher_hdr = vc_api_fixture["teacher_headers"]
        res = await client.get("/api/v1/virtual-classrooms", headers=teacher_hdr)
        assert res.status_code == 200
        data = res.json()
        assert "items" in data
        assert data["provider_configured"] is False
        assert data["provider_status"] == MeetingProviderStatus.NOT_CONFIGURED.value
        assert "pendiente de habilitación" in data["provider_message"].lower()
    finally:
        settings.MEETING_PROVIDER_TYPE = orig_provider
        settings.BBB_SHARED_SECRET = orig_secret


@pytest.mark.asyncio
async def test_02_empty_classroom_listing_returns_http_200(
    client: AsyncClient,
    vc_api_fixture: dict[str, Any],
) -> None:
    """An empty classroom listing returns HTTP 200 with total=0 and items=[]."""
    tenant2_hdr = vc_api_fixture["tenant2_headers"]
    res = await client.get("/api/v1/virtual-classrooms", headers=tenant2_hdr)
    assert res.status_code == 200
    data = res.json()
    assert data["items"] == []
    assert data["total"] == 0


@pytest.mark.asyncio
async def test_03_existing_scheduled_classrooms_remain_visible_without_bbb(
    client: AsyncClient,
    db_session: AsyncSession,
    vc_api_fixture: dict[str, Any],
) -> None:
    """Scheduled classrooms in DB remain visible when BBB is not configured."""
    inst1 = vc_api_fixture["inst1"]
    teacher = vc_api_fixture["teacher_user"]
    teacher_hdr = vc_api_fixture["teacher_headers"]

    # Directly persist a scheduled classroom in DB
    classroom = VirtualClassroom(
        institution_id=inst1.id,
        host_user_id=teacher.id,
        title="Biología Celular: Mitosis y Meiosis",
        description="Clase teórica de ciclo celular",
        bbb_meeting_id=f"pevn-meeting-{uuid.uuid4().hex[:8]}",
        moderator_password_hash="mod123",
        attendee_password_hash="att123",
        status=VirtualClassroomStatus.SCHEDULED,
        is_recording_enabled=True,
        is_breakout_enabled=False,
        max_participants=40,
    )
    db_session.add(classroom)
    await db_session.flush()

    settings = get_settings()
    orig_provider = settings.MEETING_PROVIDER_TYPE
    orig_secret = settings.BBB_SHARED_SECRET
    settings.MEETING_PROVIDER_TYPE = "bbb"
    settings.BBB_SHARED_SECRET = ""

    try:
        res = await client.get("/api/v1/virtual-classrooms", headers=teacher_hdr)
        assert res.status_code == 200
        data = res.json()
        assert data["total"] >= 1
        found = next((c for c in data["items"] if c["id"] == str(classroom.id)), None)
        assert found is not None
        assert found["title"] == "Biología Celular: Mitosis y Meiosis"
        assert found["status"] == "SCHEDULED"
    finally:
        settings.MEETING_PROVIDER_TYPE = orig_provider
        settings.BBB_SHARED_SECRET = orig_secret


@pytest.mark.asyncio
async def test_04_create_scheduled_classroom_succeeds_without_bbb(
    client: AsyncClient,
    vc_api_fixture: dict[str, Any],
) -> None:
    """Creating / scheduling a virtual classroom succeeds even when BBB is unconfigured."""
    settings = get_settings()
    orig_provider = settings.MEETING_PROVIDER_TYPE
    orig_secret = settings.BBB_SHARED_SECRET
    settings.MEETING_PROVIDER_TYPE = "bbb"
    settings.BBB_SHARED_SECRET = ""

    try:
        teacher_hdr = vc_api_fixture["teacher_headers"]
        create_payload = {
            "title": "Química General: Estequiometría",
            "description": "Sesión programada para la próxima semana",
            "max_participants": 45,
            "is_recording_enabled": True,
        }
        res = await client.post(
            "/api/v1/virtual-classrooms",
            headers=teacher_hdr,
            json=create_payload,
        )
        assert res.status_code == 201
        data = res.json()
        assert data["title"] == "Química General: Estequiometría"
        assert data["status"] == "SCHEDULED"
    finally:
        settings.MEETING_PROVIDER_TYPE = orig_provider
        settings.BBB_SHARED_SECRET = orig_secret


@pytest.mark.asyncio
async def test_05_bbb_join_returns_controlled_bbb_not_configured_503(
    client: AsyncClient,
    db_session: AsyncSession,
    vc_api_fixture: dict[str, Any],
) -> None:
    """Attempting to join a live meeting when BBB is unconfigured returns HTTP 503 BBB_NOT_CONFIGURED."""
    inst1 = vc_api_fixture["inst1"]
    teacher = vc_api_fixture["teacher_user"]
    teacher_hdr = vc_api_fixture["teacher_headers"]

    classroom = VirtualClassroom(
        institution_id=inst1.id,
        host_user_id=teacher.id,
        title="Física Mecánica: Cinemática",
        bbb_meeting_id=f"pevn-meeting-{uuid.uuid4().hex[:8]}",
        moderator_password_hash="mod123",
        attendee_password_hash="att123",
        status=VirtualClassroomStatus.SCHEDULED,
        is_recording_enabled=True,
        is_breakout_enabled=False,
        max_participants=30,
    )
    db_session.add(classroom)
    await db_session.flush()

    settings = get_settings()
    orig_provider = settings.MEETING_PROVIDER_TYPE
    orig_secret = settings.BBB_SHARED_SECRET
    settings.MEETING_PROVIDER_TYPE = "bbb"
    settings.BBB_SHARED_SECRET = ""

    try:
        res = await client.post(
            f"/api/v1/virtual-classrooms/{classroom.id}/join",
            headers=teacher_hdr,
        )
        assert res.status_code == 503
        data = res.json()
        assert data["error"]["code"] == "BBB_NOT_CONFIGURED"
        assert "no se encuentra configurado" in data["error"]["message"].lower()
    finally:
        settings.MEETING_PROVIDER_TYPE = orig_provider
        settings.BBB_SHARED_SECRET = orig_secret


@pytest.mark.asyncio
async def test_06_bbb_launch_returns_controlled_bbb_not_configured_503(
    client: AsyncClient,
    db_session: AsyncSession,
    vc_api_fixture: dict[str, Any],
) -> None:
    """Attempting to launch a live meeting when BBB is unconfigured returns HTTP 503 BBB_NOT_CONFIGURED."""
    inst1 = vc_api_fixture["inst1"]
    teacher = vc_api_fixture["teacher_user"]
    teacher_hdr = vc_api_fixture["teacher_headers"]

    classroom = VirtualClassroom(
        institution_id=inst1.id,
        host_user_id=teacher.id,
        title="Lengua Castellana: Literatura Barroca",
        bbb_meeting_id=f"pevn-meeting-{uuid.uuid4().hex[:8]}",
        moderator_password_hash="mod123",
        attendee_password_hash="att123",
        status=VirtualClassroomStatus.SCHEDULED,
        is_recording_enabled=True,
        is_breakout_enabled=False,
        max_participants=30,
    )
    db_session.add(classroom)
    await db_session.flush()

    settings = get_settings()
    orig_provider = settings.MEETING_PROVIDER_TYPE
    orig_secret = settings.BBB_SHARED_SECRET
    settings.MEETING_PROVIDER_TYPE = "bbb"
    settings.BBB_SHARED_SECRET = ""

    try:
        res = await client.post(
            f"/api/v1/virtual-classrooms/{classroom.id}/launch",
            headers=teacher_hdr,
        )
        assert res.status_code == 503
        data = res.json()
        assert data["error"]["code"] == "BBB_NOT_CONFIGURED"
        assert "no se encuentra configurado" in data["error"]["message"].lower()
    finally:
        settings.MEETING_PROVIDER_TYPE = orig_provider
        settings.BBB_SHARED_SECRET = orig_secret


@pytest.mark.asyncio
async def test_07_provider_outage_returns_controlled_503(
    client: AsyncClient,
    db_session: AsyncSession,
    vc_api_fixture: dict[str, Any],
) -> None:
    """Provider connection timeout or network outage returns controlled HTTP 503 without unhandled 500."""
    inst1 = vc_api_fixture["inst1"]
    teacher = vc_api_fixture["teacher_user"]
    teacher_hdr = vc_api_fixture["teacher_headers"]

    classroom = VirtualClassroom(
        institution_id=inst1.id,
        host_user_id=teacher.id,
        title="Geometría Analítica",
        bbb_meeting_id=f"pevn-meeting-{uuid.uuid4().hex[:8]}",
        moderator_password_hash="mod123",
        attendee_password_hash="att123",
        status=VirtualClassroomStatus.SCHEDULED,
        is_recording_enabled=True,
        is_breakout_enabled=False,
        max_participants=30,
    )
    db_session.add(classroom)
    await db_session.flush()

    # Simulate network connection failure in provider
    with patch(
        "app.services.virtual_classroom_service.VirtualClassroomService.generate_join_url",
        side_effect=MeetingProviderConnectionError("Timeout de conexión al cluster BBB."),
    ):
        res = await client.post(
            f"/api/v1/virtual-classrooms/{classroom.id}/join",
            headers=teacher_hdr,
        )
        assert res.status_code == 503
        data = res.json()
        assert data["error"]["code"] == "MEETING_PROVIDER_CONNECTION_ERROR"
        assert "Timeout de conexión" in data["error"]["message"]


@pytest.mark.asyncio
async def test_08_database_failure_is_not_masked(
    client: AsyncClient,
    vc_api_fixture: dict[str, Any],
) -> None:
    """Database failures are not incorrectly converted into empty results."""
    from sqlalchemy.exc import OperationalError

    teacher_hdr = vc_api_fixture["teacher_headers"]

    with patch(
        "app.services.virtual_classroom_service.VirtualClassroomService.list_virtual_classrooms",
        side_effect=OperationalError("Database connection lost", params=None, orig=Exception("DB down")),
    ):
        try:
            res = await client.get("/api/v1/virtual-classrooms", headers=teacher_hdr)
            # Must return an error status (500), never a fake 200 with empty list
            assert res.status_code == 500
        except OperationalError:
            # Under direct ASGI transport, uncaught DB exceptions bubble rather than masking as 200
            pass


@pytest.mark.asyncio
async def test_09_unauthorized_users_remain_blocked(
    client: AsyncClient,
) -> None:
    """Unauthenticated and unauthorized requests remain strictly rejected."""
    # 401 Unauthenticated
    res = await client.get("/api/v1/virtual-classrooms")
    assert res.status_code == 401

    res_post = await client.post(
        "/api/v1/virtual-classrooms",
        json={"title": "Unauthorized Class"},
    )
    assert res_post.status_code == 401


@pytest.mark.asyncio
async def test_10_tenant_isolation_remains_enforced(
    client: AsyncClient,
    db_session: AsyncSession,
    vc_api_fixture: dict[str, Any],
) -> None:
    """Classrooms created in Institution 1 are never visible to users from Institution 2."""
    inst1 = vc_api_fixture["inst1"]
    teacher = vc_api_fixture["teacher_user"]
    tenant2_hdr = vc_api_fixture["tenant2_headers"]

    classroom = VirtualClassroom(
        institution_id=inst1.id,
        host_user_id=teacher.id,
        title="Clase Privada Tenant 1",
        bbb_meeting_id=f"pevn-meeting-{uuid.uuid4().hex[:8]}",
        moderator_password_hash="mod123",
        attendee_password_hash="att123",
        status=VirtualClassroomStatus.SCHEDULED,
        is_recording_enabled=True,
        is_breakout_enabled=False,
        max_participants=25,
    )
    db_session.add(classroom)
    await db_session.flush()

    # User from Tenant 2 lists classrooms: must NOT see Tenant 1's classroom
    res = await client.get("/api/v1/virtual-classrooms", headers=tenant2_hdr)
    assert res.status_code == 200
    data = res.json()
    item_ids = [c["id"] for c in data["items"]]
    assert str(classroom.id) not in item_ids


@pytest.mark.asyncio
async def test_11_get_provider_status_endpoint(
    client: AsyncClient,
    vc_api_fixture: dict[str, Any],
) -> None:
    """The /provider-status endpoint exposes current BBB infrastructure availability."""
    teacher_hdr = vc_api_fixture["teacher_headers"]
    res = await client.get("/api/v1/virtual-classrooms/provider-status", headers=teacher_hdr)
    assert res.status_code == 200
    data = res.json()
    assert "provider_configured" in data
    assert "provider_status" in data
    assert "message" in data
