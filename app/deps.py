from collections.abc import Callable

from fastapi import Depends, Request
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Role, User

ROLE_HOME = {
    Role.ADMIN: "/admin",
    Role.CUSTOMER: "/customer",
    Role.TECHNICIAN: "/technician",
}


class NotAuthenticated(Exception):
    """Raised when a page needs a logged-in user and there is none. Handled in app.main."""


class Forbidden(Exception):
    """Raised when the logged-in user's role may not open a page. Handled in app.main."""


def get_optional_user(request: Request, db: Session = Depends(get_db)) -> User | None:
    user_id = request.session.get("user_id")
    if user_id is None:
        return None
    # The role is read from the database on every request, never from the cookie,
    # so a role change or deactivation — of the user or their whole shop — takes effect immediately.
    user = db.get(User, user_id)
    if user is None or not user.is_active or not user.shop.is_active:
        request.session.clear()
        return None
    return user


def get_current_user(user: User | None = Depends(get_optional_user)) -> User:
    if user is None:
        raise NotAuthenticated()
    return user


def require_role(*roles: Role) -> Callable[..., User]:
    def checker(user: User = Depends(get_current_user)) -> User:
        if user.role not in roles:
            raise Forbidden()
        return user

    return checker
