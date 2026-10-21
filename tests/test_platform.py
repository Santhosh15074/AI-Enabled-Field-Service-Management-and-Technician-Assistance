"""The config portal's API (app.routes.platform): Sollu operators configuring shops."""

import pytest
from sqlalchemy import func, select

from app.accounts import create_operator
from app.models import Role, ServiceReport, ServiceRequest, Shop, User
from tests.conftest import DEFAULT_SHOP_ID, PASSWORD, log_in

NEW_SHOP = {
    "name": "Ravi Aircon Services",
    "slug": "ravi-aircon",
    "plan": "starter",
    "contact_phone": "+91 98765 43210",
    "owner_name": "Ravi Kumar",
    "owner_email": "ravi@example.com",
    "owner_password": PASSWORD,
}


@pytest.fixture
def operator(db_session):
    return create_operator(db_session, name="Santhosh", email="ops@sollu.example", password=PASSWORD)


@pytest.fixture
def ops(client, operator):
    """The test client, logged in as an operator."""
    response = client.post("/api/platform/auth/login", json={"email": operator.email, "password": PASSWORD})
    assert response.status_code == 200
    return client


def create(ops, **overrides):
    return ops.post("/api/platform/shops", json={**NEW_SHOP, **overrides})


class TestOperatorLogin:
    def test_log_in_see_yourself_and_log_out(self, ops, operator):
        assert ops.get("/api/platform/auth/me").json()["email"] == operator.email

        assert ops.post("/api/platform/auth/logout").status_code == 204
        assert ops.get("/api/platform/auth/me").status_code == 401

    def test_wrong_password(self, client, operator):
        response = client.post("/api/platform/auth/login", json={"email": operator.email, "password": "wrong-password"})

        assert response.status_code == 401

    def test_every_endpoint_needs_an_operator(self, client):
        assert client.get("/api/platform/shops").status_code == 401

    def test_a_shop_owner_is_not_an_operator(self, client, make_user):
        owner = make_user(Role.ADMIN)
        log_in(client, owner.email)

        assert client.get("/api/platform/shops").status_code == 401

    def test_an_operator_is_not_a_shop_user(self, ops):
        assert ops.get("/api/auth/me").status_code == 401

    def test_deactivated_operator_is_logged_out(self, ops, operator, db_session):
        operator.is_active = False
        db_session.commit()

        assert ops.get("/api/platform/auth/me").status_code == 401


class TestCreateShop:
    def test_creates_the_shop_and_an_owner_who_can_log_in(self, ops, client):
        response = create(ops)

        assert response.status_code == 201
        shop = response.json()
        assert (shop["slug"], shop["plan"], shop["technician_limit"], shop["monthly_report_limit"]) == ("ravi-aircon", "starter", 10, 750)
        assert shop["contact_phone"] == "+919876543210"
        assert [(s["name"], s["role"]) for s in shop["staff"]] == [("Ravi Kumar", "admin")]

        assert log_in(client, "ravi@example.com").json()["shop_name"] == "Ravi Aircon Services"

    def test_the_plan_sets_the_limits(self, ops):
        shop = create(ops, plan="growth").json()

        assert (shop["technician_limit"], shop["monthly_report_limit"]) == (25, 2000)

    @pytest.mark.parametrize(
        "overrides",
        [
            {"slug": "default"},  # taken
            {"slug": "Not A Slug"},
            {"plan": "platinum"},
            {"owner_email": "not-an-email"},
            {"owner_password": "short"},
            {"contact_phone": "call me"},
        ],
    )
    def test_a_rejected_shop_or_owner_leaves_nothing_behind(self, ops, db_session, overrides):
        response = create(ops, **overrides)

        assert response.status_code == 400
        assert db_session.scalar(select(func.count(Shop.id))) == 1  # just the default shop

    def test_owner_email_already_in_use_leaves_no_shop(self, ops, db_session, make_user):
        make_user(Role.ADMIN, email="ravi@example.com")

        assert create(ops).status_code == 400
        assert db_session.scalar(select(Shop).where(Shop.slug == "ravi-aircon")) is None


class TestListShops:
    def test_counts(self, ops, db_session, make_user):
        make_user(Role.TECHNICIAN)
        customer = make_user(Role.CUSTOMER, email=None)
        request = ServiceRequest(customer_id=customer.customer.id, description="Not cooling.")
        db_session.add(request)
        db_session.flush()
        db_session.add(ServiceReport(request_id=request.id, report_text="Cleaned the filter."))
        db_session.commit()

        (shop,) = ops.get("/api/platform/shops").json()

        assert (shop["slug"], shop["active_technicians"], shop["customers"], shop["reports_this_month"]) == ("default", 1, 1, 1)


class TestUpdateShop:
    def test_changing_the_plan_resets_the_limits(self, ops):
        shop_id = create(ops).json()["id"]

        shop = ops.patch(f"/api/platform/shops/{shop_id}", json={"plan": "pro"}).json()

        assert (shop["plan"], shop["technician_limit"], shop["monthly_report_limit"]) == ("pro", 50, 4000)

    def test_limits_can_be_set_for_one_shop(self, ops):
        shop_id = create(ops).json()["id"]

        shop = ops.patch(f"/api/platform/shops/{shop_id}", json={"plan": "growth", "technician_limit": 12}).json()

        assert (shop["technician_limit"], shop["monthly_report_limit"]) == (12, 2000)

    def test_renaming_and_a_new_slug(self, ops, client):
        shop_id = create(ops).json()["id"]

        shop = ops.patch(f"/api/platform/shops/{shop_id}", json={"name": "Ravi Cooling", "slug": "ravi-cooling"}).json()

        assert (shop["name"], shop["slug"]) == ("Ravi Cooling", "ravi-cooling")
        assert client.get("/api/shops/ravi-aircon").status_code == 404
        assert client.get("/api/shops/ravi-cooling").json()["name"] == "Ravi Cooling"

    def test_a_shop_may_keep_its_own_slug_but_not_take_another(self, ops):
        shop_id = create(ops).json()["id"]

        assert ops.patch(f"/api/platform/shops/{shop_id}", json={"slug": "ravi-aircon"}).status_code == 200
        assert ops.patch(f"/api/platform/shops/{shop_id}", json={"slug": "default"}).status_code == 400

    def test_clearing_the_contact_phone(self, ops):
        shop_id = create(ops).json()["id"]

        assert ops.patch(f"/api/platform/shops/{shop_id}", json={"contact_phone": ""}).json()["contact_phone"] is None

    def test_a_deactivated_shop_is_locked_out(self, ops, client, make_user):
        owner = make_user(Role.ADMIN)
        log_in(client, owner.email)  # a shop session that's open when the shop is switched off

        ops.patch(f"/api/platform/shops/{DEFAULT_SHOP_ID}", json={"is_active": False})

        assert client.get("/api/auth/me").status_code == 401
        assert log_in(client, owner.email).status_code == 401
        assert client.get("/api/shops/default").status_code == 404
        register = client.post(
            "/api/auth/register", json={"shop": "default", "name": "Priya", "phone": "+919876543210", "password": PASSWORD}
        )
        assert register.status_code == 400

    def test_unknown_shop(self, ops):
        assert ops.patch("/api/platform/shops/999", json={"name": "X"}).status_code == 404


class TestStaff:
    def test_adding_an_owner_and_a_technician(self, ops):
        shop_id = create(ops).json()["id"]

        ops.post(f"/api/platform/shops/{shop_id}/staff", json={"name": "Office", "email": "office@example.com", "password": PASSWORD, "role": "admin"})
        shop = ops.post(
            f"/api/platform/shops/{shop_id}/staff",
            json={"name": "Murugan", "email": "murugan@example.com", "password": PASSWORD, "role": "technician", "skill_area": "HVAC"},
        ).json()

        assert {(s["name"], s["role"]) for s in shop["staff"]} == {("Ravi Kumar", "admin"), ("Office", "admin"), ("Murugan", "technician")}

    def test_customers_cannot_be_added_here(self, ops):
        response = ops.post(
            f"/api/platform/shops/{DEFAULT_SHOP_ID}/staff", json={"name": "P", "email": "p@example.com", "password": PASSWORD, "role": "customer"}
        )

        assert response.status_code == 400

    def test_reset_password(self, ops, client, make_user):
        technician = make_user(Role.TECHNICIAN)

        assert ops.post(f"/api/platform/users/{technician.id}/password", json={"password": "a-new-password"}).status_code == 204

        assert log_in(client, technician.email).status_code == 401
        assert log_in(client, technician.email, "a-new-password").status_code == 200

    def test_cannot_deactivate_the_last_active_owner(self, ops, make_user):
        owner = make_user(Role.ADMIN)

        response = ops.patch(f"/api/platform/users/{owner.id}/active", json={"is_active": False})

        assert response.status_code == 400
        assert "at least one active owner" in response.json()["detail"]


class TestTechnicianLimit:
    @pytest.fixture
    def full_shop(self, ops, make_user):
        """The default shop, limited to one technician, who already exists."""
        ops.patch(f"/api/platform/shops/{DEFAULT_SHOP_ID}", json={"technician_limit": 1})
        return make_user(Role.TECHNICIAN)

    def test_operator_cannot_add_past_the_limit(self, ops, full_shop):
        response = ops.post(
            f"/api/platform/shops/{DEFAULT_SHOP_ID}/staff",
            json={"name": "Two", "email": "two@example.com", "password": PASSWORD, "role": "technician"},
        )

        assert response.status_code == 400
        assert "allows 1 active technicians" in response.json()["detail"]

    def test_owner_cannot_add_past_the_limit(self, client, full_shop, make_user):
        owner = make_user(Role.ADMIN)
        log_in(client, owner.email)

        response = client.post(
            "/api/users", json={"name": "Two", "email": "two@example.com", "password": PASSWORD, "role": "technician"}
        )

        assert response.status_code == 400

    def test_deactivating_frees_a_place_and_reactivating_takes_it(self, ops, client, db_session, full_shop, make_user):
        owner = make_user(Role.ADMIN)
        log_in(client, owner.email)
        client.patch(f"/api/users/{full_shop.id}/active", json={"is_active": False})
        client.post("/api/users", json={"name": "Two", "email": "two@example.com", "password": PASSWORD, "role": "technician"})

        assert client.patch(f"/api/users/{full_shop.id}/active", json={"is_active": True}).status_code == 400
        assert ops.patch(f"/api/platform/users/{full_shop.id}/active", json={"is_active": True}).status_code == 400
        db_session.expire_all()
        assert db_session.get(User, full_shop.id).is_active is False

    def test_owners_do_not_count(self, ops, full_shop):
        response = ops.post(
            f"/api/platform/shops/{DEFAULT_SHOP_ID}/staff",
            json={"name": "Office", "email": "office@example.com", "password": PASSWORD, "role": "admin"},
        )

        assert response.status_code == 201
