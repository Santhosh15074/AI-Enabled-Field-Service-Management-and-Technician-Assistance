"""Logging in to the config portal, as a Sollu operator.

Deliberately separate from shop logins (app.deps): its own signed cookie, scoped to
/api/platform, so a shop session can never reach the config portal's endpoints and logging in
or out of one never touches the other. The cookie holds only the operator's id; whether they
still exist and are active is read from the database on every request, like shop users.
"""

from fastapi import Depends, HTTPException, Request, Response
from itsdangerous import BadSignature, URLSafeTimedSerializer
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import get_db
from app.models import Operator

COOKIE = "sollu_operator"
COOKIE_PATH = "/api/platform"


def _serializer() -> URLSafeTimedSerializer:
    return URLSafeTimedSerializer(get_settings().secret_key, salt="operator-session")


def start_session(response: Response, operator: Operator) -> None:
    settings = get_settings()
    response.set_cookie(
        COOKIE,
        _serializer().dumps(operator.id),
        max_age=settings.session_max_age_seconds,
        path=COOKIE_PATH,
        httponly=True,
        samesite="lax",
        secure=settings.session_https_only,
    )


def end_session(response: Response) -> None:
    response.delete_cookie(COOKIE, path=COOKIE_PATH)


def current_operator(request: Request, db: Session = Depends(get_db)) -> Operator:
    token = request.cookies.get(COOKIE)
    if token is None:
        raise HTTPException(status_code=401, detail="Not logged in.")
    try:
        operator_id = _serializer().loads(token, max_age=get_settings().session_max_age_seconds)
    except BadSignature:  # also covers an expired cookie
        raise HTTPException(status_code=401, detail="Not logged in.")
    operator = db.get(Operator, operator_id)
    if operator is None or not operator.is_active:
        raise HTTPException(status_code=401, detail="Not logged in.")
    return operator
