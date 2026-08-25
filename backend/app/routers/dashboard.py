import calendar
from collections import defaultdict
from datetime import date, datetime

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..auth import require_hr, require_login
from ..database import get_db
from ..models import (ApprovalRequest, AttendanceRecord, Department,
                      Employee, Position, Salary)
from ..routers.attendance import employee_month_stats
from ..routers.salaries import salary_out
from ..schemas import ChartItem, DeptItem, MyDashboard, SalaryTrendItem, DashboardSummary

router = APIRouter(prefix="/dashboard", tags=["数据看板"])


def ym_str(d: date) -> str:
    return f"{d.year}-{d.month:02d}"


def month_bounds(offset: int = 0) -> tuple[date, date]:
    now = datetime.now()
    y, m = now.year, now.month
    for _ in range(abs(offset)):
        if offset > 0:
            m -= 1
        else:
            m += 1
        if m == 0:
            y, m = y - 1, 12
        elif m == 13:
            y, m = y + 1, 1
    start = date(y, m, 1)
    end = date(y, m, calendar.monthrange(y, m)[1])
    return start, end


def overall_rate(db: Session, start: date, end: date, dept_id: int | None = None) -> float:
    q = db.query(Employee).filter(Employee.status == "在职")
    if dept_id:
        q = q.filter(Employee.department_id == dept_id)
    emps = q.all()
    if not emps:
        return 0
    total_attended = 0
    total_base = 0
    for emp in emps:
        s = employee_month_stats(db, emp.id, start.year, start.month)
        total_attended += s["attended"]
        total_base += max(1, s["workdays"] - s["leave_days"])
    return round(total_attended / total_base * 100, 1)


@router.get("/summary", response_model=DashboardSummary)
def summary(user=Depends(require_hr), db: Session = Depends(get_db)):
    now = datetime.now()
    cur_start, cur_end = month_bounds(0)
    last_start, last_end = month_bounds(1)

    employees = db.query(Employee).all()
    active = [e for e in employees if e.status == "在职"]

    hired = sum(1 for e in employees if e.hire_date.year == now.year and e.hire_date.month == now.month)
    left = sum(1 for e in employees if e.status == "离职")

    dept_map = {d.id: d.name for d in db.query(Department).all()}
    dept_count = defaultdict(int)
    for e in active:
        dept_count[e.department_id] += 1
    dept_distribution = [DeptItem(name=dept_map.get(k, "未知"), value=v)
                         for k, v in sorted(dept_count.items())]

    level_map = {p.id: p.level for p in db.query(Position).all()}
    level_count = defaultdict(int)
    for e in active:
        level_count[level_map.get(e.position_id, "未知")] += 1
    level_distribution = [ChartItem(name=k, value=v) for k, v in level_count.items()]

    attendance_rate = overall_rate(db, cur_start, cur_end)
    last_month_rate = overall_rate(db, last_start, last_end)

    leave_type_count = defaultdict(float)
    leave_rows = (db.query(ApprovalRequest)
                  .filter(ApprovalRequest.request_type == "请假",
                          ApprovalRequest.status == "已通过",
                          ApprovalRequest.start_date <= cur_end,
                          ApprovalRequest.end_date >= cur_start)
                  .all())
    for r in leave_rows:
        leave_type_count[r.leave_type or "其他"] += r.days or 0
    leave_stats = [ChartItem(name=k, value=v) for k, v in leave_type_count.items()]

    trend = []
    for offset in range(5, -1, -1):
        start, end = month_bounds(offset)
        total = db.query(Salary).filter(Salary.year == start.year,
                                        Salary.month == start.month).all()
        trend.append(SalaryTrendItem(month=ym_str(start),
                                     total=round(sum(s.actual_salary for s in total), 2)))

    return DashboardSummary(
        total_employees=len(active),
        hired_this_month=hired,
        left_this_month=left,
        dept_distribution=dept_distribution,
        level_distribution=level_distribution,
        attendance_rate=attendance_rate,
        last_month_rate=last_month_rate,
        leave_stats=leave_stats,
        salary_trend=trend,
    )


@router.get("/my", response_model=MyDashboard)
def my_dashboard(user=Depends(require_login), db: Session = Depends(get_db)):
    if not user.employee_id:
        return MyDashboard(name="", employee_no="", department="", position="",
                           today_status="未关联员工", month_attendance={},
                           month_leave_days=0, latest_salary=None)
    emp = db.get(Employee, user.employee_id)
    now = datetime.now()
    cur_start, cur_end = month_bounds(0)

    today_rec = (db.query(AttendanceRecord)
                 .filter(AttendanceRecord.employee_id == emp.id,
                         AttendanceRecord.date == date.today())
                 .first())
    today_status = "未打卡"
    if today_rec:
        today_status = "缺卡" if (today_rec.check_in and not today_rec.check_out) else (today_rec.status or "已打卡")

    month_attendance = employee_month_stats(db, emp.id, cur_start.year, cur_start.month)

    leave_days = sum((r.days or 0) for r in db.query(ApprovalRequest).filter(
        ApprovalRequest.employee_id == emp.id,
        ApprovalRequest.request_type == "请假",
        ApprovalRequest.status == "已通过",
        ApprovalRequest.start_date <= cur_end,
        ApprovalRequest.end_date >= cur_start,
    ).all())

    latest = (db.query(Salary).filter(Salary.employee_id == emp.id)
              .order_by(Salary.year.desc(), Salary.month.desc()).first())

    return MyDashboard(
        name=emp.name, employee_no=emp.employee_no,
        department=emp.department.name if emp.department else "",
        position=emp.position.name if emp.position else "",
        today_status=today_status,
        month_attendance=month_attendance,
        month_leave_days=leave_days,
        latest_salary=salary_out(latest) if latest else None,
    )
