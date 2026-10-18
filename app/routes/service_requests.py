"""Service requests: a customer's complaint, from submission through to resolution.

Status moves forward only: Open -> In Progress -> Resolved. Every change — including the
request's creation — is written to request_status_log, which is what slide 6 of the
presentation and the status-history requirement describe.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.deps import require_role
from app.ml.failure import attach_latest_risk
from app.ml.troubleshooting import suggest_fixes
from app.ml.urgency import predict_urgency
from app.models import (
    ComplaintCategory,
    Customer,
    Equipment,
    KnowledgeBaseEntry,
    Notification,
    RequestStatus,
    RequestStatusLog,
    Role,
    ServiceRequest,
    Technician,
    User,
)
from app.schemas import (
    ComplaintCategoryOut,
    RequestUpdateIn,
    ServiceRequestIn,
    ServiceRequestOut,
    SuggestionIn,
    SuggestionOut,
    TechnicianSummary,
)

router = APIRouter(prefix="/api/requests", tags=["requests"])

# Forward-only: a status can only move to something with a higher rank than it already has.
_STATUS_RANK = {RequestStatus.OPEN: 0, RequestStatus.IN_PROGRESS: 1, RequestStatus.RESOLVED: 2}

_WITH_RELATED = (
    # Customer.name and Technician.name both read through .user — load it eagerly so
    # serialising a whole list of requests doesn't issue one lazy query per row.
    joinedload(ServiceRequest.customer).joinedload(Customer.user),
    joinedload(ServiceRequest.equipment),
    joinedload(ServiceRequest.category),
    joinedload(ServiceRequest.technician).joinedload(Technician.user),
)


def _notify(db: Session, user_id: int, message: str, link: str | None = None) -> None:
    db.add(Notification(user_id=user_id, message=message, link=link))


def _with_equipment_risk(requests: list[ServiceRequest], db: Session) -> list[ServiceRequest]:
    attach_latest_risk(db, [request.equipment for request in requests if request.equipment])
    return requests


@router.post("", response_model=ServiceRequestOut, status_code=201)
def create_request(
    body: ServiceRequestIn, user: User = Depends(require_role(Role.CUSTOMER)), db: Session = Depends(get_db)
):
    description = body.description.strip()
    if not description:
        raise HTTPException(status_code=400, detail="Describe the problem.")

    equipment_id = None
    if body.equipment_id is not None:
        equipment = db.get(Equipment, body.equipment_id)
        if equipment is None or equipment.customer_id != user.customer.id:
            raise HTTPException(status_code=400, detail="Select one of your own registered equipment.")
        equipment_id = equipment.id

    category_id = None
    if body.category_id is not None:
        if db.get(ComplaintCategory, body.category_id) is None:
            raise HTTPException(status_code=400, detail="Select a valid category.")
        category_id = body.category_id

    # Asked once: if this customer has never given a service address, this complaint is
    # where we collect it, and it's then on file for every request after this one.
    if not user.customer.address:
        address = (body.address or "").strip()
        if not address:
            raise HTTPException(status_code=400, detail="Enter your service address.")
        user.customer.address = address

    request = ServiceRequest(
        customer_id=user.customer.id,
        equipment_id=equipment_id,
        category_id=category_id,
        description=description,
        urgency=predict_urgency(description),
    )
    db.add(request)
    db.flush()  # Assigns request.id for the status log row below, before the single commit.
    db.add(RequestStatusLog(request_id=request.id, old_status=None, new_status=RequestStatus.OPEN, changed_by=user.id))
    db.commit()

    created = db.scalar(select(ServiceRequest).options(*_WITH_RELATED).where(ServiceRequest.id == request.id))
    return _with_equipment_risk([created], db)[0]


@router.get("/mine", response_model=list[ServiceRequestOut])
def list_my_requests(user: User = Depends(require_role(Role.CUSTOMER)), db: Session = Depends(get_db)):
    requests = db.scalars(
        select(ServiceRequest)
        .options(*_WITH_RELATED)
        .where(ServiceRequest.customer_id == user.customer.id)
        .order_by(ServiceRequest.created_at.desc(), ServiceRequest.id.desc())
    ).all()
    return _with_equipment_risk(requests, db)


@router.get("/assigned", response_model=list[ServiceRequestOut])
def list_assigned_requests(user: User = Depends(require_role(Role.TECHNICIAN)), db: Session = Depends(get_db)):
    requests = db.scalars(
        select(ServiceRequest)
        .options(*_WITH_RELATED)
        .where(ServiceRequest.technician_id == user.technician.id)
        # False (not resolved) sorts before True (resolved) ascending, so active jobs come first.
        .order_by(
            ServiceRequest.status == RequestStatus.RESOLVED,
            ServiceRequest.created_at.desc(),
            ServiceRequest.id.desc(),
        )
    ).all()
    return _with_equipment_risk(requests, db)


@router.get("", response_model=list[ServiceRequestOut])
def list_all_requests(_user: User = Depends(require_role(Role.ADMIN)), db: Session = Depends(get_db)):
    requests = db.scalars(
        select(ServiceRequest).options(*_WITH_RELATED).order_by(ServiceRequest.created_at.desc(), ServiceRequest.id.desc())
    ).all()
    return _with_equipment_risk(requests, db)


@router.get("/technicians", response_model=list[TechnicianSummary])
def list_technicians_for_assignment(_user: User = Depends(require_role(Role.ADMIN)), db: Session = Depends(get_db)):
    return db.scalars(select(Technician).join(User).where(User.is_active).order_by(User.name)).all()


@router.get("/categories", response_model=list[ComplaintCategoryOut])
def list_categories(_user: User = Depends(require_role(Role.CUSTOMER, Role.ADMIN)), db: Session = Depends(get_db)):
    return db.scalars(select(ComplaintCategory).order_by(ComplaintCategory.category_name)).all()


def _serialize_suggestions(matches: list[tuple[KnowledgeBaseEntry, float]]) -> list[SuggestionOut]:
    return [
        SuggestionOut(
            equipment_type=entry.equipment_type,
            issue_pattern=entry.issue_pattern,
            suggested_fix=entry.suggested_fix,
            similarity=similarity,
        )
        for entry, similarity in matches
    ]


@router.post("/suggestions", response_model=list[SuggestionOut])
def suggest_for_description(
    body: SuggestionIn, _user: User = Depends(require_role(Role.CUSTOMER)), db: Session = Depends(get_db)
):
    """Tried before a request is even submitted, so a customer can attempt an easy fix
    themselves — see the "Check for a quick fix" button on the new-complaint form."""
    return _serialize_suggestions(suggest_fixes(db, body.description))


@router.get("/{request_id}/suggestions", response_model=list[SuggestionOut])
def suggest_for_request(
    request_id: int, user: User = Depends(require_role(Role.ADMIN, Role.TECHNICIAN)), db: Session = Depends(get_db)
):
    request = db.get(ServiceRequest, request_id)
    if request is None:
        raise HTTPException(status_code=404, detail="That service request doesn't exist.")
    if user.role == Role.TECHNICIAN and request.technician_id != user.technician.id:
        raise HTTPException(status_code=403, detail="This request isn't assigned to you.")
    return _serialize_suggestions(suggest_fixes(db, request.description))


@router.patch("/{request_id}", response_model=ServiceRequestOut)
def update_request(
    request_id: int,
    body: RequestUpdateIn,
    user: User = Depends(require_role(Role.ADMIN, Role.TECHNICIAN)),
    db: Session = Depends(get_db),
):
    request = db.scalar(select(ServiceRequest).options(*_WITH_RELATED).where(ServiceRequest.id == request_id))
    if request is None:
        raise HTTPException(status_code=404, detail="That service request doesn't exist.")
    if body.technician_id is None and body.status is None:
        raise HTTPException(status_code=400, detail="Nothing to update.")

    if body.technician_id is not None:
        if user.role != Role.ADMIN:
            raise HTTPException(status_code=403, detail="Only an admin can assign a technician.")
        technician = db.get(Technician, body.technician_id)
        if technician is None:
            raise HTTPException(status_code=400, detail="Select a valid technician.")
        # Assigning the related object, not just technician_id, so the .technician relationship
        # this same request already loaded above reflects the change immediately — setting only
        # the FK column leaves that in-memory relationship pointing at the old value.
        request.technician = technician
        _notify(db, technician.user_id, f"You've been assigned request #{request.id}.", link="/technician")
        _notify(db, request.customer.user_id, f"A technician has been assigned to request #{request.id}.")
        # Assigning someone is the start of work; an admin can still set status explicitly below.
        if request.status == RequestStatus.OPEN and body.status is None:
            _transition(db, request, RequestStatus.IN_PROGRESS, user)

    if body.status is not None:
        if user.role == Role.TECHNICIAN and request.technician_id != user.technician.id:
            raise HTTPException(status_code=403, detail="This request isn't assigned to you.")
        if body.status not in _STATUS_RANK:
            raise HTTPException(status_code=400, detail="That isn't a valid status.")
        if _STATUS_RANK[body.status] < _STATUS_RANK[RequestStatus(request.status)]:
            raise HTTPException(status_code=400, detail="A request's status can't move backwards.")
        if body.status != request.status:
            _transition(db, request, RequestStatus(body.status), user)

    db.commit()
    return _with_equipment_risk([request], db)[0]


def _transition(db: Session, request: ServiceRequest, new_status: RequestStatus, actor: User) -> None:
    db.add(
        RequestStatusLog(
            request_id=request.id, old_status=request.status, new_status=new_status, changed_by=actor.id
        )
    )
    request.status = new_status
    _notify(db, request.customer.user_id, f"Request #{request.id} is now {new_status.value.replace('_', ' ')}.")
