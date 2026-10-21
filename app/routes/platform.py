"""The config portal's API: Sollu operators setting up and configuring shops.

Everything about a shop that isn't the shop's own day-to-day work is configured here, not in
the shop app: creating the shop and its owner, its name and sign-up slug, its plan and limits,
switching it off, adding owners, and resetting anyone's password. Operators log in separately
from shop users — see app.operator_auth — and see every shop.
"""

from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from app.accounts import (
    PHONE_PATTERN,
    AccountError,
    create_user,
    find_operator_by_email,
    normalise_phone,
    technician_limit_problem,
)
from app.database import get_db
from app.models import PLAN_LIMITS, Operator, Plan, Role, ServiceReport, Shop, Technician, User
from app.operator_auth import current_operator, end_session, start_session
from app.schemas import (
    AddShopStaffIn,
    CreateShopIn,
    OperatorLoginIn,
    OperatorOut,
    ResetPasswordIn,
    SetUserActiveIn,
    ShopDetailOut,
    ShopStaffOut,
    ShopSummaryOut,
    UpdateShopIn,
)
from app.security import DUMMY_HASH, hash_password, password_problem, verify_password
from app.shops import ShopError, clean_name, clean_slug, create_shop, customer_ids, request_ids

router = APIRouter(prefix="/api/platform", tags=["config portal"])

STAFF_ROLES = {Role.ADMIN.value, Role.TECHNICIAN.value}
MAX_LIMIT = 100_000


# --- Logging in ---------------------------------------------------------------------------


@router.post("/auth/login", response_model=OperatorOut)
def login(body: OperatorLoginIn, response: Response, db: Session = Depends(get_db)):
    operator = find_operator_by_email(db, body.email)
    if operator is None:
        verify_password(body.password, DUMMY_HASH)
    if operator is None or not verify_password(body.password, operator.password_hash) or not operator.is_active:
        raise HTTPException(status_code=401, detail="That email and password don't match.")
    start_session(response, operator)
    return operator


@router.post("/auth/logout", status_code=204)
def logout():
    response = Response(status_code=204)
    end_session(response)
    return response


@router.get("/auth/me", response_model=OperatorOut)
def me(operator: Operator = Depends(current_operator)):
    return operator


# --- Shops --------------------------------------------------------------------------------


def _summary(db: Session, shop: Shop) -> dict:
    month_start = datetime.now(UTC).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    return dict(
        id=shop.id,
        name=shop.name,
        slug=shop.slug,
        is_active=shop.is_active,
        plan=shop.plan,
        technician_limit=shop.technician_limit,
        monthly_report_limit=shop.monthly_report_limit,
        contact_phone=shop.contact_phone,
        created_at=shop.created_at,
        active_technicians=db.scalar(
            select(func.count(Technician.id)).join(User).where(User.shop_id == shop.id, User.is_active)
        )
        or 0,
        customers=db.scalar(select(func.count()).select_from(customer_ids(shop.id).subquery())) or 0,
        reports_this_month=db.scalar(
            select(func.count(ServiceReport.id)).where(
                ServiceReport.request_id.in_(request_ids(shop.id)), ServiceReport.created_at >= month_start
            )
        )
        or 0,
    )


def _detail(db: Session, shop: Shop) -> ShopDetailOut:
    staff = db.scalars(
        select(User)
        .options(joinedload(User.technician))
        .where(User.shop_id == shop.id, User.role.in_(STAFF_ROLES))
        .order_by(User.role, User.name)
    ).all()
    return ShopDetailOut(
        **_summary(db, shop),
        staff=[
            ShopStaffOut(
                id=user.id,
                name=user.name,
                email=user.email,
                role=user.role,
                is_active=user.is_active,
                skill_area=user.technician.skill_area if user.technician else None,
            )
            for user in staff
        ],
    )


def _get_shop(db: Session, shop_id: int) -> Shop:
    shop = db.get(Shop, shop_id)
    if shop is None:
        raise HTTPException(status_code=404, detail="That shop doesn't exist.")
    return shop


def _plan(value: str) -> Plan:
    if value not in {plan.value for plan in Plan}:
        raise HTTPException(status_code=400, detail="Plan must be starter, growth or pro.")
    return Plan(value)


def _contact_phone(value: str | None) -> str | None:
    value = (value or "").strip()
    if not value:
        return None
    if not PHONE_PATTERN.match(value):
        raise HTTPException(status_code=400, detail="Enter a valid phone number, digits only, optionally starting with +.")
    return normalise_phone(value)


def _limit(value: int, what: str) -> int:
    if not 0 <= value <= MAX_LIMIT:
        raise HTTPException(status_code=400, detail=f"The {what} limit must be between 0 and {MAX_LIMIT:,}.")
    return value


@router.get("/shops", response_model=list[ShopSummaryOut])
def list_shops(_operator: Operator = Depends(current_operator), db: Session = Depends(get_db)):
    shops = db.scalars(select(Shop).order_by(Shop.is_active.desc(), Shop.name)).all()
    return [_summary(db, shop) for shop in shops]


@router.post("/shops", response_model=ShopDetailOut, status_code=201)
def create_shop_with_owner(body: CreateShopIn, _operator: Operator = Depends(current_operator), db: Session = Depends(get_db)):
    """The shop and its first owner in one transaction: create_shop only flushes, and
    create_user commits both, so a rejected owner leaves no empty shop behind."""
    try:
        shop = create_shop(
            db, name=body.name, slug=body.slug, plan=_plan(body.plan), contact_phone=_contact_phone(body.contact_phone)
        )
        create_user(
            db, shop_id=shop.id, name=body.owner_name, email=body.owner_email, password=body.owner_password, role=Role.ADMIN
        )
    except (ShopError, AccountError) as error:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(error))
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="That slug or owner email is already in use.")
    return _detail(db, shop)


@router.get("/shops/{shop_id}", response_model=ShopDetailOut)
def get_shop(shop_id: int, _operator: Operator = Depends(current_operator), db: Session = Depends(get_db)):
    return _detail(db, _get_shop(db, shop_id))


@router.patch("/shops/{shop_id}", response_model=ShopDetailOut)
def update_shop(
    shop_id: int, body: UpdateShopIn, _operator: Operator = Depends(current_operator), db: Session = Depends(get_db)
):
    shop = _get_shop(db, shop_id)
    sent = body.model_fields_set
    try:
        if "name" in sent and body.name is not None:
            shop.name = clean_name(body.name)
        if "slug" in sent and body.slug is not None:
            shop.slug = clean_slug(db, body.slug, shop_id=shop.id)
    except ShopError as error:
        raise HTTPException(status_code=400, detail=str(error))
    if "is_active" in sent and body.is_active is not None:
        shop.is_active = body.is_active
    if "plan" in sent and body.plan is not None:
        shop.plan = _plan(body.plan)
        shop.technician_limit, shop.monthly_report_limit = PLAN_LIMITS[shop.plan]
    if "technician_limit" in sent and body.technician_limit is not None:
        shop.technician_limit = _limit(body.technician_limit, "technician")
    if "monthly_report_limit" in sent and body.monthly_report_limit is not None:
        shop.monthly_report_limit = _limit(body.monthly_report_limit, "report")
    if "contact_phone" in sent:
        shop.contact_phone = _contact_phone(body.contact_phone)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="A shop with this slug already exists.")
    return _detail(db, shop)


# --- A shop's staff -------------------------------------------------------------------------


@router.post("/shops/{shop_id}/staff", response_model=ShopDetailOut, status_code=201)
def add_staff(
    shop_id: int, body: AddShopStaffIn, _operator: Operator = Depends(current_operator), db: Session = Depends(get_db)
):
    shop = _get_shop(db, shop_id)
    if body.role not in STAFF_ROLES:
        raise HTTPException(status_code=400, detail="Role must be admin (owner) or technician.")
    try:
        create_user(
            db,
            shop_id=shop.id,
            name=body.name,
            email=body.email,
            password=body.password,
            role=Role(body.role),
            skill_area=body.skill_area,
        )
    except AccountError as error:
        raise HTTPException(status_code=400, detail=str(error))
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="An account with this email already exists.")
    return _detail(db, shop)


def _get_user(db: Session, user_id: int) -> User:
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="That user doesn't exist.")
    return user


@router.patch("/users/{user_id}/active", response_model=ShopDetailOut)
def set_user_active(
    user_id: int, body: SetUserActiveIn, _operator: Operator = Depends(current_operator), db: Session = Depends(get_db)
):
    user = _get_user(db, user_id)
    if body.is_active and not user.is_active and user.technician:
        if problem := technician_limit_problem(db, user.shop_id):
            raise HTTPException(status_code=400, detail=problem)
    if not body.is_active and user.is_active and user.role == Role.ADMIN:
        other_owners = db.scalar(
            select(func.count(User.id)).where(
                User.shop_id == user.shop_id, User.role == Role.ADMIN, User.is_active, User.id != user.id
            )
        )
        if not other_owners:
            raise HTTPException(status_code=400, detail="A shop needs at least one active owner. Add another first.")
    user.is_active = body.is_active
    db.commit()
    return _detail(db, user.shop)


@router.post("/users/{user_id}/password", status_code=204)
def reset_password(
    user_id: int, body: ResetPasswordIn, _operator: Operator = Depends(current_operator), db: Session = Depends(get_db)
):
    """For an owner or technician who's forgotten theirs: the operator sets a new one and tells
    them. Takes effect at their next login."""
    user = _get_user(db, user_id)
    if problem := password_problem(body.password):
        raise HTTPException(status_code=400, detail=problem)
    user.password_hash = hash_password(body.password)
    db.commit()
    return Response(status_code=204)
