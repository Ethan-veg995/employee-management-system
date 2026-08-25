from datetime import date, datetime
from typing import Optional, List

from pydantic import BaseModel


# ---------- 通用 ----------
class UserOut(BaseModel):
    id: int
    username: str
    role: str
    employee_id: Optional[int] = None

    class Config:
        from_attributes = True


class LoginIn(BaseModel):
    username: str
    password: str


class LoginOut(BaseModel):
    token: str
    user: UserOut


# ---------- 部门 ----------
class DepartmentIn(BaseModel):
    name: str
    description: str = ""


class DepartmentOut(BaseModel):
    id: int
    name: str
    description: str = ""
    employee_count: int = 0

    class Config:
        from_attributes = True


# ---------- 职位 ----------
class PositionIn(BaseModel):
    name: str
    department_id: int
    level: str = "初级"


class PositionOut(BaseModel):
    id: int
    name: str
    department_id: int
    department_name: str = ""
    level: str = ""

    class Config:
        from_attributes = True


# ---------- 员工 ----------
class EmployeeIn(BaseModel):
    name: str
    employee_no: str
    gender: str = "男"
    phone: str = ""
    email: str = ""
    department_id: int
    position_id: int
    hire_date: date
    status: str = "在职"


class EmployeeUpdate(BaseModel):
    name: Optional[str] = None
    gender: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    department_id: Optional[int] = None
    position_id: Optional[int] = None
    hire_date: Optional[date] = None
    status: Optional[str] = None


class EmployeeOut(BaseModel):
    id: int
    name: str
    employee_no: str
    gender: str
    phone: str
    email: str
    department_id: int
    department_name: str = ""
    position_id: int
    position_name: str = ""
    hire_date: date
    status: str

    class Config:
        from_attributes = True


# ---------- 考勤 ----------
class AttendanceRuleIn(BaseModel):
    work_start: str
    work_end: str
    late_tolerance_minutes: int


class AttendanceRuleOut(BaseModel):
    id: int
    work_start: str
    work_end: str
    late_tolerance_minutes: int

    class Config:
        from_attributes = True


class PunchIn(BaseModel):
    type: str  # check_in / check_out


class AttendanceOut(BaseModel):
    id: int
    employee_id: int
    employee_name: str = ""
    date: date
    check_in: Optional[str] = None
    check_out: Optional[str] = None
    status: str = ""

    class Config:
        from_attributes = True


# ---------- 审批 ----------
class ApprovalIn(BaseModel):
    request_type: str          # 请假/加班/报销/出差
    title: str
    leave_type: Optional[str] = None
    amount: Optional[float] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    reason: str = ""


class ApproveIn(BaseModel):
    action: str  # 通过 / 驳回
    comment: str = ""


class ApprovalOut(BaseModel):
    id: int
    employee_id: int
    employee_name: str = ""
    department_name: str = ""
    request_type: str
    title: str
    leave_type: Optional[str] = None
    amount: Optional[float] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    days: Optional[float] = None
    reason: str
    status: str
    approve_comment: str = ""
    approver_name: str = ""
    created_at: datetime

    class Config:
        from_attributes = True


# ---------- 消息通知 ----------
class NotificationOut(BaseModel):
    id: int
    type: str
    title: str
    content: str = ""
    related_id: Optional[int] = None
    is_read: int
    created_at: datetime

    class Config:
        from_attributes = True


# ---------- 绩效 ----------
class PerformanceIn(BaseModel):
    employee_id: int
    year: int
    month: int
    score: float
    comment: str = ""


class PerformanceOut(BaseModel):
    id: int
    employee_id: int
    employee_name: str = ""
    department_name: str = ""
    reviewer_name: str = ""
    year: int
    month: int
    score: float
    level: str
    comment: str = ""

    class Config:
        from_attributes = True


# ---------- 公告 ----------
class AnnouncementIn(BaseModel):
    title: str
    content: str = ""


class AnnouncementOut(BaseModel):
    id: int
    title: str
    content: str = ""
    publisher_name: str = ""
    created_at: datetime

    class Config:
        from_attributes = True


# ---------- 薪资 ----------
class SalaryIn(BaseModel):
    employee_id: int
    year: int
    month: int
    base_salary: float
    bonus: float = 0
    deduction: float = 0


class SalaryOut(BaseModel):
    id: int
    employee_id: int
    employee_name: str = ""
    employee_no: str = ""
    department_name: str = ""
    year: int
    month: int
    base_salary: float
    bonus: float
    deduction: float
    actual_salary: float

    class Config:
        from_attributes = True


# ---------- 用户 ----------
class UserIn(BaseModel):
    username: str
    password: str
    role: str
    employee_id: Optional[int] = None


class UserUpdate(BaseModel):
    password: Optional[str] = None
    role: Optional[str] = None
    employee_id: Optional[int] = None


class UserDetailOut(BaseModel):
    id: int
    username: str
    role: str
    role_name: str = ""
    employee_id: Optional[int] = None
    employee_name: str = ""
    created_at: datetime

    class Config:
        from_attributes = True


# ---------- 看板 ----------
class ChartItem(BaseModel):
    name: str
    value: float


class DeptItem(BaseModel):
    name: str
    value: int


class SalaryTrendItem(BaseModel):
    month: str
    total: float


class DashboardSummary(BaseModel):
    total_employees: int
    hired_this_month: int
    left_this_month: int
    dept_distribution: List[DeptItem]
    level_distribution: List[ChartItem]
    attendance_rate: float
    last_month_rate: float
    leave_stats: List[ChartItem]
    salary_trend: List[SalaryTrendItem]


class MyDashboard(BaseModel):
    name: str
    employee_no: str
    department: str
    position: str
    today_status: str
    month_attendance: dict
    month_leave_days: float
    latest_salary: Optional[SalaryOut] = None


# ---------- 提醒 ----------
class AlertItem(BaseModel):
    level: str  # warning / danger
    title: str
    detail: str
    employee_id: Optional[int] = None
    employee_name: str = ""
