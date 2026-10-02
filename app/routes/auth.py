from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy.orm import Session

from app.accounts import find_user_by_email
from app.database import get_db
from app.deps import get_current_user
from app.models import User
from app.schemas import LoginIn, UserOut
from app.security import DUMMY_HASH, verify_password

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/login", response_model=UserOut)
def login(body: LoginIn, request: Request, db: Session = Depends(get_db)):
    user = find_user_by_email(db, body.email)
    if user is None:
        verify_password(body.password, DUMMY_HASH)
    if user is None or not verify_password(body.password, user.password_hash) or not user.is_active:
        raise HTTPException(status_code=401, detail="Email or password is incorrect.")

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
