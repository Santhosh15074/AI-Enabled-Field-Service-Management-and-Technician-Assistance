"""Headline numbers for each role's dashboard."""

from fastapi import APIRouter, Depends
from sqlalchemy import distinct, func, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import require_role
from app.models import (
    Customer,
    Equipment,
    PredictionLog,
    RequestStatus,
    RiskLevel,
    Role,
    ServiceRequest,
    Technician,
    User,
)
from app.schemas import AdminOverview, CustomerOverview, TechnicianOverview
from app.shops import customer_ids, equipment_ids, technician_ids

router = APIRouter(prefix="/api/overview", tags=["overview"])

UNRESOLVED = (RequestStatus.OPEN, RequestStatus.IN_PROGRESS)


def _count(db: Session, query) -> int:
    return db.scalar(query) or 0


@router.get("/admin", response_model=AdminOverview)
def admin_overview(user: User = Depends(require_role(Role.ADMIN)), db: Session = Depends(get_db)):
    latest_prediction = (
        select(PredictionLog.equipment_id, func.max(PredictionLog.id).label("id"))
        .where(PredictionLog.equipment_id.in_(equipment_ids(user.shop_id)))
        .group_by(PredictionLog.equipment_id)
        .subquery()
    )
    return AdminOverview(
        customers=_count(db, select(func.count(Customer.id)).where(Customer.id.in_(customer_ids(user.shop_id)))),
        technicians=_count(db, select(func.count(Technician.id)).where(Technician.id.in_(technician_ids(user.shop_id)))),
        open_requests=_count(
            db,
            select(func.count(ServiceRequest.id)).where(
                ServiceRequest.status.in_(UNRESOLVED), ServiceRequest.customer_id.in_(customer_ids(user.shop_id))
            ),
        ),
        critical_equipment=_count(
            db,
            select(func.count(distinct(PredictionLog.equipment_id)))
            .join(latest_prediction, PredictionLog.id == latest_prediction.c.id)
            .where(PredictionLog.risk_level == RiskLevel.CRITICAL),
        ),
    )


@router.get("/customer", response_model=CustomerOverview)
def customer_overview(user: User = Depends(require_role(Role.CUSTOMER)), db: Session = Depends(get_db)):
    customer_id = user.customer.id
    requests = select(func.count(ServiceRequest.id)).where(ServiceRequest.customer_id == customer_id)
    return CustomerOverview(
        equipment=_count(db, select(func.count(Equipment.id)).where(Equipment.customer_id == customer_id)),
        open_requests=_count(db, requests.where(ServiceRequest.status.in_(UNRESOLVED))),
        resolved_requests=_count(db, requests.where(ServiceRequest.status == RequestStatus.RESOLVED)),
    )


@router.get("/technician", response_model=TechnicianOverview)
def technician_overview(
    user: User = Depends(require_role(Role.TECHNICIAN)), db: Session = Depends(get_db)
):
    jobs = select(func.count(ServiceRequest.id)).where(ServiceRequest.technician_id == user.technician.id)
    return TechnicianOverview(
        assigned=_count(db, jobs.where(ServiceRequest.status == RequestStatus.OPEN)),
        in_progress=_count(db, jobs.where(ServiceRequest.status == RequestStatus.IN_PROGRESS)),
        resolved=_count(db, jobs.where(ServiceRequest.status == RequestStatus.RESOLVED)),
    )
