import pytest

from app.models import Role
from tests.conftest import log_in


@pytest.fixture
def customer(make_user):
    return make_user(Role.CUSTOMER, phone="+919000000010")


@pytest.fixture
def technician(make_user):
    return make_user(Role.TECHNICIAN)


@pytest.fixture
def admin(make_user):
    return make_user(Role.ADMIN)


@pytest.fixture
def assigned_request_id(client, customer, technician, admin):
    log_in(client, customer.email)
    request_id = client.post(
        "/api/requests", json={"description": "The unit is making a loud noise.", "address": "12 Anna Salai, Chennai"}
    ).json()["id"]
    log_in(client, admin.email)
    client.patch(f"/api/requests/{request_id}", json={"technician_id": technician.technician.id})
    return request_id


REPORT_TEXT = (
    "Found a seized bearing on the motor shaft. Replaced the bearing and tested the unit under load. "
    "Took about 45 minutes."
)


class TestExtract:
    def test_technician_can_preview_extraction_for_their_own_job(self, client, technician, assigned_request_id):
        log_in(client, technician.email)

        response = client.post(f"/api/requests/{assigned_request_id}/report/extract", json={"report_text": REPORT_TEXT})

        assert response.status_code == 200
        assert response.json()["time_spent_minutes"] == 45
        assert "bearing" in response.json()["parts_used"]

    def test_extracting_does_not_save_anything(self, client, technician, assigned_request_id):
        log_in(client, technician.email)
        client.post(f"/api/requests/{assigned_request_id}/report/extract", json={"report_text": REPORT_TEXT})

        assert client.get(f"/api/requests/{assigned_request_id}/report").status_code == 404

    def test_a_technician_cannot_preview_for_someone_else_s_job(self, client, customer, admin, make_user, assigned_request_id):
        other_technician = make_user(Role.TECHNICIAN, email="other@example.com")
        log_in(client, other_technician.email)

        response = client.post(f"/api/requests/{assigned_request_id}/report/extract", json={"report_text": REPORT_TEXT})

        assert response.status_code == 403

    def test_customers_cannot_preview_extraction(self, client, customer, assigned_request_id):
        log_in(client, customer.email)

        assert client.post(f"/api/requests/{assigned_request_id}/report/extract", json={"report_text": REPORT_TEXT}).status_code == 403


class TestCreateReport:
    def test_technician_can_save_a_report_with_corrected_fields(self, client, technician, assigned_request_id):
        log_in(client, technician.email)

        response = client.post(
            f"/api/requests/{assigned_request_id}/report",
            json={
                "report_text": REPORT_TEXT,
                "issue": "Seized motor bearing",
                "action_taken": "Replaced bearing, tested under load",
                "parts_used": "Bearing",
                "time_spent_minutes": 45,
            },
        )

        assert response.status_code == 201
        body = response.json()
        assert body["request_id"] == assigned_request_id
        assert body["issue"] == "Seized motor bearing"
        assert body["time_spent_minutes"] == 45

    def test_a_request_can_only_have_one_report(self, client, technician, assigned_request_id):
        log_in(client, technician.email)
        client.post(f"/api/requests/{assigned_request_id}/report", json={"report_text": REPORT_TEXT})

        response = client.post(f"/api/requests/{assigned_request_id}/report", json={"report_text": "A second report."})

        assert response.status_code == 400
        assert "already has a report" in response.json()["detail"]

    def test_rejects_an_empty_report(self, client, technician, assigned_request_id):
        log_in(client, technician.email)

        assert client.post(f"/api/requests/{assigned_request_id}/report", json={"report_text": "   "}).status_code == 400

    def test_structured_fields_are_optional(self, client, technician, assigned_request_id):
        log_in(client, technician.email)

        response = client.post(f"/api/requests/{assigned_request_id}/report", json={"report_text": "Visited site, no issue found."})

        assert response.status_code == 201
        assert response.json()["issue"] is None

    def test_admin_can_also_write_a_report(self, client, admin, assigned_request_id):
        log_in(client, admin.email)

        assert client.post(f"/api/requests/{assigned_request_id}/report", json={"report_text": REPORT_TEXT}).status_code == 201

    def test_a_technician_cannot_report_on_someone_else_s_job(self, client, make_user, assigned_request_id):
        other_technician = make_user(Role.TECHNICIAN, email="other@example.com")
        log_in(client, other_technician.email)

        assert client.post(f"/api/requests/{assigned_request_id}/report", json={"report_text": REPORT_TEXT}).status_code == 403

    def test_customers_cannot_write_reports(self, client, customer, assigned_request_id):
        log_in(client, customer.email)

        assert client.post(f"/api/requests/{assigned_request_id}/report", json={"report_text": REPORT_TEXT}).status_code == 403

    def test_reporting_on_an_unknown_request_is_404(self, client, technician):
        log_in(client, technician.email)

        assert client.post("/api/requests/999999/report", json={"report_text": REPORT_TEXT}).status_code == 404


class TestGetReport:
    def test_the_owning_customer_can_view_the_report(self, client, customer, technician, assigned_request_id):
        log_in(client, technician.email)
        client.post(f"/api/requests/{assigned_request_id}/report", json={"report_text": REPORT_TEXT})

        log_in(client, customer.email)
        response = client.get(f"/api/requests/{assigned_request_id}/report")

        assert response.status_code == 200
        assert response.json()["report_text"] == REPORT_TEXT

    def test_a_different_customer_cannot_view_it(self, client, technician, assigned_request_id, make_user):
        log_in(client, technician.email)
        client.post(f"/api/requests/{assigned_request_id}/report", json={"report_text": REPORT_TEXT})

        other_customer = make_user(Role.CUSTOMER, phone="+919000000011", email=None)
        log_in(client, other_customer.customer.phone)

        assert client.get(f"/api/requests/{assigned_request_id}/report").status_code == 403

    def test_missing_report_is_404(self, client, technician, assigned_request_id):
        log_in(client, technician.email)

        assert client.get(f"/api/requests/{assigned_request_id}/report").status_code == 404
