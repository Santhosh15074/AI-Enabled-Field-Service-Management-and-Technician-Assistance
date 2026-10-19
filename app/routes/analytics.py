"""Figures for the admin analytics page: request trends, workload and equipment risk.

Counts are small (one business's requests), so rows are fetched once and grouped in Python,
which keeps the date bucketing identical on PostgreSQL and the SQLite used by the tests.
"""

from collections import Counter
from datetime import UTC, date, datetime, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.deps import require_role
from app.models import (
    Equipment,
    PredictionLog,
    RequestStatus,
    RequestStatusLog,
    RiskLevel,
    Role,
    ServiceRequest,
    Technician,
    Urgency,
    User,
)
from app.schemas import AnalyticsOut, DailyCount, NamedCount, TechnicianWorkload

router = APIRouter(prefix="/api/analytics", tags=["analytics"])

DAYS = 30
UNSCORED = "unscored"
UNCATEGORISED = "Uncategorised"


def _utc(moment: datetime) -> datetime:
    # SQLite hands timestamps back without a zone; they were stored as UTC.
    return moment if moment.tzinfo else moment.replace(tzinfo=UTC)


def _hours(durations: list[timedelta]) -> float | None:
    if not durations:
        return None
    return round(sum(d.total_seconds() for d in durations) / len(durations) / 3600, 1)


def _in_order(counts: Counter, names) -> list[NamedCount]:
    return [NamedCount(name=name, count=counts[name]) for name in names]


@router.get("", response_model=AnalyticsOut)
def analytics(_user: User = Depends(require_role(Role.ADMIN)), db: Session = Depends(get_db)):
    requests = db.scalars(select(ServiceRequest).options(joinedload(ServiceRequest.category))).all()

    resolved_at = {
        request_id: _utc(changed_at)
        for request_id, changed_at in db.execute(
            select(RequestStatusLog.request_id, func.min(RequestStatusLog.changed_at))
            .where(RequestStatusLog.new_status == RequestStatus.RESOLVED)
            .group_by(RequestStatusLog.request_id)
        )
    }
    resolution_time = {
        request.id: resolved_at[request.id] - _utc(request.created_at)
        for request in requests
        if request.id in resolved_at
    }

    # Daily trend: the last DAYS days up to and including today (UTC), zero-filled.
    today = datetime.now(UTC).date()
    first_day = today - timedelta(days=DAYS - 1)
    created_per_day = Counter(_utc(request.created_at).date() for request in requests)
    resolved_per_day = Counter(moment.date() for moment in resolved_at.values())
    daily = [
        DailyCount(date=day, created=created_per_day[day], resolved=resolved_per_day[day])
        for day in (first_day + timedelta(days=offset) for offset in range(DAYS))
    ]

    category_counts = Counter(
        request.category.category_name if request.category else UNCATEGORISED for request in requests
    )
    by_category = [
        NamedCount(name=name, count=count)
        for name, count in sorted(category_counts.items(), key=lambda item: (-item[1], item[0]))
    ]

    # Each piece of equipment counts once, by its most recent prediction.
    latest_ids = select(func.max(PredictionLog.id)).group_by(PredictionLog.equipment_id)
    risk_counts = Counter(
        db.scalars(select(PredictionLog.risk_level).where(PredictionLog.id.in_(latest_ids))).all()
    )
    risk_counts[UNSCORED] = (db.scalar(select(func.count(Equipment.id))) or 0) - risk_counts.total()

    return AnalyticsOut(
        days=DAYS,
        daily=daily,
        by_status=_in_order(Counter(request.status for request in requests), RequestStatus),
        by_urgency=_in_order(Counter(request.urgency for request in requests), Urgency),
        by_category=by_category,
        equipment_risk=_in_order(risk_counts, [*RiskLevel, UNSCORED]),
        technicians=_workload(db, requests, resolution_time),
        avg_resolution_hours=_hours(list(resolution_time.values())),
    )


def _workload(
    db: Session, requests: list[ServiceRequest], resolution_time: dict[int, timedelta]
) -> list[TechnicianWorkload]:
    """Every active technician, plus any deactivated one who still has requests to their name."""
    by_technician: dict[int, list[ServiceRequest]] = {}
    for request in requests:
        if request.technician_id is not None:
            by_technician.setdefault(request.technician_id, []).append(request)

    technicians = db.scalars(select(Technician).options(joinedload(Technician.user))).all()
    workload = []
    for technician in technicians:
        jobs = by_technician.get(technician.id, [])
        if not jobs and not technician.user.is_active:
            continue
        resolved = [job for job in jobs if job.status == RequestStatus.RESOLVED]
        workload.append(
            TechnicianWorkload(
                id=technician.id,
                name=technician.name,
                active=len(jobs) - len(resolved),
                resolved=len(resolved),
                avg_resolution_hours=_hours([resolution_time[job.id] for job in resolved if job.id in resolution_time]),
            )
        )
    return sorted(workload, key=lambda item: (-item.active, -item.resolved, item.name))
