import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.accounts import AccountError, create_user
from app.models import Customer, Role, User
from app.routes.auth import _conflicting_field
from tests.conftest import PASSWORD, log_in

OVERVIEWS = {
    Role.ADMIN: "/api/overview/admin",
    Role.CUSTOMER: "/api/overview/customer",
    Role.TECHNICIAN: "/api/overview/technician",
}


def register(client, **overrides):
    data = {
        "name": "Priya",
        "phone": "+91 98765 43210",
        "password": PASSWORD,
        "email": "priya@example.com",
    }
    data.update(overrides)
    return client.post("/api/auth/register", json=data)


class TestCustomerSelfRegistration:
    """The customer portal's sign-up. Staff (admin, technician) accounts have no such endpoint."""

    def test_creates_customer_with_profile_and_hashed_password(self, client, db_session):
        response = register(client)

        assert response.status_code == 201
        assert response.json()["role"] == "customer"
        assert "password_hash" not in response.json()
        user = db_session.scalar(select(User).where(User.email == "priya@example.com"))
        assert user.password_hash != PASSWORD
        assert user.password_hash.startswith("$2b$")
        # Spaces are stripped, so the same number typed differently still matches at login.
        assert user.customer.phone == "+919876543210"

    def test_email_is_optional(self, client, db_session):
        response = register(client, email=None)

        assert response.status_code == 201
        assert response.json()["email"] is None
        user = db_session.scalar(select(User).where(User.customer.has(phone="+919876543210")))
        assert user is not None

    def test_phone_is_mandatory(self, client, db_session):
        response = register(client, phone="   ")

        assert response.status_code == 400
        assert "Enter a phone number" in response.json()["detail"]
        assert db_session.scalar(select(User)) is None

    def test_phone_field_cannot_be_omitted(self, client):
        # phone has no default in RegisterIn, so FastAPI rejects a missing field before
        # create_user's own, friendlier validation ever runs.
        response = client.post("/api/auth/register", json={"name": "Priya", "password": PASSWORD})

        assert response.status_code == 422

    def test_phone_is_unique_regardless_of_formatting(self, client):
        register(client)
        response = register(client, email="other@example.com", phone="+91-98765-43210")

        assert response.status_code == 400
        assert "already exists" in response.json()["detail"]

    def test_email_is_case_insensitive_and_unique(self, client):
        register(client)
        response = register(client, phone="+91 11111 11111", email="  PRIYA@Example.com ")

        assert response.status_code == 400
        assert "already exists" in response.json()["detail"]

    @pytest.mark.parametrize(
        ("overrides", "message"),
        [
            ({"password": "short"}, "at least 8"),
            ({"email": "not-an-email"}, "valid email"),
            ({"name": "   "}, "Enter your name"),
            ({"phone": "call me"}, "valid phone"),
        ],
    )
    def test_rejects_invalid_input(self, client, db_session, overrides, message):
        response = register(client, **overrides)

        assert response.status_code == 400
        assert message in response.json()["detail"]
        assert db_session.scalar(select(User)) is None

    def test_cannot_request_another_role(self, client, db_session):
        # RegisterIn has no role field at all, so a client can't ask for anything but customer.
        register(client, role="admin")

        assert db_session.scalar(select(User)).role == Role.CUSTOMER

    def test_registering_does_not_log_in(self, client):
        register(client)

        assert client.get("/api/auth/me").status_code == 401


class TestConflictingField:
    """The message shown when two sign-ups race each other: see register()'s except IntegrityError."""

    @pytest.mark.parametrize(
        ("driver_message", "expected"),
        [
            ("UNIQUE constraint failed: customers.phone", "phone number"),
            ('duplicate key value violates unique constraint "ix_customers_phone"', "phone number"),
            ("UNIQUE constraint failed: users.email", "email"),
            ('duplicate key value violates unique constraint "ix_users_email"', "email"),
            ("some other constraint entirely", "phone number or email"),
        ],
    )
    def test_identifies_the_conflicting_column(self, driver_message, expected):
        error = IntegrityError("INSERT ...", {}, Exception(driver_message))

        assert _conflicting_field(error) == expected


class TestCreateUser:
    """Direct checks on app.accounts.create_user, below the HTTP layer: the rules differ by
    role, and only the customer portal's registration endpoint is reachable over the API."""

    def test_staff_requires_an_email(self, db_session):
        with pytest.raises(AccountError, match="email"):
            create_user(db_session, name="Ravi", password=PASSWORD, role=Role.TECHNICIAN)

    def test_customer_requires_a_phone(self, db_session):
        with pytest.raises(AccountError, match="phone"):
            create_user(db_session, name="Priya", password=PASSWORD, role=Role.CUSTOMER)

    def test_customer_can_skip_email(self, db_session):
        user = create_user(db_session, name="Priya", password=PASSWORD, role=Role.CUSTOMER, phone="+919876543210")

        assert user.email is None
        assert user.customer.phone == "+919876543210"


class TestLogin:
    @pytest.mark.parametrize("role", list(Role))
    def test_each_role_can_log_in_and_see_its_own_overview(self, client, make_user, role):
        user = make_user(role)

        response = log_in(client, user.email)

        assert response.status_code == 200
        assert response.json()["role"] == role
        assert client.get("/api/auth/me").json()["email"] == user.email
        assert client.get(OVERVIEWS[role]).status_code == 200

    def test_address_is_null_for_staff_and_for_a_customer_with_none_on_file(self, client, make_user):
        for role in Role:
            log_in(client, make_user(role, email=f"{role.value}2@example.com").email)
            assert client.get("/api/auth/me").json()["address"] is None

    def test_customer_address_appears_once_set(self, client, make_user, db_session):
        user = make_user(Role.CUSTOMER)
        user.customer.address = "12 Anna Salai, Chennai"
        db_session.commit()

        log_in(client, user.email)

        assert client.get("/api/auth/me").json()["address"] == "12 Anna Salai, Chennai"

    def test_customer_can_log_in_by_phone_formatted_differently_than_stored(self, client, make_user):
        make_user(Role.CUSTOMER, phone="+91 98765 00000")

        response = log_in(client, "+91-98765-00000")

        assert response.status_code == 200
        assert response.json()["role"] == "customer"

    def test_customer_with_no_email_can_only_log_in_by_phone(self, client, make_user):
        user = make_user(Role.CUSTOMER, email=None, phone="+919876500001")

        assert log_in(client, user.customer.phone).status_code == 200

    def test_wrong_password_and_unknown_identifier_give_the_same_error(self, client, make_user):
        make_user(Role.CUSTOMER)

        wrong_password = log_in(client, "customer@example.com", "wrong-password")
        unknown_identifier = log_in(client, "nobody@example.com")

        assert wrong_password.status_code == unknown_identifier.status_code == 401
        assert wrong_password.json() == unknown_identifier.json()

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
