from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..auth import require_hr_admin
from ..database import get_db
from ..models import Department, Employee, Position
from ..schemas import PositionIn, PositionOut

router = APIRouter(prefix="/positions", tags=["职位管理"], dependencies=[Depends(require_hr_admin)])


def pos_out(pos: Position) -> PositionOut:
    return PositionOut(
        id=pos.id,
        name=pos.name,
        department_id=pos.department_id,
        department_name=pos.department.name if pos.department else "",
        level=pos.level,
    )


@router.get("", response_model=list[PositionOut])
def list_positions(db: Session = Depends(get_db)):
    return [pos_out(p) for p in db.query(Position).order_by(Position.id).all()]


@router.post("", response_model=PositionOut)
def create_position(body: PositionIn, db: Session = Depends(get_db)):
    if not db.get(Department, body.department_id):
        raise HTTPException(status_code=400, detail="所属部门不存在")
    pos = Position(name=body.name, department_id=body.department_id, level=body.level)
    db.add(pos)
    db.commit()
    db.refresh(pos)
    return pos_out(pos)


@router.put("/{pos_id}", response_model=PositionOut)
def update_position(pos_id: int, body: PositionIn, db: Session = Depends(get_db)):
    pos = db.get(Position, pos_id)
    if not pos:
        raise HTTPException(status_code=404, detail="职位不存在")
    if not db.get(Department, body.department_id):
        raise HTTPException(status_code=400, detail="所属部门不存在")
    pos.name = body.name
    pos.department_id = body.department_id
    pos.level = body.level
    db.commit()
    db.refresh(pos)
    return pos_out(pos)


@router.delete("/{pos_id}")
def delete_position(pos_id: int, db: Session = Depends(get_db)):
    pos = db.get(Position, pos_id)
    if not pos:
        raise HTTPException(status_code=404, detail="职位不存在")
    if db.query(Employee).filter(Employee.position_id == pos_id).count() > 0:
        raise HTTPException(status_code=400, detail="该职位下存在员工，无法删除")
    db.delete(pos)
    db.commit()
    return {"message": "删除成功"}
