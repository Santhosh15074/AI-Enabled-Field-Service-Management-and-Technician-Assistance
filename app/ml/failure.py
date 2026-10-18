"""Scores a piece of equipment's failure risk from its latest sensor readings.

Trained on the AI4I 2020 predictive-maintenance dataset; see ml/train_failure_model.py. Unlike
the urgency and troubleshooting models, there's no domain mismatch here — Equipment's reading
columns exist specifically to match this dataset's (see the comment on Equipment in app.models).

The model outputs a failure probability; MODERATE_AT and CRITICAL_AT turn that into the three
RiskLevel buckets. They're set low on purpose: on the held-out test set, scoring everything above
0.25 as critical catches about three in four real failures at roughly 30% precision, which is the
right trade for maintenance — a false alarm costs an inspection, a missed failure costs the
equipment. See ml/train_failure_model.py's printed precision/recall table if retuning these.
"""

import logging
from functools import lru_cache
from pathlib import Path

import joblib
import pandas as pd
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Equipment, PredictionLog, RiskLevel

logger = logging.getLogger(__name__)

MODEL_PATH = Path(__file__).resolve().parent.parent.parent / "ml" / "models" / "failure_model.joblib"

MODERATE_AT = 0.08
CRITICAL_AT = 0.25

FEATURE_COLUMNS = [
    "quality_grade",
    "air_temperature_k",
    "process_temperature_k",
    "rotational_speed_rpm",
    "torque_nm",
    "tool_wear_min",
]


@lru_cache(maxsize=1)
def _load_model():
    if not MODEL_PATH.exists():
        logger.warning("No failure model at %s; every prediction will fall back to moderate risk.", MODEL_PATH)
        return None
    try:
        return joblib.load(MODEL_PATH)
    except Exception:
        logger.exception("Failed to load the failure model at %s", MODEL_PATH)
        return None


def predict_risk(equipment: Equipment) -> tuple[RiskLevel, float]:
    """(risk_level, risk_score) from equipment's current readings. Falls back to a cautious
    MODERATE — not GOOD — when the model can't run, so a missing model never reads as an
    all-clear."""
    model = _load_model()
    if model is None:
        return RiskLevel.MODERATE, 0.5
    try:
        row = pd.DataFrame([{column: getattr(equipment, column) for column in FEATURE_COLUMNS}])
        score = float(model.predict_proba(row)[0, 1])
    except Exception:
        logger.exception("Failure prediction failed; defaulting to moderate risk.")
        return RiskLevel.MODERATE, 0.5

    if score >= CRITICAL_AT:
        level = RiskLevel.CRITICAL
    elif score >= MODERATE_AT:
        level = RiskLevel.MODERATE
    else:
        level = RiskLevel.GOOD
    return level, score


def attach_latest_risk(db: Session, equipment_list: list[Equipment]) -> None:
    """Sets .risk_level and .risk_score (both None if there's no reading yet) on each item, from
    its most recent PredictionLog row. EquipmentOut reads these as plain attributes, so routes
    call this once before serializing rather than everyone re-deriving it."""
    by_id = {equipment.id: equipment for equipment in equipment_list}
    if not by_id:
        return

    latest_ids = (
        select(func.max(PredictionLog.id))
        .where(PredictionLog.equipment_id.in_(by_id))
        .group_by(PredictionLog.equipment_id)
    )
    latest = db.scalars(select(PredictionLog).where(PredictionLog.id.in_(latest_ids))).all()

    for equipment in equipment_list:
        equipment.risk_level = None
        equipment.risk_score = None
    for log in latest:
        equipment = by_id[log.equipment_id]
        equipment.risk_level = log.risk_level
        equipment.risk_score = log.risk_score
