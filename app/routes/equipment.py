"""A customer's own equipment. Registering equipment is what service requests get attached to,
and what a technician records sensor readings against — see record_readings, which is what the
failure-prediction model (Phase 6) actually scores.
"""

from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from sqlalchemy.orm import joinedload

from app.database import get_db
from app.deps import require_role
from app.ml.failure import attach_latest_risk, predict_risk
from app.models import Customer, Equipment, PredictionLog, RiskLevel, Role, ServiceRequest, User
from app.schemas import AdminEquipmentOut, EquipmentIn, EquipmentOut, EquipmentReadingsIn
from app.shops import customer_ids, not_found_outside_shop

router = APIRouter(prefix="/api/equipment", tags=["equipment"])

QUALITY_GRADES = {"L", "M", "H"}

# Worst first: a fleet-risk view is only useful if the things most worth looking at are on top.
_RISK_RANK = {RiskLevel.CRITICAL: 0, RiskLevel.MODERATE: 1, RiskLevel.GOOD: 2, None: 3}


@router.get("", response_model=list[EquipmentOut])
def list_my_equipment(user: User = Depends(require_role(Role.CUSTOMER)), db: Session = Depends(get_db)):
    equipment = db.scalars(
        select(Equipment).where(Equipment.customer_id == user.customer.id).order_by(Equipment.id.desc())
    ).all()
    attach_latest_risk(db, equipment)
    return equipment


@router.get("/all", response_model=list[AdminEquipmentOut])
def list_all_equipment(user: User = Depends(require_role(Role.ADMIN)), db: Session = Depends(get_db)):
    """Every customer's equipment, worst risk first — the fleet-wide view behind "Failure
    predictions" on the admin sidebar. list_my_equipment is the customer's own, narrower one."""
    equipment = db.scalars(
        select(Equipment)
        .options(joinedload(Equipment.customer).joinedload(Customer.user))
        .where(Equipment.customer_id.in_(customer_ids(user.shop_id)))
        .order_by(Equipment.id.desc())
    ).all()
    attach_latest_risk(db, equipment)
    return sorted(equipment, key=lambda item: _RISK_RANK[item.risk_level])


@router.post("", response_model=EquipmentOut, status_code=201)
def register_equipment(
    body: EquipmentIn, user: User = Depends(require_role(Role.CUSTOMER)), db: Session = Depends(get_db)
):
    equipment = Equipment(
        customer_id=user.customer.id,
        name=body.name.strip(),
        type=body.type.strip(),
        serial_number=(body.serial_number or "").strip() or None,
    )
    db.add(equipment)
    db.commit()
    attach_latest_risk(db, [equipment])
    return equipment


@router.patch("/{equipment_id}/readings", response_model=EquipmentOut)
def record_readings(
    equipment_id: int,
    body: EquipmentReadingsIn,
    user: User = Depends(require_role(Role.ADMIN, Role.TECHNICIAN)),
    db: Session = Depends(get_db),
):
    """A technician's on-site reading of a piece of equipment. Scored for failure risk
    immediately — see app.ml.failure.predict_risk — and logged to prediction_log either way, so
    there's a full history to show even when nothing's wrong."""
    equipment = db.get(Equipment, equipment_id)
    if equipment is None:
        raise HTTPException(status_code=404, detail="That equipment doesn't exist.")
    not_found_outside_shop(equipment.customer.user.shop_id, user, "That equipment doesn't exist.")
    if user.role == Role.TECHNICIAN:
        visited = db.scalar(
            select(ServiceRequest.id)
            .where(ServiceRequest.equipment_id == equipment_id, ServiceRequest.technician_id == user.technician.id)
            .limit(1)
        )
        if visited is None:
            raise HTTPException(status_code=403, detail="You haven't been assigned a request for this equipment.")
    if body.quality_grade not in QUALITY_GRADES:
        raise HTTPException(status_code=400, detail="Quality grade must be L, M, or H.")

    equipment.quality_grade = body.quality_grade
    equipment.air_temperature_k = body.air_temperature_k
    equipment.process_temperature_k = body.process_temperature_k
    equipment.rotational_speed_rpm = body.rotational_speed_rpm
    equipment.torque_nm = body.torque_nm
    equipment.tool_wear_min = body.tool_wear_min
    equipment.last_service_date = date.today()
    equipment.usage_count = (equipment.usage_count or 0) + 1
    db.flush()  # equipment's new readings must be visible to predict_risk before it's queried.

    risk_level, risk_score = predict_risk(equipment)
    db.add(PredictionLog(equipment_id=equipment.id, risk_score=risk_score, risk_level=risk_level))
    db.commit()

    attach_latest_risk(db, [equipment])
    return equipment
