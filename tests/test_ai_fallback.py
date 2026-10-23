"""The troubleshooting assistant's AI fallback (app.ml.ai_fallback): when it's used, who sees it,
that it's saved once per request, and that every failure falls back to "no suggestion". Gemini is
never called for real; draft_fix's HTTP is served by an httpx.MockTransport."""

import httpx
import pytest
from sqlalchemy import select

from app.config import get_settings
from app.ml import ai_fallback, gemini
from app.ml.ai_fallback import AiDraft
from app.models import AiSuggestion, Role
from tests.conftest import log_in


@pytest.fixture
def customer(make_user):
    return make_user(Role.CUSTOMER, phone="+919000000001")


@pytest.fixture
def admin(make_user):
    return make_user(Role.ADMIN)


@pytest.fixture
def technician(make_user):
    return make_user(Role.TECHNICIAN)


@pytest.fixture
def key(monkeypatch):
    monkeypatch.setattr(get_settings(), "gemini_api_key", "test-key")


@pytest.fixture
def no_kb_match(monkeypatch):
    from app.routes import service_requests

    monkeypatch.setattr(service_requests, "suggest_fixes", lambda db, description, *, shop_id, limit=3: [])


@pytest.fixture
def fake_draft(monkeypatch, key):
    """Replaces the Gemini call; returns the list of (description, equipment) it was asked about."""
    calls = []

    def fake(description, equipment=None, *, for_customer=False):
        calls.append((description, equipment, for_customer))
        return AiDraft(text="1. Switch off the power.\n2. Check the capacitor.", model="google:test")

    monkeypatch.setattr(ai_fallback, "draft_fix", fake)
    return calls


def raise_request(client, customer, admin, **body):
    log_in(client, customer.email)
    request_id = client.post(
        "/api/requests", json={"description": "AC clicks and blinks, no cooling", "address": "12 Anna Salai", **body}
    ).json()["id"]
    log_in(client, admin.email)
    return request_id


class TestPerRequest:
    def test_no_kb_match_returns_an_ai_draft(self, client, customer, admin, no_kb_match, fake_draft):
        request_id = raise_request(client, customer, admin)

        response = client.get(f"/api/requests/{request_id}/suggestions")

        assert response.status_code == 200
        assert response.json() == [
            {
                "equipment_type": None,
                "issue_pattern": "AC clicks and blinks, no cooling",
                "suggested_fix": "1. Switch off the power.\n2. Check the capacitor.",
                "similarity": None,
                "source": "ai",
            }
        ]

    def test_the_draft_is_saved_and_reused(self, client, db_session, customer, admin, no_kb_match, fake_draft):
        request_id = raise_request(client, customer, admin)

        client.get(f"/api/requests/{request_id}/suggestions")
        second = client.get(f"/api/requests/{request_id}/suggestions")

        assert second.json()[0]["source"] == "ai"
        assert len(fake_draft) == 1
        saved = db_session.scalar(select(AiSuggestion).where(AiSuggestion.request_id == request_id))
        assert saved.model == "google:test"

    def test_an_edited_complaint_gets_a_new_draft(self, client, db_session, customer, admin, no_kb_match, fake_draft):
        from app.models import ServiceRequest

        request_id = raise_request(client, customer, admin)
        client.get(f"/api/requests/{request_id}/suggestions")
        db_session.get(ServiceRequest, request_id).description = "Washing machine won't drain"
        db_session.commit()

        response = client.get(f"/api/requests/{request_id}/suggestions")

        assert response.json()[0]["issue_pattern"] == "Washing machine won't drain"
        assert [call[0] for call in fake_draft] == [
            "AC clicks and blinks, no cooling",
            "Washing machine won't drain",
        ]
        assert len(db_session.scalars(select(AiSuggestion)).all()) == 1

    def test_the_equipment_is_sent_with_the_complaint(self, client, customer, admin, no_kb_match, fake_draft):
        log_in(client, customer.email)
        equipment_id = client.post("/api/equipment", json={"name": "Bedroom AC", "type": "Split AC"}).json()["id"]
        request_id = raise_request(client, customer, admin, equipment_id=equipment_id)

        client.get(f"/api/requests/{request_id}/suggestions")

        assert fake_draft[0][1] == "Split AC (Bedroom AC)"

    def test_a_kb_match_wins_and_the_model_is_not_called(self, client, customer, admin, monkeypatch, fake_draft):
        from types import SimpleNamespace

        from app.routes import service_requests

        entry = SimpleNamespace(equipment_type="AC", issue_pattern="no cooling", suggested_fix="Clean the filter.")
        monkeypatch.setattr(service_requests, "suggest_fixes", lambda db, description, *, shop_id, limit=3: [(entry, 0.8)])
        request_id = raise_request(client, customer, admin)

        response = client.get(f"/api/requests/{request_id}/suggestions")

        assert response.json()[0]["source"] == "knowledge_base"
        assert fake_draft == []

    def test_without_a_key_nothing_is_generated(self, client, customer, admin, no_kb_match, monkeypatch):
        monkeypatch.setattr(ai_fallback, "draft_fix", lambda *args: pytest.fail("called without a key"))
        request_id = raise_request(client, customer, admin)

        assert client.get(f"/api/requests/{request_id}/suggestions").json() == []

    def test_a_failed_draft_returns_nothing_and_saves_nothing(self, client, db_session, customer, admin, no_kb_match, key, monkeypatch):
        monkeypatch.setattr(ai_fallback, "draft_fix", lambda description, equipment=None, **kw: None)
        request_id = raise_request(client, customer, admin)

        assert client.get(f"/api/requests/{request_id}/suggestions").json() == []
        assert db_session.scalars(select(AiSuggestion)).all() == []


class TestBeforeSubmitting:
    def test_staff_get_an_ai_draft(self, client, technician, no_kb_match, fake_draft):
        log_in(client, technician.email)

        response = client.post("/api/requests/suggestions", json={"description": "fridge is too warm"})

        assert response.json()[0]["source"] == "ai"
        assert fake_draft == [("fridge is too warm", None, False)]

    def test_customers_get_the_customer_safe_draft(self, client, customer, no_kb_match, fake_draft):
        log_in(client, customer.email)

        response = client.post("/api/requests/suggestions", json={"description": "fridge is too warm"})

        assert response.json()[0]["source"] == "ai"
        assert fake_draft == [("fridge is too warm", None, True)]


def fake_gemini(handler):
    """Points app.ml.gemini's HTTP client at `handler` instead of Google."""
    return httpx.Client(transport=httpx.MockTransport(handler))


def reply(text, status=200):
    return httpx.Response(status, json={"candidates": [{"content": {"parts": [{"text": text}]}}]})


class TestDraftFix:
    @pytest.fixture(autouse=True)
    def _key(self, key):
        pass

    def test_returns_the_model_s_text(self, monkeypatch):
        seen = {}

        def handler(request):
            seen["key"] = request.headers["x-goog-api-key"]
            seen["url"] = str(request.url)
            seen["body"] = request.content.decode()
            return reply("  1. Switch off the power.  ")

        monkeypatch.setattr(gemini, "_client", lambda: fake_gemini(handler))

        draft = ai_fallback.draft_fix("no cooling", "Split AC (Hall)")

        assert draft == AiDraft(text="1. Switch off the power.", model="google:gemini-3.5-flash-lite")
        assert seen["key"] == "test-key"
        assert "gemini-3.5-flash-lite:generateContent" in seen["url"]
        assert "Equipment: Split AC (Hall)" in seen["body"]

    @pytest.mark.parametrize(
        "handler",
        [
            lambda request: httpx.Response(429, json={"error": {"message": "quota"}}),
            lambda request: httpx.Response(200, json={"candidates": []}),
            lambda request: reply("NO_SUGGESTION"),
            lambda request: reply("   "),
        ],
        ids=["http-error", "blocked", "not-a-fault", "empty"],
    )
    def test_anything_unusable_returns_none(self, monkeypatch, handler):
        monkeypatch.setattr(gemini, "_client", lambda: fake_gemini(handler))

        assert ai_fallback.draft_fix("no cooling") is None

    @pytest.mark.parametrize("for_customer, expected", [(False, "help technicians"), (True, "help customers")])
    def test_customers_and_staff_get_different_instructions(self, monkeypatch, for_customer, expected):
        seen = {}

        def handler(request):
            seen["body"] = request.content.decode()
            return reply("1. Check the plug.")

        monkeypatch.setattr(gemini, "_client", lambda: fake_gemini(handler))

        ai_fallback.draft_fix("no cooling", for_customer=for_customer)

        assert expected in seen["body"]

    def test_a_timeout_returns_none(self, monkeypatch):
        def handler(request):
            raise httpx.ReadTimeout("too slow", request=request)

        monkeypatch.setattr(gemini, "_client", lambda: fake_gemini(handler))

        assert ai_fallback.draft_fix("no cooling") is None

    def test_no_key_means_no_call(self, monkeypatch):
        monkeypatch.setattr(get_settings(), "gemini_api_key", "")
        monkeypatch.setattr(gemini, "_client", lambda: pytest.fail("called without a key"))

        assert ai_fallback.draft_fix("no cooling") is None
