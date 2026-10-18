from types import SimpleNamespace

import pytest
from sqlalchemy import select

from app.models import ComplaintCategory, Equipment, Notification, RequestStatus, RequestStatusLog, Role, ServiceRequest
from tests.conftest import log_in


@pytest.fixture
def customer(make_user):
    return make_user(Role.CUSTOMER, phone="+919000000001")


@pytest.fixture
def technician(make_user):
    return make_user(Role.TECHNICIAN)


@pytest.fixture
def admin(make_user):
    return make_user(Role.ADMIN)


def submit(client, **overrides):
    body = {"description": "The unit is making a loud noise.", "address": "12 Anna Salai, Chennai"}
    body.update(overrides)
    return client.post("/api/requests", json=body)


class TestEquipment:
    def test_customer_can_register_and_list_equipment(self, client, customer):
        log_in(client, customer.email)

        created = client.post("/api/equipment", json={"name": "Lathe #1", "type": "Lathe", "serial_number": "SN-1"})
        assert created.status_code == 201
        assert created.json()["name"] == "Lathe #1"

        listed = client.get("/api/equipment")
        assert listed.status_code == 200
        assert [item["name"] for item in listed.json()] == ["Lathe #1"]

    def test_only_customers_can_register_equipment(self, client, technician):
        log_in(client, technician.email)

        assert client.post("/api/equipment", json={"name": "X", "type": "Y"}).status_code == 403

    def test_a_customer_only_sees_their_own_equipment(self, client, db_session, customer, make_user):
        other = make_user(Role.CUSTOMER, phone="+919000000002", email=None)
        db_session.add(Equipment(customer_id=other.customer.id, name="Not mine", type="Lathe"))
        db_session.commit()

        log_in(client, customer.email)

        assert client.get("/api/equipment").json() == []

    def test_freshly_registered_equipment_has_no_risk_yet(self, client, customer):
        log_in(client, customer.email)

        created = client.post("/api/equipment", json={"name": "Lathe #1", "type": "Lathe"})

        assert created.json()["risk_level"] is None
        assert created.json()["risk_score"] is None


class TestAllEquipment:
    """The admin fleet-risk view — GET /api/equipment/all, as opposed to a customer's own,
    narrower GET /api/equipment."""

    def test_only_admins_can_list_all_equipment(self, client, customer):
        log_in(client, customer.email)

        assert client.get("/api/equipment/all").status_code == 403

    def test_admin_sees_every_customer_s_equipment_with_owner_details(self, client, db_session, admin, customer, make_user):
        other = make_user(Role.CUSTOMER, phone="+919000000005", email=None)
        db_session.add(Equipment(customer_id=customer.customer.id, name="Mine", type="Lathe"))
        db_session.add(Equipment(customer_id=other.customer.id, name="Theirs", type="Pump"))
        db_session.commit()

        log_in(client, admin.email)
        response = client.get("/api/equipment/all")

        assert response.status_code == 200
        names = {item["name"]: item["customer"]["phone"] for item in response.json()}
        assert names == {"Mine": customer.customer.phone, "Theirs": other.customer.phone}

    def test_worst_risk_sorts_first(self, client, db_session, admin, customer, monkeypatch):
        from app.models import RiskLevel
        from app.routes import equipment as equipment_module

        good = Equipment(customer_id=customer.customer.id, name="Good", type="Lathe")
        critical = Equipment(customer_id=customer.customer.id, name="Critical", type="Lathe")
        db_session.add_all([good, critical])
        db_session.commit()

        log_in(client, admin.email)
        monkeypatch.setattr(equipment_module, "predict_risk", lambda eq: (RiskLevel.GOOD, 0.01))
        client.patch(f"/api/equipment/{good.id}/readings", json=READINGS)
        monkeypatch.setattr(equipment_module, "predict_risk", lambda eq: (RiskLevel.CRITICAL, 0.9))
        client.patch(f"/api/equipment/{critical.id}/readings", json=READINGS)

        response = client.get("/api/equipment/all")

        names = [item["name"] for item in response.json()]
        assert names.index("Critical") < names.index("Good")


READINGS = {
    "quality_grade": "L",
    "air_temperature_k": 298.1,
    "process_temperature_k": 308.6,
    "rotational_speed_rpm": 1551,
    "torque_nm": 42.8,
    "tool_wear_min": 0,
}


class TestEquipmentReadings:
    @pytest.fixture
    def equipment_id(self, client, customer):
        log_in(client, customer.email)
        return client.post("/api/equipment", json={"name": "Lathe #1", "type": "Lathe"}).json()["id"]

    @pytest.fixture
    def visited_equipment_id(self, client, customer, technician, admin, equipment_id):
        # A technician may only record readings for equipment they've actually been sent to —
        # see app.routes.equipment.record_readings — so this ties them together with a request.
        log_in(client, customer.email)
        request_id = submit(client, equipment_id=equipment_id).json()["id"]
        log_in(client, admin.email)
        client.patch(f"/api/requests/{request_id}", json={"technician_id": technician.technician.id})
        return equipment_id

    def test_technician_can_record_readings_for_equipment_they_visited(self, client, technician, visited_equipment_id):
        log_in(client, technician.email)

        response = client.patch(f"/api/equipment/{visited_equipment_id}/readings", json=READINGS)

        assert response.status_code == 200
        assert response.json()["risk_level"] in {"good", "moderate", "critical"}
        assert isinstance(response.json()["risk_score"], float)

    def test_a_technician_cannot_record_readings_for_equipment_they_never_visited(self, client, technician, equipment_id):
        log_in(client, technician.email)

        response = client.patch(f"/api/equipment/{equipment_id}/readings", json=READINGS)

        assert response.status_code == 403

    def test_admin_can_record_readings_for_any_equipment(self, client, admin, equipment_id):
        log_in(client, admin.email)

        assert client.patch(f"/api/equipment/{equipment_id}/readings", json=READINGS).status_code == 200

    def test_customers_cannot_record_readings(self, client, customer, equipment_id):
        log_in(client, customer.email)

        assert client.patch(f"/api/equipment/{equipment_id}/readings", json=READINGS).status_code == 403

    def test_rejects_an_invalid_quality_grade(self, client, admin, equipment_id):
        log_in(client, admin.email)

        response = client.patch(f"/api/equipment/{equipment_id}/readings", json={**READINGS, "quality_grade": "X"})

        assert response.status_code == 400

    def test_recording_readings_logs_a_prediction(self, client, db_session, admin, equipment_id):
        from app.models import PredictionLog

        log_in(client, admin.email)
        client.patch(f"/api/equipment/{equipment_id}/readings", json=READINGS)

        assert db_session.scalar(select(PredictionLog).where(PredictionLog.equipment_id == equipment_id)) is not None

    def test_readings_for_unknown_equipment_is_404(self, client, admin):
        log_in(client, admin.email)

        assert client.patch("/api/equipment/999999/readings", json=READINGS).status_code == 404

    def test_a_resolved_critical_prediction_surfaces_on_the_admin_overview(self, client, admin, equipment_id, monkeypatch):
        from app.models import RiskLevel
        from app.routes import equipment as equipment_module

        monkeypatch.setattr(equipment_module, "predict_risk", lambda eq: (RiskLevel.CRITICAL, 0.9))
        log_in(client, admin.email)
        client.patch(f"/api/equipment/{equipment_id}/readings", json=READINGS)

        assert client.get("/api/overview/admin").json()["critical_equipment"] == 1


class TestCreateRequest:
    def test_asks_for_address_only_when_none_is_on_file(self, client, db_session, customer):
        log_in(client, customer.email)

        missing_address = submit(client, address="")
        assert missing_address.status_code == 400
        assert "address" in missing_address.json()["detail"]

        first = submit(client)
        assert first.status_code == 201
        db_session.refresh(customer.customer)
        assert customer.customer.address == "12 Anna Salai, Chennai"

        # Now that an address is on file, a second complaint doesn't need to repeat it.
        second = submit(client, address="")
        assert second.status_code == 201

    def test_logs_the_initial_status(self, client, db_session, customer):
        log_in(client, customer.email)

        response = submit(client)

        request_id = response.json()["id"]
        log = db_session.scalar(select(RequestStatusLog).where(RequestStatusLog.request_id == request_id))
        assert log.old_status is None
        assert log.new_status == RequestStatus.OPEN

    def test_rejects_an_empty_description(self, client, customer):
        log_in(client, customer.email)

        assert submit(client, description="   ").status_code == 400

    def test_can_attach_the_customer_s_own_equipment(self, client, customer):
        log_in(client, customer.email)
        equipment_id = client.post("/api/equipment", json={"name": "Lathe #1", "type": "Lathe"}).json()["id"]

        response = submit(client, equipment_id=equipment_id)

        assert response.status_code == 201
        assert response.json()["equipment"]["id"] == equipment_id

    def test_cannot_attach_someone_else_s_equipment(self, client, db_session, customer, make_user):
        other = make_user(Role.CUSTOMER, phone="+919000000003", email=None)
        other_equipment = Equipment(customer_id=other.customer.id, name="Not mine", type="Lathe")
        db_session.add(other_equipment)
        db_session.commit()

        log_in(client, customer.email)
        response = submit(client, equipment_id=other_equipment.id)

        assert response.status_code == 400

    def test_only_customers_can_submit_a_request(self, client, technician):
        log_in(client, technician.email)

        assert submit(client).status_code == 403

    def test_every_request_gets_an_urgency(self, client, customer):
        # Whether or not a trained classifier is on disk, app.ml.urgency.predict_urgency always
        # returns one of the three valid levels — see tests/test_urgency.py for that in isolation.
        log_in(client, customer.email)

        response = submit(client)

        assert response.json()["urgency"] in {"low", "medium", "high"}


class TestCategories:
    def test_lists_the_seeded_categories(self, client, customer):
        # Seeded by the migration (alembic/versions/..._seed_complaint_categories.py), so this
        # is really checking that migration ran, not any app logic.
        log_in(client, customer.email)

        response = client.get("/api/requests/categories")

        assert response.status_code == 200
        names = {category["category_name"] for category in response.json()}
        assert names == {"Electrical", "Mechanical", "HVAC", "Plumbing", "Electronic", "General"}

    def test_only_customers_can_list_categories(self, client, technician):
        log_in(client, technician.email)

        assert client.get("/api/requests/categories").status_code == 403

    def test_admins_can_also_list_categories(self, client, admin):
        # Needed for the knowledge-base admin screen's category picker.
        log_in(client, admin.email)

        assert client.get("/api/requests/categories").status_code == 200

    def test_can_attach_a_category(self, client, db_session, customer):
        log_in(client, customer.email)
        category_id = db_session.scalar(select(ComplaintCategory).where(ComplaintCategory.category_name == "Electrical")).id

        response = submit(client, category_id=category_id)

        assert response.status_code == 201
        assert response.json()["category"]["category_name"] == "Electrical"

    def test_rejects_an_unknown_category(self, client, customer):
        log_in(client, customer.email)

        assert submit(client, category_id=999999).status_code == 400


class TestListRequests:
    def test_customer_sees_only_their_own_requests_newest_first(self, client, customer, make_user):
        other = make_user(Role.CUSTOMER, phone="+919000000004", email=None)
        log_in(client, other.customer.phone)
        submit(client, description="Someone else's problem")

        log_in(client, customer.email)
        submit(client, description="First")
        submit(client, description="Second")

        response = client.get("/api/requests/mine")

        assert [r["description"] for r in response.json()] == ["Second", "First"]

    def test_admin_sees_every_request(self, client, customer, admin):
        log_in(client, customer.email)
        submit(client)

        log_in(client, admin.email)
        response = client.get("/api/requests")

        assert len(response.json()) == 1
        assert response.json()[0]["customer"]["name"] == customer.name

    def test_customer_cannot_list_all_requests(self, client, customer):
        log_in(client, customer.email)

        assert client.get("/api/requests").status_code == 403

    def test_admin_lists_only_active_technicians_by_name(self, client, admin, make_user, db_session):
        make_user(Role.TECHNICIAN, email="zed@example.com", name="Zed")
        inactive = make_user(Role.TECHNICIAN, email="inactive@example.com", name="Invisible")
        inactive.is_active = False
        db_session.commit()
        make_user(Role.TECHNICIAN, email="amy@example.com", name="Amy")

        log_in(client, admin.email)
        response = client.get("/api/requests/technicians")

        # Alphabetical, and the inactive technician is excluded entirely.
        assert [t["name"] for t in response.json()] == ["Amy", "Zed"]


class TestAssignment:
    def test_admin_assigning_a_technician_moves_an_open_request_to_in_progress(
        self, client, db_session, customer, technician, admin
    ):
        log_in(client, customer.email)
        request_id = submit(client).json()["id"]

        log_in(client, admin.email)
        response = client.patch(f"/api/requests/{request_id}", json={"technician_id": technician.technician.id})

        assert response.status_code == 200
        assert response.json()["status"] == "in_progress"
        assert response.json()["technician"]["id"] == technician.technician.id
        logs = db_session.scalars(
            select(RequestStatusLog).where(RequestStatusLog.request_id == request_id).order_by(RequestStatusLog.id)
        ).all()
        assert [log.new_status for log in logs] == [RequestStatus.OPEN, RequestStatus.IN_PROGRESS]

    def test_assigning_notifies_customer_and_technician(self, client, db_session, customer, technician, admin):
        log_in(client, customer.email)
        request_id = submit(client).json()["id"]

        log_in(client, admin.email)
        client.patch(f"/api/requests/{request_id}", json={"technician_id": technician.technician.id})

        recipients = {n.user_id for n in db_session.scalars(select(Notification)).all()}
        assert recipients == {customer.id, technician.id}

    def test_reassigning_an_in_progress_request_does_not_change_its_status(
        self, client, customer, technician, admin, make_user
    ):
        other_technician = make_user(Role.TECHNICIAN, email="other@example.com")
        log_in(client, customer.email)
        request_id = submit(client).json()["id"]
        log_in(client, admin.email)
        client.patch(f"/api/requests/{request_id}", json={"technician_id": technician.technician.id})

        response = client.patch(f"/api/requests/{request_id}", json={"technician_id": other_technician.technician.id})

        assert response.json()["status"] == "in_progress"
        assert response.json()["technician"]["id"] == other_technician.technician.id

    def test_only_an_admin_can_assign(self, client, customer, technician):
        log_in(client, customer.email)
        request_id = submit(client).json()["id"]

        log_in(client, technician.email)
        response = client.patch(f"/api/requests/{request_id}", json={"technician_id": technician.technician.id})

        assert response.status_code == 403

    def test_assigning_an_unknown_technician_fails(self, client, customer, admin):
        log_in(client, customer.email)
        request_id = submit(client).json()["id"]

        log_in(client, admin.email)
        response = client.patch(f"/api/requests/{request_id}", json={"technician_id": 999999})

        assert response.status_code == 400


class TestStatusUpdates:
    def test_assigned_technician_can_advance_status(self, client, customer, technician, admin):
        log_in(client, customer.email)
        request_id = submit(client).json()["id"]
        log_in(client, admin.email)
        client.patch(f"/api/requests/{request_id}", json={"technician_id": technician.technician.id})

        log_in(client, technician.email)
        response = client.patch(f"/api/requests/{request_id}", json={"status": "resolved"})

        assert response.status_code == 200
        assert response.json()["status"] == "resolved"

    def test_a_technician_cannot_update_a_request_assigned_to_someone_else(
        self, client, customer, technician, admin, make_user
    ):
        other_technician = make_user(Role.TECHNICIAN, email="other@example.com")
        log_in(client, customer.email)
        request_id = submit(client).json()["id"]
        log_in(client, admin.email)
        client.patch(f"/api/requests/{request_id}", json={"technician_id": technician.technician.id})

        log_in(client, other_technician.email)
        response = client.patch(f"/api/requests/{request_id}", json={"status": "resolved"})

        assert response.status_code == 403

    def test_status_cannot_move_backwards(self, client, customer, technician, admin):
        log_in(client, customer.email)
        request_id = submit(client).json()["id"]
        log_in(client, admin.email)
        client.patch(f"/api/requests/{request_id}", json={"technician_id": technician.technician.id})
        client.patch(f"/api/requests/{request_id}", json={"status": "resolved"})

        response = client.patch(f"/api/requests/{request_id}", json={"status": "open"})

        assert response.status_code == 400

    def test_rejects_an_unknown_status(self, client, customer, admin):
        log_in(client, customer.email)
        request_id = submit(client).json()["id"]

        log_in(client, admin.email)
        response = client.patch(f"/api/requests/{request_id}", json={"status": "cancelled"})

        assert response.status_code == 400

    def test_update_requires_at_least_one_field(self, client, customer, admin):
        log_in(client, customer.email)
        request_id = submit(client).json()["id"]

        log_in(client, admin.email)
        assert client.patch(f"/api/requests/{request_id}", json={}).status_code == 400

    def test_updating_an_unknown_request_is_404(self, client, admin):
        log_in(client, admin.email)

        assert client.patch("/api/requests/999999", json={"status": "resolved"}).status_code == 404

    def test_changing_status_notifies_the_customer(self, client, db_session, customer, technician, admin):
        log_in(client, customer.email)
        request_id = submit(client).json()["id"]
        log_in(client, admin.email)
        client.patch(f"/api/requests/{request_id}", json={"technician_id": technician.technician.id})

        log_in(client, technician.email)
        client.patch(f"/api/requests/{request_id}", json={"status": "resolved"})

        messages = [
            n.message
            for n in db_session.scalars(select(Notification).where(Notification.user_id == customer.id)).all()
        ]
        assert any("resolved" in m for m in messages)


class TestAssignedQueue:
    def test_technician_sees_only_their_own_jobs_active_ones_first(
        self, client, db_session, customer, technician, admin, make_user
    ):
        other_technician = make_user(Role.TECHNICIAN, email="other@example.com")
        log_in(client, customer.email)
        first_id = submit(client, description="First").json()["id"]
        second_id = submit(client, description="Second").json()["id"]
        not_mine_id = submit(client, description="Not mine").json()["id"]

        log_in(client, admin.email)
        client.patch(f"/api/requests/{first_id}", json={"technician_id": technician.technician.id})
        client.patch(f"/api/requests/{second_id}", json={"technician_id": technician.technician.id})
        client.patch(f"/api/requests/{not_mine_id}", json={"technician_id": other_technician.technician.id})
        client.patch(f"/api/requests/{first_id}", json={"status": "resolved"})

        log_in(client, technician.email)
        response = client.get("/api/requests/assigned")

        descriptions = [r["description"] for r in response.json()]
        assert descriptions == ["Second", "First"]

    def test_only_technicians_can_view_the_assigned_queue(self, client, customer):
        log_in(client, customer.email)

        assert client.get("/api/requests/assigned").status_code == 403


class TestSuggestions:
    """Both endpoints just call app.ml.troubleshooting.suggest_fixes and reshape the result —
    see tests/test_troubleshooting.py for the matching logic itself. These are about routing and
    permissions, so the real model is swapped out for a deterministic stand-in."""

    @pytest.fixture
    def fake_suggestions(self, monkeypatch):
        from app.routes import service_requests

        entry = SimpleNamespace(equipment_type="Pump", issue_pattern="the pump is leaking", suggested_fix="Tighten the fitting.")
        calls = []

        def fake(db, description, limit=3):
            calls.append(description)
            return [(entry, 0.87)]

        monkeypatch.setattr(service_requests, "suggest_fixes", fake)
        return calls

    def test_customer_can_get_suggestions_before_submitting(self, client, customer, fake_suggestions):
        log_in(client, customer.email)

        response = client.post("/api/requests/suggestions", json={"description": "it's leaking everywhere"})

        assert response.status_code == 200
        assert response.json() == [
            {"equipment_type": "Pump", "issue_pattern": "the pump is leaking", "suggested_fix": "Tighten the fitting.", "similarity": 0.87}
        ]
        assert fake_suggestions == ["it's leaking everywhere"]

    def test_only_customers_can_request_suggestions_before_submitting(self, client, technician, fake_suggestions):
        log_in(client, technician.email)

        assert client.post("/api/requests/suggestions", json={"description": "x"}).status_code == 403

    def test_technician_can_see_suggestions_for_their_own_assigned_request(
        self, client, customer, technician, admin, fake_suggestions
    ):
        log_in(client, customer.email)
        request_id = submit(client).json()["id"]
        log_in(client, admin.email)
        client.patch(f"/api/requests/{request_id}", json={"technician_id": technician.technician.id})

        log_in(client, technician.email)
        response = client.get(f"/api/requests/{request_id}/suggestions")

        assert response.status_code == 200
        assert response.json()[0]["similarity"] == 0.87

    def test_admin_can_see_suggestions_for_any_request(self, client, customer, admin, fake_suggestions):
        log_in(client, customer.email)
        request_id = submit(client).json()["id"]

        log_in(client, admin.email)
        assert client.get(f"/api/requests/{request_id}/suggestions").status_code == 200

    def test_a_technician_cannot_see_suggestions_for_someone_else_s_request(
        self, client, customer, technician, admin, make_user, fake_suggestions
    ):
        other_technician = make_user(Role.TECHNICIAN, email="other@example.com")
        log_in(client, customer.email)
        request_id = submit(client).json()["id"]
        log_in(client, admin.email)
        client.patch(f"/api/requests/{request_id}", json={"technician_id": technician.technician.id})

        log_in(client, other_technician.email)
        assert client.get(f"/api/requests/{request_id}/suggestions").status_code == 403

    def test_suggestions_for_an_unknown_request_is_404(self, client, admin, fake_suggestions):
        log_in(client, admin.email)

        assert client.get("/api/requests/999999/suggestions").status_code == 404
