from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import select

from app.models import (
    ComplaintCategory,
    Equipment,
    PredictionLog,
    RequestStatus,
    RequestStatusLog,
    Role,
    ServiceRequest,
)
from tests.conftest import log_in

NOW = datetime.now(UTC)


@pytest.fixture
def admin(make_user):
    return make_user(Role.ADMIN)


@pytest.fixture
def customer(make_user):
    return make_user(Role.CUSTOMER, email=None)


def add_request(db, customer, *, created, resolved=None, technician=None, urgency="medium", category=None):
    request = ServiceRequest(
        customer_id=customer.customer.id,
        description="Leaking pump",
        urgency=urgency,
        status=RequestStatus.RESOLVED if resolved else RequestStatus.IN_PROGRESS if technician else RequestStatus.OPEN,
        technician_id=technician.technician.id if technician else None,
        category_id=category.id if category else None,
        created_at=created,
    )
    db.add(request)
    db.flush()
    db.add(RequestStatusLog(request_id=request.id, new_status=RequestStatus.OPEN, changed_at=created))
    if resolved:
        db.add(
            RequestStatusLog(
                request_id=request.id,
                old_status=RequestStatus.IN_PROGRESS,
                new_status=RequestStatus.RESOLVED,
                changed_at=resolved,
            )
        )
    db.commit()
    return request


def get_analytics(client, admin):
    log_in(client, admin.email)
    response = client.get("/api/analytics")
    assert response.status_code == 200
    return response.json()


@pytest.mark.parametrize("role", [Role.CUSTOMER, Role.TECHNICIAN])
def test_only_admins_can_see_analytics(client, make_user, role):
    user = make_user(role)
    log_in(client, user.email or user.customer.phone)

    assert client.get("/api/analytics").status_code == 403


def test_empty_system_gives_zeroes_not_errors(client, admin):
    data = get_analytics(client, admin)

    assert data["days"] == 30
    assert len(data["daily"]) == 30
    assert data["daily"][-1]["date"] == NOW.date().isoformat()
    assert all(day["created"] == 0 and day["resolved"] == 0 for day in data["daily"])
    assert data["by_status"] == [
        {"name": "open", "count": 0},
        {"name": "in_progress", "count": 0},
        {"name": "resolved", "count": 0},
    ]
    assert data["by_category"] == []
    assert data["technicians"] == []
    assert data["avg_resolution_hours"] is None


def test_counts_requests_by_status_urgency_and_category(client, db_session, admin, customer, make_user):
    technician = make_user(Role.TECHNICIAN)
    plumbing, electrical = db_session.scalars(select(ComplaintCategory).order_by(ComplaintCategory.id).limit(2)).all()
    add_request(db_session, customer, created=NOW, urgency="high", category=plumbing)
    add_request(db_session, customer, created=NOW, urgency="high", category=plumbing, technician=technician)
    add_request(db_session, customer, created=NOW, urgency="low", category=electrical, technician=technician,
                resolved=NOW)
    add_request(db_session, customer, created=NOW)

    data = get_analytics(client, admin)

    assert {item["name"]: item["count"] for item in data["by_status"]} == {"open": 2, "in_progress": 1, "resolved": 1}
    assert data["by_urgency"] == [
        {"name": "low", "count": 1},
        {"name": "medium", "count": 1},
        {"name": "high", "count": 2},
    ]
    # Most common first; a request with no category is still counted.
    assert data["by_category"][0] == {"name": plumbing.category_name, "count": 2}
    assert {item["name"] for item in data["by_category"][1:]} == {electrical.category_name, "Uncategorised"}


def test_daily_trend_covers_the_last_30_days_only(client, db_session, admin, customer):
    add_request(db_session, customer, created=NOW - timedelta(days=2), resolved=NOW)
    add_request(db_session, customer, created=NOW - timedelta(days=2))
    add_request(db_session, customer, created=NOW - timedelta(days=45))

    daily = {day["date"]: day for day in get_analytics(client, admin)["daily"]}

    two_days_ago = (NOW - timedelta(days=2)).date().isoformat()
    assert daily[two_days_ago]["created"] == 2
    assert daily[NOW.date().isoformat()]["resolved"] == 1
    assert sum(day["created"] for day in daily.values()) == 2


def test_resolution_time_and_technician_workload(client, db_session, admin, customer, make_user):
    busy = make_user(Role.TECHNICIAN, email="busy@example.com", name="Busy Tech")
    idle = make_user(Role.TECHNICIAN, email="idle@example.com", name="Idle Tech")
    gone = make_user(Role.TECHNICIAN, email="gone@example.com", name="Gone Tech")
    gone.is_active = False
    add_request(db_session, customer, created=NOW - timedelta(hours=4), resolved=NOW, technician=busy)
    add_request(db_session, customer, created=NOW - timedelta(hours=2), resolved=NOW, technician=busy)
    add_request(db_session, customer, created=NOW, technician=busy)

    data = get_analytics(client, admin)

    assert data["avg_resolution_hours"] == 3.0
    # Deactivated technicians with no jobs are left out; idle active ones are listed.
    assert [(t["name"], t["active"], t["resolved"], t["avg_resolution_hours"]) for t in data["technicians"]] == [
        ("Busy Tech", 1, 2, 3.0),
        ("Idle Tech", 0, 0, None),
    ]
    assert idle.technician.id in {t["id"] for t in data["technicians"]}


def test_equipment_risk_uses_each_item_s_latest_prediction(client, db_session, admin, customer):
    pump, lathe, new = (
        Equipment(customer_id=customer.customer.id, name=name, type="Pump") for name in ("Pump", "Lathe", "New")
    )
    db_session.add_all([pump, lathe, new])
    db_session.flush()
    db_session.add_all(
        [
            PredictionLog(equipment_id=pump.id, risk_score=0.9, risk_level="critical"),
            PredictionLog(equipment_id=pump.id, risk_score=0.01, risk_level="good"),
            PredictionLog(equipment_id=lathe.id, risk_score=0.3, risk_level="critical"),
        ]
    )
    db_session.commit()

    risk = {item["name"]: item["count"] for item in get_analytics(client, admin)["equipment_risk"]}

    assert risk == {"good": 1, "moderate": 0, "critical": 1, "unscored": 1}
