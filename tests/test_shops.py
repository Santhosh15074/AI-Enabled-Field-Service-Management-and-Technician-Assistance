"""Each shop sees only its own people, equipment and requests — see app.shops.

Every test has two shops: the default one (where make_user puts people unless told otherwise)
and "Other Shop". Records from the other shop must be invisible: missing from lists, and a
404 (never a 403) when asked for by id.
"""

import pytest
from sqlalchemy import select

from app.models import Equipment, KnowledgeBaseEntry, PredictionLog, Role, ServiceRequest, User
from app.shops import ShopError, create_shop
from tests.conftest import DEFAULT_SHOP_ID, DEFAULT_SHOP_SLUG, PASSWORD, log_in


@pytest.fixture
def mine(make_user, db_session):
    """The default shop: an owner, a technician, and a customer with equipment and a request."""
    admin = make_user(Role.ADMIN, email="owner@mine.example")
    technician = make_user(Role.TECHNICIAN, email="tech@mine.example", name="My Technician")
    customer = make_user(Role.CUSTOMER, email=None, name="My Customer", phone="+919000000001")
    return _with_job(db_session, admin, technician, customer)


@pytest.fixture
def theirs(make_user, make_shop, db_session):
    shop = make_shop()
    admin = make_user(Role.ADMIN, email="owner@theirs.example", shop_id=shop.id)
    technician = make_user(Role.TECHNICIAN, email="tech@theirs.example", name="Their Technician", shop_id=shop.id)
    customer = make_user(Role.CUSTOMER, email=None, name="Their Customer", phone="+919000000002", shop_id=shop.id)
    return _with_job(db_session, admin, technician, customer)


def _with_job(db_session, admin, technician, customer):
    equipment = Equipment(customer_id=customer.customer.id, name=f"{customer.name}'s AC", type="Split AC")
    db_session.add(equipment)
    db_session.flush()
    request = ServiceRequest(
        customer_id=customer.customer.id,
        equipment_id=equipment.id,
        technician_id=technician.technician.id,
        description=f"{customer.name}'s AC isn't cooling.",
    )
    db_session.add(request)
    db_session.add(PredictionLog(equipment_id=equipment.id, risk_score=0.9, risk_level="critical"))
    db_session.commit()
    return type("Shop", (), dict(admin=admin, technician=technician, customer=customer, equipment=equipment, request=request))


class TestListsOnlyShowYourShop:
    def test_requests(self, client, mine, theirs):
        log_in(client, mine.admin.email)

        assert [r["id"] for r in client.get("/api/requests").json()] == [mine.request.id]

    def test_users(self, client, mine, theirs):
        log_in(client, mine.admin.email)

        names = {user["name"] for user in client.get("/api/users").json()}

        assert "Their Technician" not in names and "Their Customer" not in names
        assert {"My Technician", "My Customer"} <= names

    def test_technicians_and_customers_to_pick_from(self, client, mine, theirs):
        log_in(client, mine.admin.email)

        assert [t["name"] for t in client.get("/api/requests/technicians").json()] == ["My Technician"]
        assert [c["name"] for c in client.get("/api/requests/customers").json()] == ["My Customer"]

    def test_equipment(self, client, mine, theirs):
        log_in(client, mine.admin.email)

        assert [e["id"] for e in client.get("/api/equipment/all").json()] == [mine.equipment.id]

    def test_overview_counts(self, client, mine, theirs):
        log_in(client, mine.admin.email)

        overview = client.get("/api/overview/admin").json()

        assert overview == {"customers": 1, "technicians": 1, "open_requests": 1, "critical_equipment": 1}

    def test_analytics(self, client, mine, theirs):
        log_in(client, mine.admin.email)

        analytics = client.get("/api/analytics").json()

        assert sum(item["count"] for item in analytics["by_status"]) == 1
        assert [t["name"] for t in analytics["technicians"]] == ["My Technician"]
        assert {item["name"]: item["count"] for item in analytics["equipment_risk"]}["critical"] == 1

    def test_knowledge_base(self, client, db_session, mine, theirs):
        category_id = db_session.scalar(select(KnowledgeBaseEntry.category_id).limit(1))
        db_session.add(
            KnowledgeBaseEntry(
                shop_id=theirs.admin.shop_id, category_id=category_id, issue_pattern="Their secret fix", suggested_fix="x"
            )
        )
        db_session.commit()

        log_in(client, mine.admin.email)

        assert "Their secret fix" not in {entry["issue_pattern"] for entry in client.get("/api/knowledge-base").json()}


class TestAnotherShopsRecordsAreNotFound:
    def test_updating_their_request(self, client, mine, theirs):
        log_in(client, mine.admin.email)

        response = client.patch(f"/api/requests/{theirs.request.id}", json={"status": "resolved"})

        assert response.status_code == 404

    def test_reading_or_writing_their_report(self, client, mine, theirs):
        log_in(client, mine.admin.email)

        assert client.get(f"/api/requests/{theirs.request.id}/report").status_code == 404
        assert client.post(f"/api/requests/{theirs.request.id}/report", json={"report_text": "Done."}).status_code == 404

    def test_suggestions_for_their_request(self, client, mine, theirs):
        log_in(client, mine.admin.email)

        assert client.get(f"/api/requests/{theirs.request.id}/suggestions").status_code == 404

    def test_recording_readings_on_their_equipment(self, client, mine, theirs):
        log_in(client, mine.admin.email)

        response = client.patch(
            f"/api/equipment/{theirs.equipment.id}/readings",
            json={
                "quality_grade": "M",
                "air_temperature_k": 300,
                "process_temperature_k": 310,
                "rotational_speed_rpm": 1500,
                "torque_nm": 40,
                "tool_wear_min": 100,
            },
        )

        assert response.status_code == 404

    def test_deactivating_their_user(self, client, db_session, mine, theirs):
        log_in(client, mine.admin.email)

        response = client.patch(f"/api/users/{theirs.technician.id}/active", json={"is_active": False})

        assert response.status_code == 404
        db_session.expire_all()
        assert db_session.get(User, theirs.technician.id).is_active

    def test_editing_their_knowledge_base_entry(self, client, db_session, mine, theirs):
        category_id = db_session.scalar(select(KnowledgeBaseEntry.category_id).limit(1))
        entry = KnowledgeBaseEntry(shop_id=theirs.admin.shop_id, category_id=category_id, issue_pattern="x", suggested_fix="y")
        db_session.add(entry)
        db_session.commit()

        log_in(client, mine.admin.email)

        assert client.delete(f"/api/knowledge-base/{entry.id}").status_code == 404


class TestNoMixingAcrossShops:
    def test_cannot_assign_their_technician_to_my_request(self, client, mine, theirs):
        log_in(client, mine.admin.email)

        response = client.patch(
            f"/api/requests/{mine.request.id}", json={"technician_id": theirs.technician.technician.id}
        )

        assert response.status_code == 400

    @pytest.mark.parametrize("who", ["admin", "technician"])
    def test_cannot_raise_a_request_for_their_customer(self, client, mine, theirs, who):
        log_in(client, getattr(mine, who).email)

        response = client.post(
            "/api/requests",
            json={"description": "Not cooling.", "customer_id": theirs.customer.customer.id, "address": "1 Mount Road"},
        )

        assert response.status_code == 400

    def test_staff_an_owner_creates_join_the_owner_s_shop(self, client, db_session, theirs):
        log_in(client, theirs.admin.email)

        response = client.post(
            "/api/users",
            json={"name": "New Tech", "email": "new@theirs.example", "password": PASSWORD, "role": "technician"},
        )

        assert response.status_code == 201
        assert db_session.scalar(select(User.shop_id).where(User.email == "new@theirs.example")) == theirs.admin.shop_id


class TestCustomerSignUp:
    def test_the_link_s_shop_is_the_customer_s_shop(self, client, db_session, make_shop):
        shop = make_shop(name="Ravi Aircon", slug="ravi-aircon")

        response = client.post(
            "/api/auth/register", json={"shop": "ravi-aircon", "name": "Priya", "phone": "+919876543210", "password": PASSWORD}
        )

        assert response.status_code == 201
        assert response.json()["shop_name"] == "Ravi Aircon"
        assert db_session.scalar(select(User.shop_id).where(User.name == "Priya")) == shop.id

    def test_an_unknown_shop_is_rejected(self, client):
        response = client.post(
            "/api/auth/register", json={"shop": "nobody", "name": "Priya", "phone": "+919876543210", "password": PASSWORD}
        )

        assert response.status_code == 400
        assert "sign-up link" in response.json()["detail"]

    def test_the_sign_up_page_can_look_up_the_shop_s_name(self, client, make_shop):
        make_shop(name="Ravi Aircon", slug="ravi-aircon")

        assert client.get("/api/shops/ravi-aircon").json() == {"name": "Ravi Aircon", "slug": "ravi-aircon"}
        assert client.get("/api/shops/nobody").status_code == 404


class TestShops:
    def test_logged_in_users_see_their_shop_s_name(self, client, make_user):
        admin = make_user(Role.ADMIN)
        log_in(client, admin.email)

        assert client.get("/api/auth/me").json()["shop_name"] == "Default shop"

    def test_data_from_before_shops_is_in_the_default_shop(self, db_session):
        # The seed_knowledge_base migration ran before shops existed; the shops migration moves
        # those entries into the default shop.
        shop_ids = set(db_session.scalars(select(KnowledgeBaseEntry.shop_id)))

        assert shop_ids == {DEFAULT_SHOP_ID}

    @pytest.mark.parametrize("slug", ["ab", "Has Spaces", "-starts-with-dash", "ends-with-dash-", "x" * 41])
    def test_slug_must_be_url_safe(self, db_session, slug):
        with pytest.raises(ShopError):
            create_shop(db_session, name="A Shop", slug=slug)

    def test_slug_must_be_unique(self, db_session):
        with pytest.raises(ShopError, match="already exists"):
            create_shop(db_session, name="Another default", slug=DEFAULT_SHOP_SLUG)
