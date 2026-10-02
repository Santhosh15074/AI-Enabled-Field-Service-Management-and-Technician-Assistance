import pytest
from sqlalchemy import select

from app.models import Customer, Role
from tests.conftest import PASSWORD, log_in

OVERVIEWS = {
    Role.ADMIN: "/api/overview/admin",
    Role.CUSTOMER: "/api/overview/customer",
    Role.TECHNICIAN: "/api/overview/technician",
}


class TestNoSelfSignUp:
    """There is no public account creation: every account is provisioned by an admin."""

    def test_register_endpoint_does_not_exist(self, client):
        response = client.post(
            "/api/auth/register",
            json={"name": "Priya", "email": "priya@example.com", "password": PASSWORD},
        )

        # 404 normally; 405 if frontend/dist is built and its catch-all route claims the path.
        assert response.status_code in (404, 405)


class TestLogin:
    @pytest.mark.parametrize("role", list(Role))
    def test_each_role_can_log_in_and_see_its_own_overview(self, client, make_user, role):
        user = make_user(role)

        response = log_in(client, user.email)

        assert response.status_code == 200
        assert response.json()["role"] == role
        assert client.get("/api/auth/me").json()["email"] == user.email
        assert client.get(OVERVIEWS[role]).status_code == 200

    def test_wrong_password_and_unknown_email_give_the_same_error(self, client, make_user):
        make_user(Role.CUSTOMER)

        wrong_password = log_in(client, "customer@example.com", "wrong-password")
        unknown_email = log_in(client, "nobody@example.com")

        assert wrong_password.status_code == unknown_email.status_code == 401
        assert wrong_password.json() == unknown_email.json()

    def test_inactive_user_cannot_log_in(self, client, make_user, db_session):
        user = make_user(Role.TECHNICIAN)
        user.is_active = False
        db_session.commit()

        assert log_in(client, user.email).status_code == 401

    def test_deactivating_a_logged_in_user_ends_their_session(self, client, make_user, db_session):
        user = make_user(Role.TECHNICIAN)
        log_in(client, user.email)
        user.is_active = False
        db_session.commit()

        assert client.get("/api/auth/me").status_code == 401


class TestRoleChecks:
    @pytest.mark.parametrize("path", [*OVERVIEWS.values(), "/api/auth/me"])
    def test_anonymous_visitor_is_rejected(self, client, path):
        assert client.get(path).status_code == 401

    @pytest.mark.parametrize("role", list(Role))
    def test_other_roles_overviews_are_forbidden(self, client, make_user, role):
        log_in(client, make_user(role).email)

        for other_role, path in OVERVIEWS.items():
            if other_role != role:
                assert client.get(path).status_code == 403


class TestLogout:
    def test_logout_ends_session(self, client, make_user):
        log_in(client, make_user(Role.ADMIN).email)

        assert client.post("/api/auth/logout").status_code == 204
        assert client.get("/api/overview/admin").status_code == 401

    def test_api_responses_are_never_cached(self, client, make_user):
        log_in(client, make_user(Role.ADMIN).email)

        assert client.get("/api/auth/me").headers["cache-control"] == "no-store"


class TestOverview:
    def test_admin_counts_accounts(self, client, make_user):
        make_user(Role.CUSTOMER)
        make_user(Role.TECHNICIAN)
        log_in(client, make_user(Role.ADMIN).email)

        assert client.get("/api/overview/admin").json() == {
            "customers": 1,
            "technicians": 1,
            "open_requests": 0,
            "critical_equipment": 0,
        }


class TestCascadeDelete:
    def test_deleting_a_user_deletes_their_customer_profile(self, make_user, db_session):
        user = make_user(Role.CUSTOMER)

        db_session.delete(user)
        db_session.commit()

        assert db_session.scalar(select(Customer)) is None
