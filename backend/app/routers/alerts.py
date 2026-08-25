from collections import defaultdict
from datetime import date, datetime

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..auth import require_hr
from ..config import LEAVE_QUOTA, ATTENDANCE_WARN_RATE
from ..database import get_db
from ..models import ApprovalRequest, AttendanceRecord, Department, Employee
from ..routers.attendance import employee_month_stats
from ..schemas import AlertItem

router = APIRouter(prefix="/alerts", tags=["智能提醒"], dependencies=[Depends(require_hr)])


@router.get("", response_model=list[AlertItem])
def get_alerts(db: Session = Depends(get_db)):
    alerts: list[AlertItem] = []
    now = datetime.now()
    cur_y, cur_m = now.year, now.month
    emp_name = {e.id: e.name for e in db.query(Employee).all()}

    # 规则1：本月连续3天及以上迟到
    records = (db.query(AttendanceRecord)
               .filter(AttendanceRecord.date >= date(cur_y, cur_m, 1),
                       AttendanceRecord.date <= date.today())
               .order_by(AttendanceRecord.date).all())
    by_emp: dict[int, list[AttendanceRecord]] = defaultdict(list)
    for r in records:
        by_emp[r.employee_id].append(r)
    for emp_id, rs in by_emp.items():
        run = 0
        prev_date = None
        for r in rs:
            if r.status == "迟到":
                if prev_date and (r.date - prev_date).days <= 3:
                    run += 1
                else:
                    run = 1
            else:
                run = 0
            prev_date = r.date
            if run >= 3:
                alerts.append(AlertItem(
                    level="danger",
                    title="连续迟到提醒",
                    detail=f"本月已连续 {run} 天迟到（最近 {r.date}），请关注考勤纪律",
                    employee_id=emp_id, employee_name=emp_name.get(emp_id, ""),
                ))
                run = 0

    # 规则2：本月缺卡 >= 3 次
    for emp_id, rs in by_emp.items():
        missing = sum(1 for r in rs if r.check_in and not r.check_out)
        if missing >= 3:
            alerts.append(AlertItem(
                level="warning",
                title="缺卡提醒",
                detail=f"本月已缺卡 {missing} 次（只打上班卡未打下班卡）",
                employee_id=emp_id, employee_name=emp_name.get(emp_id, ""),
            ))

    # 规则3：请假超年度额度
    quota_rows = (db.query(ApprovalRequest)
                  .filter(ApprovalRequest.request_type == "请假",
                          ApprovalRequest.status == "已通过",
                          ApprovalRequest.start_date >= date(cur_y, 1, 1),
                          ApprovalRequest.start_date <= date(cur_y, 12, 31))
                  .all())
    quota_used = defaultdict(lambda: defaultdict(float))
    for r in quota_rows:
        quota_used[r.employee_id][r.leave_type or ""] += r.days or 0
    for emp_id, usage in quota_used.items():
        for leave_type, days in usage.items():
            if leave_type in LEAVE_QUOTA and days > LEAVE_QUOTA[leave_type]:
                alerts.append(AlertItem(
                    level="warning",
                    title="请假额度超限",
                    detail=f"本年度{leave_type}已休 {days} 天，超过额度 {LEAVE_QUOTA[leave_type]} 天",
                    employee_id=emp_id, employee_name=emp_name.get(emp_id, ""),
                ))

    # 规则4：部门出勤率低于阈值
    dept_map = {d.id: d.name for d in db.query(Department).all()}
    dept_stats: dict[int, dict] = defaultdict(lambda: {"attended": 0, "base": 0})
    active_emps = db.query(Employee).filter(Employee.status == "在职").all()
    for emp in active_emps:
        s = employee_month_stats(db, emp.id, cur_y, cur_m)
        dept_stats[emp.department_id]["attended"] += s["attended"]
        dept_stats[emp.department_id]["base"] += max(1, s["workdays"] - s["leave_days"])
    for dept_id, st in dept_stats.items():
        rate = st["attended"] / st["base"] if st["base"] else 1
        if rate < ATTENDANCE_WARN_RATE:
            alerts.append(AlertItem(
                level="warning",
                title="部门出勤率偏低",
                detail=f"{dept_map.get(dept_id, '未知部门')} 本月出勤率 {rate * 100:.1f}%，低于阈值 {ATTENDANCE_WARN_RATE * 100:.0f}%",
            ))

    return alerts
