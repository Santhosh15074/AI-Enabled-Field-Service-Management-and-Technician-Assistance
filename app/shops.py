"""Shops, and keeping each shop's data to itself.

Only users and knowledge-base entries carry a shop_id. Everything else reaches its shop through
the customer it belongs to (equipment, requests, reports) or the technician's own user, so the
helpers below are subqueries over those — one place to get the scoping right, rather than a
hand-written join in every route.

A record from another shop is reported as not found (404), never forbidden (403), so staff can't
tell another shop's request ids from ones that don't exist.

Shops themselves are created and configured only by a Sollu operator in the config portal
(app.routes.platform), together with their owner's account: the founder sets every shop up in
person, so there's no public sign-up.
"""

import re

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import PLAN_LIMITS, Customer, Equipment, Plan, ServiceRequest, Shop, Technician, User

SLUG_PATTERN = re.compile(r"^[a-z0-9](?:[a-z0-9-]{1,38}[a-z0-9])$")


class ShopError(ValueError):
    pass


def find_shop_by_slug(db: Session, slug: str, *, active_only: bool = False) -> Shop | None:
    query = select(Shop).where(Shop.slug == slug.strip().lower())
    if active_only:
        query = query.where(Shop.is_active)
    return db.scalar(query)


def clean_name(name: str) -> str:
    name = name.strip()
    if not name:
        raise ShopError("Enter the shop's name.")
    if len(name) > 100:
        raise ShopError("The shop's name must be at most 100 characters.")
    return name


def clean_slug(db: Session, slug: str, *, shop_id: int | None = None) -> str:
    """Validated and unique; `shop_id` is the shop being renamed, which may keep its own slug."""
    slug = slug.strip().lower()
    if not SLUG_PATTERN.match(slug):
        raise ShopError("The slug must be 3-40 lowercase letters, digits or dashes, e.g. ravi-aircon.")
    existing = find_shop_by_slug(db, slug)
    if existing is not None and existing.id != shop_id:
        raise ShopError("A shop with this slug already exists.")
    return slug


def create_shop(db: Session, *, name: str, slug: str, plan: Plan = Plan.STARTER, contact_phone: str | None = None) -> Shop:
    """Add the shop and flush, without committing — its owner is created in the same transaction
    (see app.routes.platform.create_shop), so a failed owner account doesn't leave an empty shop."""
    technician_limit, monthly_report_limit = PLAN_LIMITS[plan]
    shop = Shop(
        name=clean_name(name),
        slug=clean_slug(db, slug),
        plan=plan,
        technician_limit=technician_limit,
        monthly_report_limit=monthly_report_limit,
        contact_phone=(contact_phone or "").strip() or None,
    )
    db.add(shop)
    db.flush()
    return shop


def customer_ids(shop_id: int):
    return select(Customer.id).join(User, Customer.user_id == User.id).where(User.shop_id == shop_id)


def technician_ids(shop_id: int):
    return select(Technician.id).join(User, Technician.user_id == User.id).where(User.shop_id == shop_id)


def request_ids(shop_id: int):
    return select(ServiceRequest.id).where(ServiceRequest.customer_id.in_(customer_ids(shop_id)))


def equipment_ids(shop_id: int):
    return select(Equipment.id).where(Equipment.customer_id.in_(customer_ids(shop_id)))


def not_found_outside_shop(record_shop_id: int | None, user: User, detail: str) -> None:
    if record_shop_id != user.shop_id:
        raise HTTPException(status_code=404, detail=detail)
