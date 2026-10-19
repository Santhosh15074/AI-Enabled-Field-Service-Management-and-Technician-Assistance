import pytest
from sqlalchemy import select

from app.models import Role, User
from tests.conftest import PASSWORD, log_in


@pytest.fixture
def admin(make_user):
    return make_user(Role.ADMIN)


@pytest.fixture
def technician(make_user):
    return make_user(Role.TECHNICIAN)


@pytest.fixture
def customer(make_user):
    return make_user(Role.CUSTOMER, phone="+919000000020")


STAFF_PAYLOAD = {"name": "New Tech", "email": "newtech@example.com", "password": PASSWORD, "role": "technician"}


class TestListUsers:
    def test_admin_sees_every_user_with_role_specific_details(self, client, admin, technician, customer):
        log_in(client, admin.email)

        response = client.get("/api/users")

        assert response.status_code == 200
        by_role = {row["role"]: row for row in response.json()}
        assert by_role["technician"]["skill_area"] is None
        assert by_role["customer"]["phone"] == customer.customer.phone
        assert by_role["customer"]["email"] == customer.email

    def test_only_admins_can_list_users(self, client, technician):
        log_in(client, technician.email)

        assert client.get("/api/users").status_code == 403


class TestCreateStaffUser:
    def test_admin_can_create_a_technician(self, client, db_session, admin):
        log_in(client, admin.email)

        response = client.post("/api/users", json={**STAFF_PAYLOAD, "skill_area": "Electrical"})

        assert response.status_code == 201
        assert response.json()["role"] == "technician"
        assert response.json()["skill_area"] == "Electrical"
        user = db_session.scalar(select(User).where(User.email == "newtech@example.com"))
        assert user.password_hash.startswith("$2b$")

    def test_admin_can_create_another_admin(self, client, admin):
        log_in(client, admin.email)

        response = client.post("/api/users", json={**STAFF_PAYLOAD, "role": "admin", "email": "newadmin@example.com"})

        assert response.status_code == 201
        assert response.json()["role"] == "admin"

    def test_cannot_create_a_customer_through_this_endpoint(self, client, admin):
        log_in(client, admin.email)

        response = client.post("/api/users", json={**STAFF_PAYLOAD, "role": "customer"})

        assert response.status_code == 400

    def test_rejects_a_duplicate_email(self, client, admin, technician):
        log_in(client, admin.email)

        response = client.post("/api/users", json={**STAFF_PAYLOAD, "email": technician.email})

        assert response.status_code == 400
        assert "already exists" in response.json()["detail"]

    def test_only_admins_can_create_staff(self, client, technician):
        log_in(client, technician.email)

        assert client.post("/api/users", json=STAFF_PAYLOAD).status_code == 403

    def test_rejects_a_weak_password(self, client, admin):
        log_in(client, admin.email)

        response = client.post("/api/users", json={**STAFF_PAYLOAD, "password": "short"})

        assert response.status_code == 400

    def test_rejects_an_invalid_email(self, client, admin):
        log_in(client, admin.email)

        response = client.post("/api/users", json={**STAFF_PAYLOAD, "email": "not-an-email"})

        assert response.status_code == 400
        assert "valid email" in response.json()["detail"]


class TestSetActive:
    def test_admin_can_deactivate_a_technician(self, client, db_session, admin, technician):
        log_in(client, admin.email)

        response = client.patch(f"/api/users/{technician.id}/active", json={"is_active": False})

        assert response.status_code == 200
        assert response.json()["is_active"] is False
        db_session.refresh(technician)
        assert technician.is_active is False

    def test_admin_can_reactivate(self, client, admin, technician):
        log_in(client, admin.email)
        client.patch(f"/api/users/{technician.id}/active", json={"is_active": False})

        response = client.patch(f"/api/users/{technician.id}/active", json={"is_active": True})

        assert response.json()["is_active"] is True

    def test_an_admin_cannot_deactivate_themselves(self, client, admin):
        log_in(client, admin.email)

        response = client.patch(f"/api/users/{admin.id}/active", json={"is_active": False})

        assert response.status_code == 400

    def test_a_deactivated_technician_can_no_longer_log_in(self, client, admin, technician):
        log_in(client, admin.email)
        client.patch(f"/api/users/{technician.id}/active", json={"is_active": False})

        assert log_in(client, technician.email).status_code == 401

    def test_only_admins_can_set_active_state(self, client, technician, customer):
        log_in(client, technician.email)

        assert client.patch(f"/api/users/{customer.id}/active", json={"is_active": False}).status_code == 403

    def test_setting_active_on_an_unknown_user_is_404(self, client, admin):
        log_in(client, admin.email)

        assert client.patch("/api/users/999999/active", json={"is_active": False}).status_code == 404
