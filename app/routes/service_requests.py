"""Service requests: a customer's complaint, from submission through to resolution.

Status moves forward only: Open -> In Progress -> Resolved. Every change — including the
request's creation — is written to request_status_log, which is what slide 6 of the
presentation and the status-history requirement describe.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload, selectinload

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
    CustomerChoice,
    RequestUpdateIn,
    ServiceRequestIn,
    ServiceRequestOut,
    SuggestionIn,
    SuggestionOut,
    TechnicianSummary,
)
from app.shops import customer_ids, not_found_outside_shop

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
    body: ServiceRequestIn,
    user: User = Depends(require_role(Role.CUSTOMER, Role.ADMIN, Role.TECHNICIAN)),
    db: Session = Depends(get_db),
):
    """A customer raises their own request. An admin or technician raises one on a customer's
    behalf (a phone call, or a new fault found on site); a technician's is assigned to them,
    since otherwise it would never reach their job queue."""
    description = body.description.strip()
    if not description:
        raise HTTPException(status_code=400, detail="Describe the problem.")

    on_behalf = user.role != Role.CUSTOMER
    if on_behalf:
        customer = db.get(Customer, body.customer_id) if body.customer_id is not None else None
        if customer is None or not customer.user.is_active or customer.user.shop_id != user.shop_id:
            raise HTTPException(status_code=400, detail="Select the customer this request is for.")
    else:
        customer = user.customer

    equipment_id = None
    if body.equipment_id is not None:
        equipment = db.get(Equipment, body.equipment_id)
        if equipment is None or equipment.customer_id != customer.id:
            detail = (
                "Select equipment registered to this customer."
                if on_behalf
                else "Select one of your own registered equipment."
            )
            raise HTTPException(status_code=400, detail=detail)
        equipment_id = equipment.id

    category_id = None
    if body.category_id is not None:
        if db.get(ComplaintCategory, body.category_id) is None:
            raise HTTPException(status_code=400, detail="Select a valid category.")
        category_id = body.category_id

    # Asked once: if this customer has never given a service address, this request is
    # where we collect it, and it's then on file for every request after this one.
    if not customer.address:
        address = (body.address or "").strip()
        if not address:
            detail = "Enter the customer's service address." if on_behalf else "Enter your service address."
            raise HTTPException(status_code=400, detail=detail)
        customer.address = address

    request = ServiceRequest(
        customer_id=customer.id,
        technician_id=user.technician.id if user.role == Role.TECHNICIAN else None,
        equipment_id=equipment_id,
        category_id=category_id,
        description=description,
        urgency=predict_urgency(description),
    )
    db.add(request)
    db.flush()  # Assigns request.id for the status log row below, before the single commit.
    db.add(RequestStatusLog(request_id=request.id, old_status=None, new_status=RequestStatus.OPEN, changed_by=user.id))
    if on_behalf:
        _notify(db, customer.user_id, f"{user.name} raised request #{request.id} for you.", link="/portal/requests")
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
def list_all_requests(user: User = Depends(require_role(Role.ADMIN)), db: Session = Depends(get_db)):
    requests = db.scalars(
        select(ServiceRequest)
        .options(*_WITH_RELATED)
        .where(ServiceRequest.customer_id.in_(customer_ids(user.shop_id)))
        .order_by(ServiceRequest.created_at.desc(), ServiceRequest.id.desc())
    ).all()
    return _with_equipment_risk(requests, db)


@router.get("/technicians", response_model=list[TechnicianSummary])
def list_technicians_for_assignment(user: User = Depends(require_role(Role.ADMIN)), db: Session = Depends(get_db)):
    return db.scalars(
        select(Technician).join(User).where(User.is_active, User.shop_id == user.shop_id).order_by(User.name)
    ).all()


@router.get("/customers", response_model=list[CustomerChoice])
def list_customers_for_requests(
    user: User = Depends(require_role(Role.ADMIN, Role.TECHNICIAN)), db: Session = Depends(get_db)
):
    """Active customers and their equipment, for staff raising a request on someone's behalf."""
    return db.scalars(
        select(Customer)
        .join(User)
        .where(User.is_active, User.shop_id == user.shop_id)
        .options(joinedload(Customer.user), selectinload(Customer.equipment))
        .order_by(User.name)
    ).all()


@router.get("/categories", response_model=list[ComplaintCategoryOut])
def list_categories(
    _user: User = Depends(require_role(Role.CUSTOMER, Role.ADMIN, Role.TECHNICIAN)), db: Session = Depends(get_db)
):
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
    body: SuggestionIn,
    user: User = Depends(require_role(Role.CUSTOMER, Role.ADMIN, Role.TECHNICIAN)),
    db: Session = Depends(get_db),
):
    """Tried before a request is even submitted, so a customer (or staff taking their call) can
    attempt an easy fix first — see the "Check for a quick fix" button on the new-request form."""
    return _serialize_suggestions(suggest_fixes(db, body.description, shop_id=user.shop_id))


@router.get("/{request_id}/suggestions", response_model=list[SuggestionOut])
def suggest_for_request(
    request_id: int, user: User = Depends(require_role(Role.ADMIN, Role.TECHNICIAN)), db: Session = Depends(get_db)
):
    request = _get_request_in_shop(db, request_id, user)
    if user.role == Role.TECHNICIAN and request.technician_id != user.technician.id:
        raise HTTPException(status_code=403, detail="This request isn't assigned to you.")
    return _serialize_suggestions(suggest_fixes(db, request.description, shop_id=user.shop_id))


@router.patch("/{request_id}", response_model=ServiceRequestOut)
def update_request(
    request_id: int,
    body: RequestUpdateIn,
    user: User = Depends(require_role(Role.ADMIN, Role.TECHNICIAN)),
    db: Session = Depends(get_db),
):
    request = _get_request_in_shop(db, request_id, user, *_WITH_RELATED)
    if body.technician_id is None and body.status is None:
        raise HTTPException(status_code=400, detail="Nothing to update.")

    if body.technician_id is not None:
        if user.role != Role.ADMIN:
            raise HTTPException(status_code=403, detail="Only an admin can assign a technician.")
        technician = db.get(Technician, body.technician_id)
        if technician is None or technician.user.shop_id != user.shop_id:
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


def _get_request_in_shop(db: Session, request_id: int, user: User, *options) -> ServiceRequest:
    request = db.scalar(select(ServiceRequest).options(*options).where(ServiceRequest.id == request_id))
    detail = "That service request doesn't exist."
    if request is None:
        raise HTTPException(status_code=404, detail=detail)
    not_found_outside_shop(request.customer.user.shop_id, user, detail)
    return request


def _transition(db: Session, request: ServiceRequest, new_status: RequestStatus, actor: User) -> None:
    db.add(
        RequestStatusLog(
            request_id=request.id, old_status=request.status, new_status=new_status, changed_by=actor.id
        )
    )
    request.status = new_status
    _notify(db, request.customer.user_id, f"Request #{request.id} is now {new_status.value.replace('_', ' ')}.")
