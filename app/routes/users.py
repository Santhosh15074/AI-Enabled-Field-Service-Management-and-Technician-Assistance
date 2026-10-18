"""Admin management of staff accounts — the in-app counterpart to scripts/create_user.py,
mentioned as "a later phase" in the docstring on app.accounts. Customers still only ever sign
themselves up through the portal; nothing here can create one.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from app.accounts import AccountError, create_user
from app.database import get_db
from app.deps import require_role
from app.models import Role, User
from app.schemas import CreateStaffUserIn, SetUserActiveIn, StaffUserOut

router = APIRouter(prefix="/api/users", tags=["users"])

STAFF_ROLES = {Role.ADMIN.value, Role.TECHNICIAN.value}


def _serialize(user: User) -> StaffUserOut:
    return StaffUserOut(
        id=user.id,
        name=user.name,
        email=user.email,
        role=user.role,
        is_active=user.is_active,
        created_at=user.created_at,
        skill_area=user.technician.skill_area if user.technician else None,
        phone=user.customer.phone if user.customer else None,
    )


@router.get("", response_model=list[StaffUserOut])
def list_users(_user: User = Depends(require_role(Role.ADMIN)), db: Session = Depends(get_db)):
    users = db.scalars(
        select(User).options(joinedload(User.customer), joinedload(User.technician)).order_by(User.role, User.name)
    ).all()
    return [_serialize(user) for user in users]


@router.post("", response_model=StaffUserOut, status_code=201)
def create_staff_user(
    body: CreateStaffUserIn, _admin: User = Depends(require_role(Role.ADMIN)), db: Session = Depends(get_db)
):
    if body.role not in STAFF_ROLES:
        raise HTTPException(status_code=400, detail="Role must be admin or technician.")
    try:
        user = create_user(
            db, name=body.name, email=body.email, password=body.password, role=Role(body.role), skill_area=body.skill_area
        )
    except AccountError as error:
        raise HTTPException(status_code=400, detail=str(error))
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="An account with this email already exists.")
    return _serialize(user)


@router.patch("/{user_id}/active", response_model=StaffUserOut)
def set_active(
    user_id: int, body: SetUserActiveIn, admin: User = Depends(require_role(Role.ADMIN)), db: Session = Depends(get_db)
):
    if user_id == admin.id:
        raise HTTPException(status_code=400, detail="You can't deactivate your own account.")
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="That user doesn't exist.")
    user.is_active = body.is_active
    db.commit()
    return _serialize(user)
