from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..auth import require_hr_admin, require_login
from ..database import get_db
from ..models import Employee, Salary
from ..schemas import SalaryIn, SalaryOut

router = APIRouter(prefix="/salaries", tags=["薪资管理"])


def salary_out(s: Salary) -> SalaryOut:
    return SalaryOut(
        id=s.id,
        employee_id=s.employee_id,
        employee_name=s.employee.name if s.employee else "",
        employee_no=s.employee.employee_no if s.employee else "",
        department_name=s.employee.department.name if s.employee and s.employee.department else "",
        year=s.year,
        month=s.month,
        base_salary=s.base_salary,
        bonus=s.bonus,
        deduction=s.deduction,
        actual_salary=s.actual_salary,
    )


@router.get("/years")
def salary_years(user=Depends(require_hr_admin), db: Session = Depends(get_db)):
    rows = db.query(Salary.year).distinct().order_by(Salary.year.desc()).all()
    return [r[0] for r in rows]


@router.get("")
def list_salaries(year: int | None = None, month: int | None = None,
                  employee_id: int | None = None, department_id: int | None = None,
                  user=Depends(require_hr_admin), db: Session = Depends(get_db)):
    q = db.query(Salary)
    if year:
        q = q.filter(Salary.year == year)
    if month:
        q = q.filter(Salary.month == month)
    if employee_id:
        q = q.filter(Salary.employee_id == employee_id)
    if department_id:
        q = q.join(Employee).filter(Employee.department_id == department_id)
    rows = q.order_by(Salary.year.desc(), Salary.month.desc(), Salary.employee_id).all()
    return [salary_out(s) for s in rows]


@router.get("/my")
def my_salaries(user=Depends(require_login), db: Session = Depends(get_db)):
    if not user.employee_id:
        raise HTTPException(status_code=400, detail="当前账号未关联员工档案")
    rows = (db.query(Salary).filter(Salary.employee_id == user.employee_id)
            .order_by(Salary.year.desc(), Salary.month.desc()).all())
    return [salary_out(s) for s in rows]


@router.post("", response_model=SalaryOut)
def create_salary(body: SalaryIn, user=Depends(require_hr_admin), db: Session = Depends(get_db)):
    if not db.get(Employee, body.employee_id):
        raise HTTPException(status_code=400, detail="员工不存在")
    existing = (db.query(Salary)
                .filter(Salary.employee_id == body.employee_id,
                        Salary.year == body.year, Salary.month == body.month)
                .first())
    if existing:
        raise HTTPException(status_code=400, detail="该员工当月薪资已存在，请使用编辑功能")
    s = Salary(employee_id=body.employee_id, year=body.year, month=body.month,
               base_salary=body.base_salary, bonus=body.bonus, deduction=body.deduction,
               actual_salary=round(body.base_salary + body.bonus - body.deduction, 2))
    db.add(s)
    db.commit()
    db.refresh(s)
    return salary_out(s)


@router.put("/{salary_id}", response_model=SalaryOut)
def update_salary(salary_id: int, body: SalaryIn, user=Depends(require_hr_admin),
                  db: Session = Depends(get_db)):
    s = db.get(Salary, salary_id)
    if not s:
        raise HTTPException(status_code=404, detail="薪资记录不存在")
    dup = (db.query(Salary)
           .filter(Salary.employee_id == body.employee_id,
                   Salary.year == body.year, Salary.month == body.month,
                   Salary.id != salary_id).first())
    if dup:
        raise HTTPException(status_code=400, detail="该员工当月薪资已存在")
    s.employee_id = body.employee_id
    s.year = body.year
    s.month = body.month
    s.base_salary = body.base_salary
    s.bonus = body.bonus
    s.deduction = body.deduction
    s.actual_salary = round(body.base_salary + body.bonus - body.deduction, 2)
    db.commit()
    db.refresh(s)
    return salary_out(s)


@router.delete("/{salary_id}")
def delete_salary(salary_id: int, user=Depends(require_hr_admin), db: Session = Depends(get_db)):
    s = db.get(Salary, salary_id)
    if not s:
        raise HTTPException(status_code=404, detail="薪资记录不存在")
    db.delete(s)
    db.commit()
    return {"message": "删除成功"}
