from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..auth import require_hr_admin, require_login
from ..config import PERF_COEFF, PERF_BONUS_RATE, PERF_LEVELS
from ..database import get_db
from ..models import Employee, PerformanceReview, Salary, User
from ..schemas import PerformanceIn, PerformanceOut

router = APIRouter(prefix="/performance", tags=["绩效管理"])


def level_of(score: float) -> str:
    for level, threshold in PERF_LEVELS:
        if score >= threshold:
            return level
    return "C"


def perf_out(r: PerformanceReview) -> PerformanceOut:
    return PerformanceOut(
        id=r.id,
        employee_id=r.employee_id,
        employee_name=r.employee.name if r.employee else "",
        department_name=r.employee.department.name if r.employee and r.employee.department else "",
        reviewer_name=r.reviewer.username if r.reviewer else "",
        year=r.year,
        month=r.month,
        score=r.score,
        level=r.level,
        comment=r.comment,
    )


@router.get("")
def list_performance(year: int | None = None, month: int | None = None,
                     department_id: int | None = None, employee_id: int | None = None,
                     user=Depends(require_login), db: Session = Depends(get_db)):
    q = db.query(PerformanceReview)
    if year:
        q = q.filter(PerformanceReview.year == year)
    if month:
        q = q.filter(PerformanceReview.month == month)
    if employee_id:
        q = q.filter(PerformanceReview.employee_id == employee_id)
    if user.role == "employee":
        if not user.employee_id:
            raise HTTPException(status_code=400, detail="当前账号未关联员工档案")
        q = q.filter(PerformanceReview.employee_id == user.employee_id)
    elif department_id:
        q = q.join(Employee).filter(Employee.department_id == department_id)
    rows = q.order_by(PerformanceReview.year.desc(), PerformanceReview.month.desc()).all()
    return [perf_out(r) for r in rows]


@router.get("/my")
def my_performance(user=Depends(require_login), db: Session = Depends(get_db)):
    if not user.employee_id:
        raise HTTPException(status_code=400, detail="当前账号未关联员工档案")
    rows = (db.query(PerformanceReview)
            .filter(PerformanceReview.employee_id == user.employee_id)
            .order_by(PerformanceReview.year.desc(), PerformanceReview.month.desc()).all())
    return [perf_out(r) for r in rows]


@router.get("/suggest")
def suggest_bonus(employee_id: int, year: int, month: int,
                  user=Depends(require_hr_admin), db: Session = Depends(get_db)):
    """绩效→薪资联动：返回当月绩效等级/系数与建议绩效奖金"""
    emp = db.get(Employee, employee_id)
    if not emp:
        raise HTTPException(status_code=404, detail="员工不存在")
    perf = (db.query(PerformanceReview)
            .filter(PerformanceReview.employee_id == employee_id,
                    PerformanceReview.year == year, PerformanceReview.month == month)
            .first())
    salary = (db.query(Salary)
              .filter(Salary.employee_id == employee_id,
                      Salary.year == year, Salary.month == month)
              .first())
    if not perf:
        return {"level": None, "coefficient": 1.0, "suggested_bonus": 0,
                "base_salary": salary.base_salary if salary else 0}
    coeff = PERF_COEFF.get(perf.level, 1.0)
    base = salary.base_salary if salary else 0
    return {"level": perf.level, "coefficient": coeff,
            "suggested_bonus": round(coeff * base * PERF_BONUS_RATE, 2),
            "base_salary": base}


@router.post("", response_model=PerformanceOut)
def create_performance(body: PerformanceIn, user=Depends(require_login),
                       db: Session = Depends(get_db)):
    if user.role == "employee":
        raise HTTPException(status_code=403, detail="没有权限进行绩效评分")
    emp = db.get(Employee, body.employee_id)
    if not emp:
        raise HTTPException(status_code=400, detail="员工不存在")
    if user.role == "manager":
        if not user.employee_id:
            raise HTTPException(status_code=400, detail="当前账号未关联员工档案")
        if emp.department_id != user.employee.department_id:
            raise HTTPException(status_code=403, detail="只能为本部门员工评分")
    if not (0 <= body.score <= 100):
        raise HTTPException(status_code=400, detail="评分范围为 0-100")
    existing = (db.query(PerformanceReview)
                .filter(PerformanceReview.employee_id == body.employee_id,
                        PerformanceReview.year == body.year,
                        PerformanceReview.month == body.month)
                .first())
    if existing:
        raise HTTPException(status_code=400, detail="该员工当月已有绩效记录，请使用编辑功能")
    perf = PerformanceReview(employee_id=body.employee_id, reviewer_id=user.id,
                             year=body.year, month=body.month, score=body.score,
                             level=level_of(body.score), comment=body.comment)
    db.add(perf)
    db.commit()
    db.refresh(perf)
    return perf_out(perf)


@router.put("/{perf_id}", response_model=PerformanceOut)
def update_performance(perf_id: int, body: PerformanceIn,
                       user=Depends(require_hr_admin), db: Session = Depends(get_db)):
    perf = db.get(PerformanceReview, perf_id)
    if not perf:
        raise HTTPException(status_code=404, detail="绩效记录不存在")
    if not (0 <= body.score <= 100):
        raise HTTPException(status_code=400, detail="评分范围为 0-100")
    perf.score = body.score
    perf.level = level_of(body.score)
    perf.comment = body.comment
    db.commit()
    db.refresh(perf)
    return perf_out(perf)


@router.delete("/{perf_id}")
def delete_performance(perf_id: int, user=Depends(require_hr_admin),
                       db: Session = Depends(get_db)):
    perf = db.get(PerformanceReview, perf_id)
    if not perf:
        raise HTTPException(status_code=404, detail="绩效记录不存在")
    db.delete(perf)
    db.commit()
    return {"message": "删除成功"}
