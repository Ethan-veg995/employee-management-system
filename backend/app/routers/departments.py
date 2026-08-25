from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..auth import require_hr_admin
from ..database import get_db
from ..models import Department, Employee, Position
from ..schemas import DepartmentIn, DepartmentOut

router = APIRouter(prefix="/departments", tags=["部门管理"], dependencies=[Depends(require_hr_admin)])


def dept_out(db: Session, dept: Department) -> DepartmentOut:
    count = db.query(Employee).filter(Employee.department_id == dept.id).count()
    return DepartmentOut(id=dept.id, name=dept.name, description=dept.description, employee_count=count)


@router.get("", response_model=list[DepartmentOut])
def list_departments(db: Session = Depends(get_db)):
    return [dept_out(db, d) for d in db.query(Department).order_by(Department.id).all()]


@router.post("", response_model=DepartmentOut)
def create_department(body: DepartmentIn, db: Session = Depends(get_db)):
    if db.query(Department).filter(Department.name == body.name).first():
        raise HTTPException(status_code=400, detail="部门名称已存在")
    dept = Department(name=body.name, description=body.description)
    db.add(dept)
    db.commit()
    db.refresh(dept)
    return dept_out(db, dept)


@router.put("/{dept_id}", response_model=DepartmentOut)
def update_department(dept_id: int, body: DepartmentIn, db: Session = Depends(get_db)):
    dept = db.get(Department, dept_id)
    if not dept:
        raise HTTPException(status_code=404, detail="部门不存在")
    dup = db.query(Department).filter(Department.name == body.name, Department.id != dept_id).first()
    if dup:
        raise HTTPException(status_code=400, detail="部门名称已存在")
    dept.name = body.name
    dept.description = body.description
    db.commit()
    db.refresh(dept)
    return dept_out(db, dept)


@router.delete("/{dept_id}")
def delete_department(dept_id: int, db: Session = Depends(get_db)):
    dept = db.get(Department, dept_id)
    if not dept:
        raise HTTPException(status_code=404, detail="部门不存在")
    emp_count = db.query(Employee).filter(Employee.department_id == dept_id).count()
    pos_count = db.query(Position).filter(Position.department_id == dept_id).count()
    if emp_count > 0 or pos_count > 0:
        raise HTTPException(status_code=400, detail="该部门下存在员工或职位，无法删除")
    db.delete(dept)
    db.commit()
    return {"message": "删除成功"}
