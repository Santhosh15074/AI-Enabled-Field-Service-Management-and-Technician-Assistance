"""Creating accounts. All accounts are provisioned by an organization admin, via
scripts/create_user.py today and an in-app admin screen in a later phase — there is no
public self-service sign-up.
"""

import re

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Customer, Role, Technician, User
from app.security import hash_password, password_problem

EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
PHONE_PATTERN = re.compile(r"^\+?[0-9][0-9 \-]{6,18}$")


class AccountError(ValueError):
    pass


def normalise_email(email: str) -> str:
    return email.strip().lower()


def find_user_by_email(db: Session, email: str) -> User | None:
    return db.scalar(select(User).where(func.lower(User.email) == normalise_email(email)))


def create_user(
    db: Session,
    *,
    name: str,
    email: str,
    password: str,
    role: Role,
    address: str | None = None,
    phone: str | None = None,
    skill_area: str | None = None,
) -> User:
    """Create a user and the matching customer or technician profile, then commit.

    Raises AccountError with a message that is safe to show on the form.
    """
    name = name.strip()
    email = normalise_email(email)
    phone = phone.strip() if phone else None

    if not name:
        raise AccountError("Enter your name.")
    if len(name) > 100:
        raise AccountError("Name must be at most 100 characters.")
    if not EMAIL_PATTERN.match(email) or len(email) > 255:
        raise AccountError("Enter a valid email address, like name@example.com.")
    if problem := password_problem(password):
        raise AccountError(problem)
    if phone and not PHONE_PATTERN.match(phone):
        raise AccountError("Enter a valid phone number, digits only, optionally starting with +.")
    if find_user_by_email(db, email):
        raise AccountError("An account with this email already exists.")

    user = User(name=name, email=email, password_hash=hash_password(password), role=role)
    if role == Role.CUSTOMER:
        user.customer = Customer(address=(address or "").strip() or None, phone=phone)
    elif role == Role.TECHNICIAN:
        user.technician = Technician(skill_area=(skill_area or "").strip() or None)

    db.add(user)
    db.commit()
    return user
