"""The real _load_model functions: a missing or unreadable model file must give None (so callers
fall back to a safe default) rather than crash a request. Other tests stub _load_model out."""

import pytest

from app.ml import failure, urgency
from app.models import RiskLevel, Urgency

MODULES = [urgency, failure]


@pytest.fixture(autouse=True)
def fresh_cache():
    for module in MODULES:
        module._load_model.cache_clear()
    yield
    for module in MODULES:
        module._load_model.cache_clear()


@pytest.mark.parametrize("module", MODULES)
def test_missing_model_file_loads_as_none(module, monkeypatch, tmp_path):
    monkeypatch.setattr(module, "MODEL_PATH", tmp_path / "absent.joblib")

    assert module._load_model() is None


@pytest.mark.parametrize("module", MODULES)
def test_corrupt_model_file_loads_as_none(module, monkeypatch, tmp_path):
    corrupt = tmp_path / "corrupt.joblib"
    corrupt.write_bytes(b"not a joblib file")
    monkeypatch.setattr(module, "MODEL_PATH", corrupt)

    assert module._load_model() is None


def test_corrupt_model_still_gives_safe_defaults(monkeypatch, tmp_path):
    corrupt = tmp_path / "corrupt.joblib"
    corrupt.write_bytes(b"not a joblib file")
    monkeypatch.setattr(urgency, "MODEL_PATH", corrupt)
    monkeypatch.setattr(failure, "MODEL_PATH", corrupt)

    assert urgency.predict_urgency("the pump is leaking") == Urgency.MEDIUM
    assert failure.predict_risk(object()) == (RiskLevel.MODERATE, 0.5)
