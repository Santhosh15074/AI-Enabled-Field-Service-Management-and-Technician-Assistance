"""Triage (app.ml.triage), report structuring (app.ml.report_ai), assignment suggestions
(app.ml.assignment) and the shared Gemini client's hedging (app.ml.gemini). Gemini is never called
for real: gemini.generate is replaced with a stand-in that returns whatever a test sets."""

import time

import httpx
import pytest
from sqlalchemy import select

from app.config import get_settings
from app.ml import gemini
from app.models import Availability, ComplaintCategory, Equipment, RequestStatus, Role, ServiceRequest
from tests.conftest import log_in


@pytest.fixture
def customer(make_user):
    return make_user(Role.CUSTOMER, phone="+919000000001")


@pytest.fixture
def admin(make_user):
    return make_user(Role.ADMIN)


@pytest.fixture
def fake_gemini(monkeypatch):
    """Set `.answer` to what Gemini should return; `.calls` records each (instructions, prompt)."""

    class Fake:
        answer = None
        calls: list = []

        def __call__(self, instructions, prompt, *, schema=None, max_tokens=400):
            self.calls.append((instructions, prompt))
            return self.answer

    fake = Fake()
    fake.calls = []
    monkeypatch.setattr(gemini, "generate", fake)
    return fake


def submit(client, description, **body):
    return client.post("/api/requests", json={"description": description, "address": "12 Anna Salai", **body})


def category_named(db, name):
    return db.scalar(select(ComplaintCategory).where(ComplaintCategory.category_name == name))


class TestTriage:
    def test_ai_sets_urgency_reason_and_category(self, client, db_session, customer, fake_gemini):
        fake_gemini.answer = {"urgency": "high", "category": "HVAC", "reason": "Food is spoiling."}
        log_in(client, customer.email)

        data = submit(client, "fridge not cooling, food spoiling").json()

        assert data["urgency"] == "high"
        assert data["urgency_source"] == "ai"
        assert data["urgency_reason"] == "Food is spoiling."
        assert data["category"]["category_name"] == "HVAC"
        assert data["category_source"] == "ai"

    def test_a_category_the_customer_chose_is_kept(self, client, db_session, customer, fake_gemini):
        fake_gemini.answer = {"urgency": "low", "category": "HVAC", "reason": "Routine."}
        plumbing = category_named(db_session, "Plumbing")
        log_in(client, customer.email)

        data = submit(client, "general service please", category_id=plumbing.id).json()

        assert data["category"]["category_name"] == "Plumbing"
        assert data["category_source"] is None

    @pytest.mark.parametrize(
        "description, danger",
        [
            ("Burning smell from the AC", "burning"),
            ("sparks coming out of the plug", "sparks"),
            ("ஏசி ல இருந்து புகை வருது", "smoke"),
            ("washing machine la current adikkudhu", "an electric shock"),
            ("I can smell gas near the stove", "a gas smell or leak"),
        ],
    )
    def test_the_safety_rule_always_wins(self, client, customer, fake_gemini, description, danger):
        fake_gemini.answer = {"urgency": "low", "category": "Electrical", "reason": "Looks minor."}
        log_in(client, customer.email)

        data = submit(client, description).json()

        assert data["urgency"] == "high"
        assert data["urgency_source"] == "safety_rule"
        assert data["urgency_reason"] == f"Safety rule: the complaint mentions {danger}."
        assert data["category"]["category_name"] == "Electrical"  # AI still picks the category

    def test_melting_ice_is_not_a_safety_hit(self, client, customer, fake_gemini):
        fake_gemini.answer = {"urgency": "medium", "category": "HVAC", "reason": "Not cold enough."}
        log_in(client, customer.email)

        assert submit(client, "fridge ice is melting").json()["urgency_source"] == "ai"

    def test_without_ai_the_classifier_decides_and_no_category_is_guessed(self, client, customer, fake_gemini):
        log_in(client, customer.email)

        data = submit(client, "the unit is making a noise").json()

        assert data["urgency"] in {"low", "medium", "high"}
        assert data["urgency_source"] == "model"
        assert data["urgency_reason"] is None
        assert data["category"] is None

    @pytest.mark.parametrize(
        "answer",
        [
            {"urgency": "urgent", "category": "HVAC", "reason": "x"},
            {"urgency": "high", "category": "Spaceships", "reason": "x"},
            "not a dict",
        ],
    )
    def test_an_invalid_ai_answer_falls_back_to_the_classifier(self, client, customer, fake_gemini, answer):
        fake_gemini.answer = answer
        log_in(client, customer.email)

        assert submit(client, "the unit is making a noise").json()["urgency_source"] == "model"

    def test_equipment_is_sent_to_the_model(self, client, customer, fake_gemini):
        fake_gemini.answer = {"urgency": "medium", "category": "HVAC", "reason": "x"}
        log_in(client, customer.email)
        equipment_id = client.post("/api/equipment", json={"name": "Hall AC", "type": "Split AC"}).json()["id"]

        submit(client, "not cooling", equipment_id=equipment_id)

        assert "Equipment: Split AC (Hall AC)" in fake_gemini.calls[0][1]


class TestReportStructuring:
    @pytest.fixture
    def request_id(self, client, customer, make_user, admin):
        technician = make_user(Role.TECHNICIAN)
        log_in(client, customer.email)
        request_id = submit(client, "AC not cooling").json()["id"]
        log_in(client, admin.email)
        client.patch(f"/api/requests/{request_id}", json={"technician_id": technician.technician.id})
        log_in(client, technician.email)
        return request_id

    def test_ai_fills_the_fields(self, client, request_id, fake_gemini):
        fake_gemini.answer = {
            "issue": "Weak capacitor",
            "action_taken": "Replaced the capacitor",
            "parts_used": "45 mfd capacitor",
            "time_spent_minutes": 60,
        }

        response = client.post(
            f"/api/requests/{request_id}/report/extract",
            json={"report_text": "capacitor weak ah irundhuchu maathitten oru mani neram aachu"},
        )

        assert response.json() == {
            "issue": "Weak capacitor",
            "action_taken": "Replaced the capacitor",
            "parts_used": "45 mfd capacitor",
            "time_spent_minutes": 60,
            "source": "ai",
        }

    def test_without_ai_the_rules_fill_the_fields(self, client, request_id, fake_gemini):
        response = client.post(
            f"/api/requests/{request_id}/report/extract", json={"report_text": "Cleaned the filter. Took 20 minutes."}
        )

        assert response.json()["source"] == "rules"
        assert response.json()["time_spent_minutes"] == 20

    @pytest.mark.parametrize("minutes", [-5, 0, 100_000, True, "an hour"])
    def test_an_impossible_time_is_dropped(self, client, request_id, fake_gemini, minutes):
        fake_gemini.answer = {"issue": "x", "action_taken": "y", "parts_used": None, "time_spent_minutes": minutes}

        response = client.post(f"/api/requests/{request_id}/report/extract", json={"report_text": "notes"})

        assert response.json()["time_spent_minutes"] is None

    def test_an_empty_ai_answer_falls_back_to_the_rules(self, client, request_id, fake_gemini):
        fake_gemini.answer = {"issue": None, "action_taken": None, "parts_used": None, "time_spent_minutes": None}

        response = client.post(
            f"/api/requests/{request_id}/report/extract", json={"report_text": "Replaced the fan motor."}
        )

        assert response.json()["source"] == "rules"


class TestAssignmentSuggestion:
    @pytest.fixture
    def technicians(self, make_user, db_session):
        ravi = make_user(Role.TECHNICIAN, name="Ravi", email="ravi@example.com")
        ravi.technician.skill_area = "AC and fridge"
        kumar = make_user(Role.TECHNICIAN, name="Kumar", email="kumar@example.com")
        kumar.technician.skill_area = "Washing machines"
        db_session.commit()
        return ravi.technician, kumar.technician

    def raise_ac_request(self, client, customer, admin, db_session):
        log_in(client, customer.email)
        equipment_id = client.post("/api/equipment", json={"name": "Hall AC", "type": "AC"}).json()["id"]
        request_id = submit(client, "AC not cooling", equipment_id=equipment_id).json()["id"]
        log_in(client, admin.email)
        return request_id

    def test_ai_picks_one_of_the_shop_s_technicians(self, client, db_session, customer, admin, technicians, fake_gemini):
        ravi, kumar = technicians
        request_id = self.raise_ac_request(client, customer, admin, db_session)
        fake_gemini.answer = {"technician_id": ravi.id, "reason": "Ravi handles ACs and is free."}

        response = client.get(f"/api/requests/{request_id}/assignment-suggestion")

        assert response.json() == {
            "technician_id": ravi.id,
            "technician_name": "Ravi",
            "reason": "Ravi handles ACs and is free.",
            "source": "ai",
        }
        prompt = fake_gemini.calls[-1][1]
        assert "Ravi; skill area: AC and fridge" in prompt and "Kumar" in prompt

    def test_an_id_outside_the_list_is_ignored(self, client, db_session, customer, admin, technicians, fake_gemini):
        request_id = self.raise_ac_request(client, customer, admin, db_session)
        fake_gemini.answer = {"technician_id": 999, "reason": "Someone else."}

        response = client.get(f"/api/requests/{request_id}/assignment-suggestion")

        assert response.json()["source"] == "rules"

    def test_without_ai_the_skill_match_wins(self, client, db_session, customer, admin, technicians, fake_gemini):
        request_id = self.raise_ac_request(client, customer, admin, db_session)

        data = client.get(f"/api/requests/{request_id}/assignment-suggestion").json()

        assert data["technician_name"] == "Ravi"
        assert data["source"] == "rules"
        assert data["reason"] == "Ravi: skill area (AC and fridge) fits, 0 open jobs."

    def test_without_ai_workload_and_availability_count(self, client, db_session, customer, admin, technicians, fake_gemini):
        ravi, kumar = technicians
        request_id = self.raise_ac_request(client, customer, admin, db_session)
        ravi.availability = Availability.OFF_DUTY
        db_session.commit()

        assert client.get(f"/api/requests/{request_id}/assignment-suggestion").json()["technician_name"] == "Kumar"

    def test_open_jobs_are_counted(self, client, db_session, customer, admin, technicians, fake_gemini):
        ravi, kumar = technicians
        request_id = self.raise_ac_request(client, customer, admin, db_session)
        for _ in range(2):
            db_session.add(
                ServiceRequest(customer_id=customer.customer.id, description="x", technician_id=ravi.id, status=RequestStatus.IN_PROGRESS)
            )
        db_session.commit()
        fake_gemini.answer = {"technician_id": kumar.id, "reason": "r"}

        client.get(f"/api/requests/{request_id}/assignment-suggestion")

        assert "Ravi; skill area: AC and fridge; available; 2 unresolved jobs" in fake_gemini.calls[-1][1]

    def test_a_shop_with_no_technicians_gets_none(self, client, customer, admin, fake_gemini):
        log_in(client, customer.email)
        request_id = submit(client, "AC not cooling").json()["id"]
        log_in(client, admin.email)

        response = client.get(f"/api/requests/{request_id}/assignment-suggestion")

        assert response.status_code == 200
        assert response.json() is None

    def test_only_admins_can_ask(self, client, customer, technicians, fake_gemini):
        log_in(client, customer.email)
        request_id = submit(client, "AC not cooling").json()["id"]

        assert client.get(f"/api/requests/{request_id}/assignment-suggestion").status_code == 403

    def test_another_shop_s_request_is_404(self, client, customer, admin, make_user, make_shop, fake_gemini):
        log_in(client, customer.email)
        request_id = submit(client, "AC not cooling").json()["id"]
        other_admin = make_user(Role.ADMIN, email="other-admin@example.com", shop_id=make_shop().id)
        log_in(client, other_admin.email)

        assert client.get(f"/api/requests/{request_id}/assignment-suggestion").status_code == 404


class TestHedging:
    """A slow main model gets raced by the backup; whichever answers first wins."""

    @pytest.fixture(autouse=True)
    def _settings(self, monkeypatch):
        settings = get_settings()
        monkeypatch.setattr(settings, "gemini_api_key", "test-key")
        monkeypatch.setattr(settings, "ai_fallback_model", "main")
        monkeypatch.setattr(settings, "ai_backup_model", "backup")
        monkeypatch.setattr(settings, "ai_hedge_after_seconds", 0.2)
        monkeypatch.setattr(settings, "ai_fallback_timeout_seconds", 2.0)

    def serve(self, monkeypatch, handler):
        monkeypatch.setattr(gemini, "_client", lambda: httpx.Client(transport=httpx.MockTransport(handler)))

    @staticmethod
    def reply(text):
        return httpx.Response(200, json={"candidates": [{"content": {"parts": [{"text": text}]}}]})

    def test_a_fast_main_model_answers_alone(self, monkeypatch):
        asked = []
        self.serve(monkeypatch, lambda request: asked.append(request.url.path) or self.reply("main says"))

        assert gemini.generate("i", "p") == "main says"
        assert len(asked) == 1 and "/main:" in asked[0]

    def test_a_slow_main_model_loses_to_the_backup(self, monkeypatch):
        def handler(request):
            if "/main:" in request.url.path:
                time.sleep(1.0)
                return self.reply("main says")
            return self.reply("backup says")

        self.serve(monkeypatch, handler)
        started = time.monotonic()

        assert gemini.generate("i", "p") == "backup says"
        assert time.monotonic() - started < 0.9

    def test_a_failing_main_model_falls_to_the_backup(self, monkeypatch):
        def handler(request):
            if "/main:" in request.url.path:
                return httpx.Response(503, json={"error": "overloaded"})
            return self.reply("backup says")

        self.serve(monkeypatch, handler)

        assert gemini.generate("i", "p") == "backup says"

    def test_json_answers_are_parsed(self, monkeypatch):
        self.serve(monkeypatch, lambda request: self.reply('{"urgency": "low"}'))

        assert gemini.generate("i", "p", schema={"type": "object"}) == {"urgency": "low"}

    def test_both_failing_returns_none(self, monkeypatch):
        self.serve(monkeypatch, lambda request: httpx.Response(500))

        assert gemini.generate("i", "p") is None
