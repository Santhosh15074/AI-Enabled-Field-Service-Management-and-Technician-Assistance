from types import SimpleNamespace

import numpy as np
import pytest

from app.ml import failure
from app.models import RiskLevel


class FakeModel:
    """Deterministic stand-in: failure probability is just tool wear scaled to 0-1, so tests can
    reason about it without depending on the real trained model's exact output."""

    def predict_proba(self, df):
        wear = df["tool_wear_min"].iloc[0]
        p = min(wear / 300, 1.0)
        return np.array([[1 - p, p]])


@pytest.fixture(autouse=True)
def fake_model(monkeypatch):
    failure._load_model.cache_clear()
    monkeypatch.setattr(failure, "_load_model", lambda: FakeModel())


def equipment(tool_wear_min=0.0):
    return SimpleNamespace(
        quality_grade="L",
        air_temperature_k=298.0,
        process_temperature_k=308.0,
        rotational_speed_rpm=1500,
        torque_nm=40.0,
        tool_wear_min=tool_wear_min,
    )


def test_low_wear_is_good():
    level, score = failure.predict_risk(equipment(tool_wear_min=0))

    assert level == RiskLevel.GOOD
    assert score < failure.MODERATE_AT


def test_mid_wear_is_moderate():
    level, _ = failure.predict_risk(equipment(tool_wear_min=60))

    assert level == RiskLevel.MODERATE


def test_high_wear_is_critical():
    level, score = failure.predict_risk(equipment(tool_wear_min=280))

    assert level == RiskLevel.CRITICAL
    assert score >= failure.CRITICAL_AT


def test_falls_back_to_moderate_when_no_model_is_on_disk(monkeypatch):
    monkeypatch.setattr(failure, "_load_model", lambda: None)

    level, score = failure.predict_risk(equipment())

    assert level == RiskLevel.MODERATE
    assert score == 0.5


def test_falls_back_to_moderate_if_prediction_raises(monkeypatch):
    class Broken:
        def predict_proba(self, df):
            raise RuntimeError("boom")

    monkeypatch.setattr(failure, "_load_model", lambda: Broken())

    level, score = failure.predict_risk(equipment())

    assert level == RiskLevel.MODERATE
    assert score == 0.5


class TestAttachLatestRisk:
    @pytest.fixture
    def customer_equipment(self, db_session, make_user):
        from app.models import Equipment, Role

        customer = make_user(Role.CUSTOMER)
        item = Equipment(customer_id=customer.customer.id, name="Lathe #1", type="Lathe")
        db_session.add(item)
        db_session.commit()
        return item

    def test_equipment_with_no_predictions_gets_none(self, db_session, customer_equipment):
        failure.attach_latest_risk(db_session, [customer_equipment])

        assert customer_equipment.risk_level is None
        assert customer_equipment.risk_score is None

    def test_uses_the_most_recent_prediction(self, db_session, customer_equipment):
        from app.models import PredictionLog

        db_session.add(PredictionLog(equipment_id=customer_equipment.id, risk_score=0.1, risk_level=RiskLevel.GOOD))
        db_session.add(PredictionLog(equipment_id=customer_equipment.id, risk_score=0.9, risk_level=RiskLevel.CRITICAL))
        db_session.commit()

        failure.attach_latest_risk(db_session, [customer_equipment])

        assert customer_equipment.risk_level == RiskLevel.CRITICAL
        assert customer_equipment.risk_score == 0.9

    def test_empty_list_does_not_error(self, db_session):
        failure.attach_latest_risk(db_session, [])
