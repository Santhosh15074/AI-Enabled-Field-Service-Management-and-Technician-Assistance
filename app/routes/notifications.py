"""A user's own notifications — written by app.routes.service_requests whenever a request they
care about is assigned or changes status. Nothing here creates a notification; this is only
where they're read and marked read.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models import Notification, NotificationStatus, User
from app.schemas import NotificationOut, UnreadCountOut

router = APIRouter(prefix="/api/notifications", tags=["notifications"])

RECENT_LIMIT = 50


@router.get("", response_model=list[NotificationOut])
def list_notifications(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.scalars(
        select(Notification)
        .where(Notification.user_id == user.id)
        .order_by(Notification.sent_on.desc(), Notification.id.desc())
        .limit(RECENT_LIMIT)
    ).all()


@router.get("/unread-count", response_model=UnreadCountOut)
def unread_count(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    count = db.scalar(
        select(func.count(Notification.id)).where(
            Notification.user_id == user.id, Notification.status == NotificationStatus.UNREAD
        )
    )
    return UnreadCountOut(count=count or 0)


@router.patch("/{notification_id}/read", response_model=NotificationOut)
def mark_read(notification_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    notification = db.get(Notification, notification_id)
    if notification is None or notification.user_id != user.id:
        raise HTTPException(status_code=404, detail="That notification doesn't exist.")
    notification.status = NotificationStatus.READ
    db.commit()
    return notification


@router.post("/read-all", status_code=204)
def mark_all_read(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    db.execute(
        update(Notification)
        .where(Notification.user_id == user.id, Notification.status == NotificationStatus.UNREAD)
        .values(status=NotificationStatus.READ)
    )
    db.commit()
