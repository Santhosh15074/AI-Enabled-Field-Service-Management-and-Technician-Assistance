from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.accounts import AccountError, create_user, find_user_by_identifier
from app.database import get_db
from app.deps import get_current_user
from app.models import Role, User
from app.schemas import LoginIn, RegisterIn, UserOut
from app.security import DUMMY_HASH, verify_password
from app.shops import find_shop_by_slug

router = APIRouter(prefix="/api/auth", tags=["auth"])


def _conflicting_field(error: IntegrityError) -> str:
    """Which unique column a race-condition duplicate actually violated.

    Postgres names the constraint (e.g. "ix_customers_phone") and SQLite names the column
    ("UNIQUE constraint failed: customers.phone") in the original driver error, so this is a
    plain substring check rather than parsing either format precisely.
    """
    message = str(error.orig).lower()
    if "phone" in message:
        return "phone number"
    if "email" in message:
        return "email"
    return "phone number or email"  # Should be unreachable; a safe fallback if the message changes shape.


@router.post("/login", response_model=UserOut)
def login(body: LoginIn, request: Request, db: Session = Depends(get_db)):
    user = find_user_by_identifier(db, body.identifier)
    if user is None:
        verify_password(body.password, DUMMY_HASH)
    if (
        user is None
        or not verify_password(body.password, user.password_hash)
        or not user.is_active
        or not user.shop.is_active
    ):
        raise HTTPException(status_code=401, detail="That login and password don't match.")

    # A fresh session on every login, so nothing from before the login carries over.
    request.session.clear()
    request.session["user_id"] = user.id
    return user


@router.post("/logout", status_code=204)
def logout(request: Request):
    request.session.clear()
    return Response(status_code=204)


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)):
    return user


@router.post("/register", response_model=UserOut, status_code=201)
def register(body: RegisterIn, db: Session = Depends(get_db)):
    """The customer portal's sign-up. Always creates a customer — there is no way for a
    caller to request another role here. Owners and technicians are created by the shop's owner
    or in the config portal (app.routes.platform), never through this endpoint. No address is collected here;
    that's asked for when the customer raises their first complaint. The shop comes from the
    shop's own sign-up link (/portal/register?shop=<slug>).
    """
    shop = find_shop_by_slug(db, body.shop, active_only=True)
    if shop is None:
        raise HTTPException(status_code=400, detail="This sign-up link isn't valid. Ask your service company for theirs.")
    try:
        return create_user(
            db,
            shop_id=shop.id,
            name=body.name,
            email=body.email,
            password=body.password,
            role=Role.CUSTOMER,
            phone=body.phone,
        )
    except AccountError as error:
        raise HTTPException(status_code=400, detail=str(error))
    except IntegrityError as error:
        # Two sign-ups with the same phone or email at the same moment: the unique index
        # rejects the second, after create_user's own check already missed the race.
        db.rollback()
        raise HTTPException(status_code=400, detail=f"An account with this {_conflicting_field(error)} already exists.")
