import numpy as np
import pytest
from sqlalchemy import delete

from app.ml import troubleshooting
from tests.conftest import DEFAULT_SHOP_ID
from app.models import ComplaintCategory, KnowledgeBaseEntry


class FakeModel:
    """Deterministic stand-in for the real sentence-transformer: known phrases map to fixed
    vectors (a paraphrase landing close to the phrase it means the same as), anything else maps
    to the zero vector, so it never accidentally matches anything. This tests suggest_fixes'
    ranking and threshold logic without downloading or running a real model."""

    VECTORS = {
        "the pump is leaking water": np.array([1.0, 0.0, 0.0]),
        "water is dripping from the pump": np.array([0.9, 0.1, 0.0]),
        "completely unrelated electrical fault": np.array([0.0, 0.0, 1.0]),
    }

    def encode(self, texts, normalize_embeddings=True):
        vectors = np.array([self.VECTORS.get(text, np.zeros(3)) for text in texts])
        if normalize_embeddings:
            norms = np.linalg.norm(vectors, axis=1, keepdims=True)
            vectors = vectors / np.where(norms == 0, 1, norms)
        return vectors


@pytest.fixture(autouse=True)
def fake_model(monkeypatch):
    troubleshooting._corpus_cache.clear()
    monkeypatch.setattr(troubleshooting, "_model", lambda: FakeModel())
    yield
    troubleshooting._corpus_cache.clear()


@pytest.fixture
def category(db_session):
    # Seeded categories already exist (see the seed_complaint_categories migration); a fresh one
    # keeps this test independent of that seed data.
    category = ComplaintCategory(category_name="Test category", urgency_level="medium")
    db_session.add(category)
    db_session.commit()
    return category


@pytest.fixture
def clean_kb(db_session):
    # The seed_knowledge_base migration already populated this table; clearing it keeps these
    # tests about the matching logic, not about which real entries happen to exist.
    db_session.execute(delete(KnowledgeBaseEntry))
    db_session.commit()


def test_matches_by_meaning_not_exact_wording(db_session, category, clean_kb):
    db_session.add(
        KnowledgeBaseEntry(shop_id=DEFAULT_SHOP_ID, category_id=category.id, issue_pattern="the pump is leaking water", suggested_fix="Tighten the fitting.")
    )
    db_session.commit()

    matches = troubleshooting.suggest_fixes(db_session, "water is dripping from the pump", shop_id=DEFAULT_SHOP_ID)

    assert len(matches) == 1
    entry, score = matches[0]
    assert entry.suggested_fix == "Tighten the fitting."
    assert score > troubleshooting.MIN_SIMILARITY


def test_nothing_below_the_similarity_threshold_is_returned(db_session, category, clean_kb):
    db_session.add(
        KnowledgeBaseEntry(shop_id=DEFAULT_SHOP_ID, category_id=category.id, issue_pattern="the pump is leaking water", suggested_fix="Tighten the fitting.")
    )
    db_session.commit()

    assert troubleshooting.suggest_fixes(db_session, "completely unrelated electrical fault", shop_id=DEFAULT_SHOP_ID) == []


def test_empty_knowledge_base_returns_no_suggestions(db_session, clean_kb):
    assert troubleshooting.suggest_fixes(db_session, "anything at all", shop_id=DEFAULT_SHOP_ID) == []


def test_limit_caps_the_number_of_matches(db_session, category, clean_kb):
    for _ in range(5):
        db_session.add(
            KnowledgeBaseEntry(shop_id=DEFAULT_SHOP_ID, category_id=category.id, issue_pattern="the pump is leaking water", suggested_fix="Tighten the fitting.")
        )
    db_session.commit()

    assert len(troubleshooting.suggest_fixes(db_session, "the pump is leaking water", shop_id=DEFAULT_SHOP_ID, limit=2)) == 2


def test_a_broken_model_fails_closed_instead_of_raising(db_session, category, clean_kb, monkeypatch):
    db_session.add(
        KnowledgeBaseEntry(shop_id=DEFAULT_SHOP_ID, category_id=category.id, issue_pattern="the pump is leaking water", suggested_fix="Tighten the fitting.")
    )
    db_session.commit()

    def _raise():
        raise RuntimeError("model unavailable")

    monkeypatch.setattr(troubleshooting, "_model", _raise)

    assert troubleshooting.suggest_fixes(db_session, "the pump is leaking water", shop_id=DEFAULT_SHOP_ID) == []
