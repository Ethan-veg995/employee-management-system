import calendar
from datetime import date, datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..auth import require_hr, require_login
from ..database import get_db
from ..models import ApprovalRequest, AttendanceRecord, AttendanceRule, Employee
from ..schemas import AttendanceOut, AttendanceRuleIn, AttendanceRuleOut, PunchIn

router = APIRouter(prefix="/attendance", tags=["考勤管理"])


def get_rule(db: Session) -> AttendanceRule:
    rule = db.get(AttendanceRule, 1)
    if not rule:
        rule = AttendanceRule(id=1, work_start="09:00", work_end="18:00", late_tolerance_minutes=10)
        db.add(rule)
        db.commit()
        db.refresh(rule)
    return rule


def now_str() -> str:
    return datetime.now().strftime("%H:%M")


def compute_status(rule: AttendanceRule, check_in: str, check_out: str | None) -> str:
    if not check_in:
        return "缺卡"
    def to_min(t: str) -> int:
        h, m = t.split(":")
        return int(h) * 60 + int(m)
    late = to_min(check_in) > to_min(rule.work_start) + rule.late_tolerance_minutes
    early = bool(check_out) and to_min(check_out) < to_min(rule.work_end)
    if late:
        return "迟到"
    if early:
        return "早退"
    return "正常"


@router.get("/rules", response_model=AttendanceRuleOut)
def get_rules(user=Depends(require_hr), db: Session = Depends(get_db)):
    return get_rule(db)


@router.put("/rules", response_model=AttendanceRuleOut)
def update_rules(body: AttendanceRuleIn, user=Depends(require_hr), db: Session = Depends(get_db)):
    rule = get_rule(db)
    rule.work_start = body.work_start
    rule.work_end = body.work_end
    rule.late_tolerance_minutes = body.late_tolerance_minutes
    db.commit()
    db.refresh(rule)
    return rule


def punch(user, body: PunchIn, db: Session) -> AttendanceOut:
    if not user.employee_id:
        raise HTTPException(status_code=400, detail="当前账号未关联员工档案")
    rule = get_rule(db)
    today = date.today()
    record = (db.query(AttendanceRecord)
              .filter(AttendanceRecord.employee_id == user.employee_id,
                      AttendanceRecord.date == today)
              .first())
    t = now_str()
    if body.type == "check_in":
        if record and record.check_in:
            raise HTTPException(status_code=400, detail=f"今日已于 {record.check_in} 打卡上班")
        if not record:
            record = AttendanceRecord(employee_id=user.employee_id, date=today,
                                      check_in=t, status=compute_status(rule, t, None))
            db.add(record)
        else:
            record.check_in = t
            record.status = compute_status(rule, t, record.check_out)
        msg = f"上班打卡成功：{t}"
    elif body.type == "check_out":
        if not record or not record.check_in:
            raise HTTPException(status_code=400, detail="尚未打卡上班，无法打下班卡")
        if record.check_out:
            raise HTTPException(status_code=400, detail=f"今日已于 {record.check_out} 打卡下班")
        record.check_out = t
        record.status = compute_status(rule, record.check_in, t)
        msg = f"下班打卡成功：{t}"
    else:
        raise HTTPException(status_code=400, detail="type 仅支持 check_in / check_out")
    db.commit()
    db.refresh(record)
    return {
        "message": msg,
        "record": AttendanceOut(id=record.id, employee_id=record.employee_id,
                                date=record.date, check_in=record.check_in,
                                check_out=record.check_out, status=record.status).model_dump(),
    }


@router.post("/punch")
def punch_clock(body: PunchIn, user=Depends(require_login), db: Session = Depends(get_db)):
    return punch(user, body, db)


def month_range(month_str: str) -> tuple[int, int]:
    try:
        y, m = month_str.split("-")
        y, m = int(y), int(m)
    except Exception:
        raise HTTPException(status_code=400, detail="月份格式应为 YYYY-MM")
    if not (1 <= m <= 12):
        raise HTTPException(status_code=400, detail="月份格式应为 YYYY-MM")
    return y, m


def workdays_in_month(y: int, m: int) -> int:
    count = 0
    for day in range(1, calendar.monthrange(y, m)[1] + 1):
        if date(y, m, day).weekday() < 5:
            count += 1
    return count


def employee_month_stats(db: Session, emp_id: int, y: int, m: int) -> dict:
    start = date(y, m, 1)
    end = date(y, m, calendar.monthrange(y, m)[1])
    records = (db.query(AttendanceRecord)
               .filter(AttendanceRecord.employee_id == emp_id,
                       AttendanceRecord.date >= start,
                       AttendanceRecord.date <= end)
               .all())
    attended = len({r.date for r in records if r.check_in})
    late = sum(1 for r in records if r.status == "迟到")
    early = sum(1 for r in records if r.status == "早退")
    missing = sum(1 for r in records if r.check_in and not r.check_out)
    leave_days = sum(
        r.days or 0 for r in db.query(ApprovalRequest).filter(
            ApprovalRequest.employee_id == emp_id,
            ApprovalRequest.request_type == "请假",
            ApprovalRequest.status == "已通过",
            ApprovalRequest.start_date <= end,
            ApprovalRequest.end_date >= start,
        ).all()
    )
    workdays = workdays_in_month(y, m)
    rate = round(attended / max(1, workdays - leave_days) * 100, 1)
    return {
        "workdays": workdays, "attended": attended, "late": late, "early": early,
        "missing_punch": missing, "leave_days": leave_days,
        "absent": max(0, workdays - attended - leave_days), "rate": rate,
    }


@router.get("/my")
def my_attendance(month: str = "", user=Depends(require_login), db: Session = Depends(get_db)):
    if not user.employee_id:
        raise HTTPException(status_code=400, detail="当前账号未关联员工档案")
    y, m = month_range(month or datetime.now().strftime("%Y-%m"))
    start, end = date(y, m, 1), date(y, m, calendar.monthrange(y, m)[1])
    records = (db.query(AttendanceRecord)
               .filter(AttendanceRecord.employee_id == user.employee_id,
                       AttendanceRecord.date >= start,
                       AttendanceRecord.date <= end)
               .order_by(AttendanceRecord.date).all())
    return {"month": f"{y}-{m:02d}", "stats": employee_month_stats(db, user.employee_id, y, m),
            "records": [AttendanceOut(id=r.id, employee_id=r.employee_id,
                                      employee_name=user.employee.name if user.employee else "",
                                      date=r.date, check_in=r.check_in,
                                      check_out=r.check_out, status=r.status).model_dump()
                        for r in records]}


@router.get("/records")
def attendance_records(month: str = "", department_id: int | None = None,
                       employee_id: int | None = None,
                       user=Depends(require_hr), db: Session = Depends(get_db)):
    y, m = month_range(month or datetime.now().strftime("%Y-%m"))
    start, end = date(y, m, 1), date(y, m, calendar.monthrange(y, m)[1])
    q = db.query(AttendanceRecord).filter(AttendanceRecord.date >= start,
                                          AttendanceRecord.date <= end)
    if employee_id:
        q = q.filter(AttendanceRecord.employee_id == employee_id)
    elif department_id:
        q = q.join(Employee).filter(Employee.department_id == department_id)
    records = q.order_by(AttendanceRecord.date, AttendanceRecord.employee_id).all()
    return [AttendanceOut(id=r.id, employee_id=r.employee_id,
                          employee_name=r.employee.name if r.employee else "",
                          date=r.date, check_in=r.check_in, check_out=r.check_out,
                          status=r.status).model_dump() for r in records]


@router.get("/monthly")
def monthly_stats(month: str = "", department_id: int | None = None,
                  user=Depends(require_hr), db: Session = Depends(get_db)):
    y, m = month_range(month or datetime.now().strftime("%Y-%m"))
    q = db.query(Employee).filter(Employee.status == "在职")
    if department_id:
        q = q.filter(Employee.department_id == department_id)
    emps = q.order_by(Employee.id).all()
    rows = []
    for emp in emps:
        s = employee_month_stats(db, emp.id, y, m)
        rows.append({
            "employee_id": emp.id, "employee_name": emp.name, "employee_no": emp.employee_no,
            "department": emp.department.name if emp.department else "", **s,
        })
    return {"month": f"{y}-{m:02d}", "items": rows}
