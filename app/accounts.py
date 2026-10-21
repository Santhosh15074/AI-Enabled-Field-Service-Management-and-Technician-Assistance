"""Creating accounts.

Customers are the general public — people with equipment to service — so they sign
themselves up through the customer portal (see app.routes.auth.register). A phone number
is all that's required of them; email is optional, since not every customer has or checks
one. Admins and technicians are a shop's own staff: those accounts are provisioned by that
shop's admin (the owner) in the app, or by a Sollu operator in the config portal, never by
public sign-up, and they're still identified by email.

Every account belongs to exactly one shop (see app.shops). Emails and customer phone numbers
are still unique across all shops, because they're what people log in with and login doesn't
ask which shop you're from.
"""

import re

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Customer, Operator, Role, Shop, Technician, User
from app.security import hash_password, password_problem

EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
PHONE_PATTERN = re.compile(r"^\+?[0-9][0-9 \-]{6,18}$")


class AccountError(ValueError):
    pass


def normalise_email(email: str) -> str:
    return email.strip().lower()


def normalise_phone(phone: str) -> str:
    # Keeps a leading "+" and the digits only, so "+91 98765 43210" and "+91-98765-43210"
    # are recognised as the same number at login regardless of how either was typed.
    phone = phone.strip()
    prefix = "+" if phone.startswith("+") else ""
    return prefix + re.sub(r"[^0-9]", "", phone)


def find_user_by_email(db: Session, email: str) -> User | None:
    return db.scalar(select(User).where(func.lower(User.email) == normalise_email(email)))


def find_user_by_phone(db: Session, phone: str) -> User | None:
    return db.scalar(select(User).join(Customer).where(Customer.phone == normalise_phone(phone)))


def find_user_by_identifier(db: Session, identifier: str) -> User | None:
    """Login identifier: an email for staff, an email or a phone number for a customer."""
    return find_user_by_email(db, identifier) or find_user_by_phone(db, identifier)


def technician_limit_problem(db: Session, shop_id: int) -> str | None:
    """Why the shop can't have one more active technician, or None if it can (see Shop.technician_limit)."""
    shop = db.get(Shop, shop_id)
    active = db.scalar(
        select(func.count(Technician.id)).join(User).where(User.shop_id == shop_id, User.is_active)
    )
    if (active or 0) >= shop.technician_limit:
        return f"This shop's plan allows {shop.technician_limit} active technicians. Call Sollu to move up a plan."
    return None


def create_user(
    db: Session,
    *,
    shop_id: int,
    name: str,
    password: str,
    role: Role,
    email: str | None = None,
    address: str | None = None,
    phone: str | None = None,
    skill_area: str | None = None,
) -> User:
    """Create a user and the matching customer or technician profile, then commit.

    Customers need a phone number and may skip email. Everyone else (admin, technician)
    needs an email; they have no phone-based login.

    Raises AccountError with a message that is safe to show on the form.
    """
    name = name.strip()
    email = normalise_email(email) if email else None
    # Validated against the raw, spaces-and-dashes-allowed form first (so a typo like
    # "call me" gets "enter a valid phone number", not "enter a phone number"); normalised
    # only afterwards, for storage and for matching at login.
    phone = phone.strip() if phone else None

    if not name:
        raise AccountError("Enter your name.")
    if len(name) > 100:
        raise AccountError("Name must be at most 100 characters.")
    if problem := password_problem(password):
        raise AccountError(problem)

    if role == Role.CUSTOMER:
        if not phone:
            raise AccountError("Enter a phone number.")
        if not PHONE_PATTERN.match(phone):
            raise AccountError("Enter a valid phone number, digits only, optionally starting with +.")
        phone = normalise_phone(phone)
        if db.scalar(select(Customer).where(Customer.phone == phone)):
            raise AccountError("An account with this phone number already exists.")
        if email and (not EMAIL_PATTERN.match(email) or len(email) > 255):
            raise AccountError("Enter a valid email address, like name@example.com.")
    else:
        if not email:
            raise AccountError("Enter an email address.")
        if not EMAIL_PATTERN.match(email) or len(email) > 255:
            raise AccountError("Enter a valid email address, like name@example.com.")
    if role == Role.TECHNICIAN and (problem := technician_limit_problem(db, shop_id)):
        raise AccountError(problem)

    if email and find_user_by_email(db, email):
        raise AccountError("An account with this email already exists.")

    user = User(shop_id=shop_id, name=name, email=email, password_hash=hash_password(password), role=role)
    if role == Role.CUSTOMER:
        user.customer = Customer(address=(address or "").strip() or None, phone=phone)
    elif role == Role.TECHNICIAN:
        user.technician = Technician(skill_area=(skill_area or "").strip() or None)

    db.add(user)
    db.commit()
    return user


def find_operator_by_email(db: Session, email: str) -> Operator | None:
    return db.scalar(select(Operator).where(func.lower(Operator.email) == normalise_email(email)))


def create_operator(db: Session, *, name: str, email: str, password: str) -> Operator:
    """A Sollu operator for the config portal — see scripts/create_operator.py. Commits."""
    name = name.strip()
    email = normalise_email(email)
    if not name:
        raise AccountError("Enter a name.")
    if not EMAIL_PATTERN.match(email) or len(email) > 255:
        raise AccountError("Enter a valid email address, like name@example.com.")
    if problem := password_problem(password):
        raise AccountError(problem)
    if find_operator_by_email(db, email):
        raise AccountError("An operator with this email already exists.")

    operator = Operator(name=name, email=email, password_hash=hash_password(password))
    db.add(operator)
    db.commit()
    return operator
