from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..auth import require_hr, require_login
from ..database import get_db
from ..models import Announcement
from ..routers.notifications import notify_all
from ..schemas import AnnouncementIn, AnnouncementOut

router = APIRouter(prefix="/announcements", tags=["公告中心"])


def ann_out(a: Announcement) -> AnnouncementOut:
    return AnnouncementOut(id=a.id, title=a.title, content=a.content,
                           publisher_name=a.publisher.username if a.publisher else "",
                           created_at=a.created_at)


@router.get("", response_model=list[AnnouncementOut])
def list_announcements(user=Depends(require_login), db: Session = Depends(get_db)):
    rows = db.query(Announcement).order_by(Announcement.created_at.desc()).all()
    return [ann_out(a) for a in rows]


@router.post("", response_model=AnnouncementOut)
def create_announcement(body: AnnouncementIn, user=Depends(require_hr),
                        db: Session = Depends(get_db)):
    if not body.title.strip():
        raise HTTPException(status_code=400, detail="公告标题不能为空")
    ann = Announcement(title=body.title, content=body.content, publisher_id=user.id)
    db.add(ann)
    db.commit()
    db.refresh(ann)
    notify_all(db, "announcement", "新公告发布",
               f"「{ann.title}」已发布，请及时查看", ann.id)
    return ann_out(ann)


@router.put("/{ann_id}", response_model=AnnouncementOut)
def update_announcement(ann_id: int, body: AnnouncementIn,
                        user=Depends(require_hr), db: Session = Depends(get_db)):
    ann = db.get(Announcement, ann_id)
    if not ann:
        raise HTTPException(status_code=404, detail="公告不存在")
    if not body.title.strip():
        raise HTTPException(status_code=400, detail="公告标题不能为空")
    ann.title = body.title
    ann.content = body.content
    db.commit()
    db.refresh(ann)
    return ann_out(ann)


@router.delete("/{ann_id}")
def delete_announcement(ann_id: int, user=Depends(require_hr),
                        db: Session = Depends(get_db)):
    ann = db.get(Announcement, ann_id)
    if not ann:
        raise HTTPException(status_code=404, detail="公告不存在")
    db.delete(ann)
    db.commit()
    return {"message": "删除成功"}
