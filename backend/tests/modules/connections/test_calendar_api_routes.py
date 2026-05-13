"""Tests for Calendar API route functions."""

import datetime
from types import SimpleNamespace
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest
from fastapi import HTTPException

from luana_core_connections.api.calendar import (
    book_meeting,
    create_booking_link,
    create_personalized_link,
    create_schedule,
    delete_schedule,
    disconnect,
    get_auth_url,
    get_slots,
    get_status,
    list_appointments,
    list_schedules,
    oauth_callback,
    update_schedule,
)
from luana_core_connections.api.calendar import (
    test_connection as cal_test_connection,
)
from luana_core_connections.api.dto.calendar import (
    BookMeetingRequest,
    CreateBookingLinkRequest,
)

TENANT_ID = uuid4()


def _user(tenant=None):
    u = SimpleNamespace(
        tenant_id=TENANT_ID,
        id=uuid4(),
        tenant=tenant,
    )
    return u


def _repo(**kwargs):
    repo = MagicMock()
    for k, v in kwargs.items():
        setattr(repo, k, v)
    return repo


def _conn(config=None, credentials=None):
    c = MagicMock()
    c.config = config or {"email": "user@example.com"}
    c.credentials = credentials or {"access_token": "tok", "refresh_token": "rt"}
    return c


def _mock_db():
    db = MagicMock()
    db.execute.return_value.scalars.return_value.first.return_value = None
    return db


# ---------------------------------------------------------------------------
# get_auth_url
# ---------------------------------------------------------------------------


class TestCalendarGetAuthUrl:
    @pytest.mark.asyncio
    async def test_returns_url_and_state(self):
        user = _user()
        with patch("luana_core_connections.api.calendar.GoogleCalendarAdapter.get_authorization_url") as mock_url:
            mock_url.return_value = ("https://accounts.google.com/auth", "state_abc")
            result = await get_auth_url(user, redirect_uri=None)
        assert "url" in result
        assert result["state"] == "state_abc"


# ---------------------------------------------------------------------------
# oauth_callback
# ---------------------------------------------------------------------------


class TestCalendarOAuthCallback:
    @pytest.mark.asyncio
    async def test_raises_400_on_exchange_failure(self):
        db = _mock_db()
        user = _user()
        repo = _repo()

        with patch("luana_core_connections.api.calendar.GoogleCalendarAdapter.exchange_code") as mock_ex:
            mock_ex.side_effect = Exception("bad code")
            with pytest.raises(HTTPException) as exc_info:
                await oauth_callback("bad_code", db, user, repo, redirect_uri=None)
        assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    async def test_saves_credentials_with_email(self):
        db = _mock_db()
        user = _user()
        repo = _repo(upsert=MagicMock())
        creds = {"access_token": "at", "refresh_token": "rt"}

        with (
            patch("luana_core_connections.api.calendar.GoogleCalendarAdapter.exchange_code", return_value=creds),
            patch("luana_core_connections.api.calendar.GoogleCalendarAdapter") as MockAdapter,
        ):
            mock_service = MagicMock()
            mock_service.calendars.return_value.get.return_value.execute.return_value = {"id": "user@gmail.com"}
            MockAdapter.return_value.get_service.return_value = mock_service
            result = await oauth_callback("good_code", db, user, repo, redirect_uri=None)

        assert result["status"] == "connected"
        assert result["email"] == "user@gmail.com"
        repo.upsert.assert_called_once()

    @pytest.mark.asyncio
    async def test_falls_back_to_unknown_email_on_error(self):
        db = _mock_db()
        user = _user()
        repo = _repo(upsert=MagicMock())
        creds = {"access_token": "at", "refresh_token": "rt"}

        with (
            patch("luana_core_connections.api.calendar.GoogleCalendarAdapter.exchange_code", return_value=creds),
            patch("luana_core_connections.api.calendar.GoogleCalendarAdapter") as MockAdapter,
        ):
            MockAdapter.return_value.get_service.side_effect = Exception("service error")
            result = await oauth_callback("good_code", db, user, repo, redirect_uri=None)

        assert result["status"] == "connected"
        assert result["email"] == "Unknown"


# ---------------------------------------------------------------------------
# get_status
# ---------------------------------------------------------------------------


class TestCalendarGetStatus:
    @pytest.mark.asyncio
    async def test_not_connected_when_no_connection(self):
        db = _mock_db()
        user = _user()
        repo = _repo(get_active=MagicMock(return_value=None))

        with (
            patch("luana_core_connections.api.calendar.get_booking_base_url", return_value="https://book.example.com"),
            patch("luana_core_connections.api.calendar.create_domain_lookup"),
        ):
            result = await get_status(db, user, repo)

        assert result.is_connected is False

    @pytest.mark.asyncio
    async def test_connected_returns_email(self):
        db = _mock_db()
        user = _user()
        conn = _conn(config={"email": "me@gmail.com"})
        repo = _repo(get_active=MagicMock(return_value=conn))

        with (
            patch("luana_core_connections.api.calendar.get_booking_base_url", return_value="https://book.example.com"),
            patch("luana_core_connections.api.calendar.create_domain_lookup"),
        ):
            result = await get_status(db, user, repo)

        assert result.is_connected is True
        assert result.email == "me@gmail.com"

    @pytest.mark.asyncio
    async def test_includes_booking_link_when_link_exists(self):
        db = _mock_db()
        link = MagicMock()
        link.token = "abc123"
        db.execute.return_value.scalars.return_value.first.return_value = link
        user = _user()
        repo = _repo(get_active=MagicMock(return_value=None))

        with (
            patch("luana_core_connections.api.calendar.get_booking_base_url", return_value="https://book.example.com"),
            patch("luana_core_connections.api.calendar.create_domain_lookup"),
        ):
            result = await get_status(db, user, repo)

        assert result.booking_link is not None
        assert "abc123" in result.booking_link


# ---------------------------------------------------------------------------
# create_booking_link
# ---------------------------------------------------------------------------


class TestCreateBookingLink:
    @pytest.mark.asyncio
    async def test_creates_and_returns_link(self):
        db = _mock_db()
        user = _user()
        link = MagicMock()
        link.token = "tok123"

        with (
            patch("luana_core_connections.api.calendar.LinkService") as MockLS,
            patch("luana_core_connections.api.calendar.get_booking_base_url", return_value="https://book.example.com"),
            patch("luana_core_connections.api.calendar.create_domain_lookup"),
        ):
            MockLS.return_value.create_link.return_value = link
            result = await create_booking_link(db, user)

        assert result["token"] == "tok123"
        assert "tok123" in result["url"]


# ---------------------------------------------------------------------------
# create_personalized_link
# ---------------------------------------------------------------------------


class TestCreatePersonalizedLink:
    @pytest.mark.asyncio
    async def test_raises_404_when_lead_not_found(self):
        db = _mock_db()
        user = _user()
        payload = CreateBookingLinkRequest(lead_id=str(uuid4()), event_slug="meeting", expiration_days=7)

        with (
            patch("luana_core_connections.api.calendar.verify_lead_exists", return_value=False),
            pytest.raises(HTTPException) as exc_info,
        ):
            await create_personalized_link(payload, db, user)
        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_creates_link_when_lead_exists(self):
        db = _mock_db()
        tenant = SimpleNamespace(slug="mytenant")
        user = _user(tenant=tenant)
        payload = CreateBookingLinkRequest(lead_id=str(uuid4()), event_slug="meeting", expiration_days=7)
        link_data = {"token": "plink123", "expires_at": datetime.datetime.now(datetime.UTC)}

        with (
            patch("luana_core_connections.api.calendar.verify_lead_exists", return_value=True),
            patch("luana_core_connections.api.calendar.create_personalized_booking_link", return_value=link_data),
            patch("luana_core_connections.api.calendar.get_booking_base_url", return_value="https://book.example.com"),
            patch("luana_core_connections.api.calendar.create_domain_lookup"),
        ):
            result = await create_personalized_link(payload, db, user)

        assert result["token"] == "plink123"


# ---------------------------------------------------------------------------
# disconnect
# ---------------------------------------------------------------------------


class TestCalendarDisconnect:
    @pytest.mark.asyncio
    async def test_deactivates_connection(self):
        user = _user()
        conn = _conn()
        repo = _repo(
            get_by_tenant_and_type=MagicMock(return_value=conn),
            deactivate=MagicMock(),
        )
        result = await disconnect(user, repo)
        repo.deactivate.assert_called_once_with(conn)
        assert result["status"] == "disconnected"

    @pytest.mark.asyncio
    async def test_returns_disconnected_when_no_connection(self):
        user = _user()
        repo = _repo(get_by_tenant_and_type=MagicMock(return_value=None))
        result = await disconnect(user, repo)
        assert result["status"] == "disconnected"


# ---------------------------------------------------------------------------
# test_connection
# ---------------------------------------------------------------------------


class TestCalendarTestConnection:
    @pytest.mark.asyncio
    async def test_raises_400_when_not_connected(self):
        user = _user()
        repo = _repo(get_active=MagicMock(return_value=None))

        with pytest.raises(HTTPException) as exc_info:
            await cal_test_connection(user, repo)
        assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    async def test_returns_ok_on_success(self):
        user = _user()
        conn = _conn()
        repo = _repo(get_active=MagicMock(return_value=conn))

        with patch("luana_core_connections.api.calendar.GoogleCalendarAdapter") as MockAdapter:
            MockAdapter.return_value.list_busy_periods.return_value = []
            result = await cal_test_connection(user, repo)

        assert result["status"] == "ok"

    @pytest.mark.asyncio
    async def test_returns_error_on_exception(self):
        user = _user()
        conn = _conn()
        repo = _repo(get_active=MagicMock(return_value=conn))

        with patch("luana_core_connections.api.calendar.GoogleCalendarAdapter") as MockAdapter:
            MockAdapter.return_value.list_busy_periods.side_effect = Exception("API error")
            result = await cal_test_connection(user, repo)

        assert result["status"] == "error"


# ---------------------------------------------------------------------------
# get_slots
# ---------------------------------------------------------------------------


class TestGetSlots:
    @pytest.mark.asyncio
    async def test_returns_available_slots(self):
        db = _mock_db()
        user = _user()
        start = datetime.date(2024, 1, 1)
        end = datetime.date(2024, 1, 7)

        with patch("luana_core_connections.api.calendar.get_availability_service") as mock_svc:
            mock_svc.return_value.get_available_slots.return_value = ["2024-01-01T09:00:00", "2024-01-01T10:00:00"]
            result = await get_slots(start, end, db, user, duration=30)

        assert len(result["slots"]) == 2


# ---------------------------------------------------------------------------
# book_meeting
# ---------------------------------------------------------------------------


class TestBookMeeting:
    @pytest.mark.asyncio
    async def test_books_and_returns_event_link(self):
        db = _mock_db()
        user = _user()
        payload = BookMeetingRequest(
            slot_time=datetime.datetime(2024, 1, 1, 9, 0, tzinfo=datetime.UTC),
            duration_minutes=30,
            lead_data={"name": "Test Lead", "email": "lead@example.com"},
        )

        with patch("luana_core_connections.api.calendar.get_availability_service") as mock_svc:
            mock_svc.return_value.book_meeting.return_value = {"htmlLink": "https://calendar.google.com/event/123"}
            result = await book_meeting(payload, db, user)

        assert result["status"] == "booked"
        assert result["event_link"] is not None

    @pytest.mark.asyncio
    async def test_raises_500_on_booking_error(self):
        db = _mock_db()
        user = _user()
        payload = BookMeetingRequest(
            slot_time=datetime.datetime(2024, 1, 1, 9, 0, tzinfo=datetime.UTC),
            duration_minutes=30,
            lead_data={},
        )

        with patch("luana_core_connections.api.calendar.get_availability_service") as mock_svc:
            mock_svc.return_value.book_meeting.side_effect = Exception("slot taken")
            with pytest.raises(HTTPException) as exc_info:
                await book_meeting(payload, db, user)
        assert exc_info.value.status_code == 500


# ---------------------------------------------------------------------------
# list_appointments
# ---------------------------------------------------------------------------


class TestListAppointments:
    @pytest.mark.asyncio
    async def test_returns_appointments_list(self):
        db = _mock_db()
        user = _user()
        start = datetime.date(2024, 1, 1)
        end = datetime.date(2024, 1, 7)
        events = [
            {
                "id": "evt_1",
                "summary": "Meeting",
                "start": {"dateTime": "2024-01-01T09:00:00Z"},
                "end": {"dateTime": "2024-01-01T09:30:00Z"},
                "hangoutLink": "https://meet.google.com/abc",
                "attendees": [{"email": "guest@example.com"}],
            }
        ]

        with patch("luana_core_connections.api.calendar.get_availability_service") as mock_svc:
            mock_svc.return_value.list_appointments.return_value = events
            result = await list_appointments(start, end, db, user)

        assert len(result) == 1
        assert result[0]["id"] == "evt_1"
        assert result[0]["attendees"] == ["guest@example.com"]


# ---------------------------------------------------------------------------
# Schedules endpoints
# ---------------------------------------------------------------------------


class TestScheduleEndpoints:
    @pytest.mark.asyncio
    async def test_list_schedules_returns_list(self):
        db = _mock_db()
        user = _user()

        with patch("luana_core_connections.api.calendar.get_availability_service") as mock_svc:
            mock_svc.return_value.list_schedules.return_value = [MagicMock()]
            result = await list_schedules(db, user)

        assert len(result) == 1

    @pytest.mark.asyncio
    async def test_create_schedule_returns_schedule(self):
        db = _mock_db()
        user = _user()
        schedule = MagicMock()

        with patch("luana_core_connections.api.calendar.get_availability_service") as mock_svc:
            mock_svc.return_value.create_schedule.return_value = schedule
            result = await create_schedule(schedule, db, user)

        assert result == schedule

    @pytest.mark.asyncio
    async def test_update_schedule_returns_updated(self):
        db = _mock_db()
        user = _user()
        update = MagicMock()
        updated = MagicMock()

        with patch("luana_core_connections.api.calendar.get_availability_service") as mock_svc:
            mock_svc.return_value.update_schedule.return_value = updated
            result = await update_schedule("sched_1", update, db, user)

        assert result == updated

    @pytest.mark.asyncio
    async def test_update_schedule_raises_404_when_not_found(self):
        db = _mock_db()
        user = _user()
        update = MagicMock()

        with patch("luana_core_connections.api.calendar.get_availability_service") as mock_svc:
            mock_svc.return_value.update_schedule.return_value = None
            with pytest.raises(HTTPException) as exc_info:
                await update_schedule("missing_id", update, db, user)
        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_schedule_returns_deleted(self):
        db = _mock_db()
        user = _user()

        with patch("luana_core_connections.api.calendar.get_availability_service") as mock_svc:
            mock_svc.return_value.delete_schedule.return_value = True
            result = await delete_schedule("sched_1", db, user)

        assert result["status"] == "deleted"

    @pytest.mark.asyncio
    async def test_delete_schedule_raises_404_when_not_found(self):
        db = _mock_db()
        user = _user()

        with patch("luana_core_connections.api.calendar.get_availability_service") as mock_svc:
            mock_svc.return_value.delete_schedule.return_value = False
            with pytest.raises(HTTPException) as exc_info:
                await delete_schedule("missing_id", db, user)
        assert exc_info.value.status_code == 404
