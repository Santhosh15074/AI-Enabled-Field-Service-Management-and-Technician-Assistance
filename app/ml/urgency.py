"""Predicts how urgently a service request needs a response, from its description alone.

Trained on real customer-support ticket text; see ml/train_urgency_classifier.py for how and
ml/models/.gitkeep for why the trained file itself isn't committed. Without it on disk — a fresh
clone that hasn't run the training script yet — every request is treated as medium urgency rather
than failing to save at all.
"""

import logging
from functools import lru_cache
from pathlib import Path

import joblib

from app.models import Urgency

logger = logging.getLogger(__name__)

MODEL_PATH = Path(__file__).resolve().parent.parent.parent / "ml" / "models" / "urgency_classifier.joblib"


@lru_cache(maxsize=1)
def _load_model():
    if not MODEL_PATH.exists():
        logger.warning("No urgency classifier at %s; defaulting every request to medium urgency.", MODEL_PATH)
        return None
    try:
        return joblib.load(MODEL_PATH)
    except Exception:
        logger.exception("Failed to load the urgency classifier at %s", MODEL_PATH)
        return None


def predict_urgency(description: str) -> Urgency:
    model = _load_model()
    if model is None:
        return Urgency.MEDIUM
    try:
        return Urgency(model.predict([description])[0])
    except Exception:
        logger.exception("Urgency prediction failed; defaulting to medium.")
        return Urgency.MEDIUM
