import pytest

from app.models import Notification, NotificationStatus, Role
from tests.conftest import log_in


@pytest.fixture
def customer(make_user):
    return make_user(Role.CUSTOMER, phone="+919000000030")


@pytest.fixture
def other_customer(make_user):
    return make_user(Role.CUSTOMER, phone="+919000000031", email=None)


def add_notification(db_session, user_id, message="Hello", status=NotificationStatus.UNREAD):
    notification = Notification(user_id=user_id, message=message, status=status)
    db_session.add(notification)
    db_session.commit()
    return notification


class TestListNotifications:
    def test_lists_only_the_logged_in_user_s_notifications_newest_first(self, client, db_session, customer, other_customer):
        add_notification(db_session, customer.id, message="First")
        add_notification(db_session, customer.id, message="Second")
        add_notification(db_session, other_customer.id, message="Not mine")

        log_in(client, customer.email)
        response = client.get("/api/notifications")

        assert response.status_code == 200
        assert [n["message"] for n in response.json()] == ["Second", "First"]

    def test_anonymous_visitor_is_rejected(self, client):
        assert client.get("/api/notifications").status_code == 401


class TestUnreadCount:
    def test_counts_only_unread_notifications(self, client, db_session, customer):
        add_notification(db_session, customer.id, status=NotificationStatus.UNREAD)
        add_notification(db_session, customer.id, status=NotificationStatus.UNREAD)
        add_notification(db_session, customer.id, status=NotificationStatus.READ)

        log_in(client, customer.email)
        response = client.get("/api/notifications/unread-count")

        assert response.json() == {"count": 2}

    def test_zero_when_there_are_none(self, client, customer):
        log_in(client, customer.email)

        assert client.get("/api/notifications/unread-count").json() == {"count": 0}


class TestMarkRead:
    def test_marks_a_single_notification_read(self, client, db_session, customer):
        notification = add_notification(db_session, customer.id)

        log_in(client, customer.email)
        response = client.patch(f"/api/notifications/{notification.id}/read")

        assert response.status_code == 200
        assert response.json()["status"] == "read"
        assert client.get("/api/notifications/unread-count").json() == {"count": 0}

    def test_cannot_mark_someone_else_s_notification_read(self, client, db_session, customer, other_customer):
        notification = add_notification(db_session, other_customer.id)

        log_in(client, customer.email)
        response = client.patch(f"/api/notifications/{notification.id}/read")

        assert response.status_code == 404

    def test_marking_an_unknown_notification_is_404(self, client, customer):
        log_in(client, customer.email)

        assert client.patch("/api/notifications/999999/read").status_code == 404


class TestMarkAllRead:
    def test_marks_every_unread_notification_read(self, client, db_session, customer):
        add_notification(db_session, customer.id)
        add_notification(db_session, customer.id)

        log_in(client, customer.email)
        response = client.post("/api/notifications/read-all")

        assert response.status_code == 204
        assert client.get("/api/notifications/unread-count").json() == {"count": 0}

    def test_does_not_touch_another_user_s_notifications(self, client, db_session, customer, other_customer):
        theirs = add_notification(db_session, other_customer.id)

        log_in(client, customer.email)
        client.post("/api/notifications/read-all")

        db_session.refresh(theirs)
        assert theirs.status == NotificationStatus.UNREAD


class TestNotificationsAreCreatedByAssignmentAndStatusChange:
    """Integration check that the writer (app.routes.service_requests) and reader (this module)
    actually agree on shape — not a re-test of assignment/status logic itself."""

    def test_assigning_a_technician_creates_notifications_visible_through_this_api(self, client, make_user, customer):
        technician = make_user(Role.TECHNICIAN)
        admin = make_user(Role.ADMIN)
        log_in(client, customer.email)
        request_id = client.post(
            "/api/requests", json={"description": "Noisy unit", "address": "12 Anna Salai, Chennai"}
        ).json()["id"]

        log_in(client, admin.email)
        client.patch(f"/api/requests/{request_id}", json={"technician_id": technician.technician.id})

        log_in(client, technician.email)
        messages = [n["message"] for n in client.get("/api/notifications").json()]
        assert any("assigned" in m for m in messages)
