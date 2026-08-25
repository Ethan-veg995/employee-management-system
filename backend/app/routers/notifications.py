from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..auth import require_login
from ..database import get_db
from ..models import Notification, User
from ..schemas import NotificationOut

router = APIRouter(prefix="/notifications", tags=["消息通知"])


def create_notification(db: Session, user_id: int, ntype: str, title: str,
                        content: str = "", related_id: int | None = None) -> Notification:
    n = Notification(user_id=user_id, type=ntype, title=title,
                     content=content, related_id=related_id)
    db.add(n)
    db.commit()
    db.refresh(n)
    return n


def notify_all(db: Session, ntype: str, title: str, content: str = "", related_id: int | None = None):
    """给所有员工账号发通知"""
    users = db.query(User).all()
    for u in users:
        create_notification(db, u.id, ntype, title, content, related_id)


def notif_out(n: Notification) -> NotificationOut:
    return NotificationOut(id=n.id, type=n.type, title=n.title, content=n.content,
                           related_id=n.related_id, is_read=n.is_read, created_at=n.created_at)


@router.get("", response_model=list[NotificationOut])
def list_notifications(unread_only: int = 0, limit: int = 50,
                       user=Depends(require_login), db: Session = Depends(get_db)):
    q = db.query(Notification).filter(Notification.user_id == user.id)
    if unread_only:
        q = q.filter(Notification.is_read == 0)
    rows = q.order_by(Notification.created_at.desc()).limit(limit).all()
    return [notif_out(n) for n in rows]


@router.get("/unread-count")
def unread_count(user=Depends(require_login), db: Session = Depends(get_db)):
    count = (db.query(Notification)
             .filter(Notification.user_id == user.id, Notification.is_read == 0)
             .count())
    return {"count": count}


@router.post("/{notif_id}/read")
def mark_read(notif_id: int, user=Depends(require_login), db: Session = Depends(get_db)):
    n = db.get(Notification, notif_id)
    if n and n.user_id == user.id:
        n.is_read = 1
        db.commit()
    return {"message": "已标记已读"}


@router.post("/read-all")
def mark_all_read(user=Depends(require_login), db: Session = Depends(get_db)):
    db.query(Notification).filter(Notification.user_id == user.id,
                                  Notification.is_read == 0).update({Notification.is_read: 1})
    db.commit()
    return {"message": "全部已读"}
