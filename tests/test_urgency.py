from app.ml import urgency
from app.models import Urgency


class FakeModel:
    def __init__(self, prediction):
        self.prediction = prediction

    def predict(self, texts):
        return [self.prediction] * len(texts)


class BrokenModel:
    def predict(self, texts):
        raise RuntimeError("boom")


def test_defaults_to_medium_when_no_model_is_on_disk(monkeypatch):
    monkeypatch.setattr(urgency, "_load_model", lambda: None)

    assert urgency.predict_urgency("anything") == Urgency.MEDIUM


def test_uses_the_model_s_prediction(monkeypatch):
    monkeypatch.setattr(urgency, "_load_model", lambda: FakeModel("high"))

    assert urgency.predict_urgency("the compressor is on fire") == Urgency.HIGH


def test_falls_back_to_medium_if_prediction_fails(monkeypatch):
    monkeypatch.setattr(urgency, "_load_model", lambda: BrokenModel())

    assert urgency.predict_urgency("anything") == Urgency.MEDIUM
