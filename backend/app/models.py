from datetime import datetime, date

from sqlalchemy import Column, Integer, String, Float, Date, DateTime, Text, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship

from .database import Base


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    password_hash = Column(String(128), nullable=False)
    role = Column(String(20), nullable=False)  # admin / hr / manager / employee
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.now)

    employee = relationship("Employee", back_populates="user")


class Department(Base):
    __tablename__ = "departments"
    id = Column(Integer, primary_key=True)
    name = Column(String(50), unique=True, nullable=False)
    description = Column(String(200), default="")
    created_at = Column(DateTime, default=datetime.now)

    employees = relationship("Employee", back_populates="department")


class Position(Base):
    __tablename__ = "positions"
    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=False)
    level = Column(String(20), default="初级")  # 初级 / 中级 / 高级 / 资深
    created_at = Column(DateTime, default=datetime.now)

    department = relationship("Department")


class Employee(Base):
    __tablename__ = "employees"
    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False)
    employee_no = Column(String(20), unique=True, nullable=False)
    gender = Column(String(4), default="男")
    phone = Column(String(20), default="")
    email = Column(String(100), default="")
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=False)
    position_id = Column(Integer, ForeignKey("positions.id"), nullable=False)
    hire_date = Column(Date, nullable=False)
    status = Column(String(10), default="在职")  # 在职 / 离职
    created_at = Column(DateTime, default=datetime.now)

    department = relationship("Department", back_populates="employees")
    position = relationship("Position")
    user = relationship("User", back_populates="employee", uselist=False)


class AttendanceRule(Base):
    __tablename__ = "attendance_rules"
    id = Column(Integer, primary_key=True)
    work_start = Column(String(5), default="09:00")
    work_end = Column(String(5), default="18:00")
    late_tolerance_minutes = Column(Integer, default=10)


class AttendanceRecord(Base):
    __tablename__ = "attendance_records"
    id = Column(Integer, primary_key=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    date = Column(Date, nullable=False)
    check_in = Column(String(5), nullable=True)   # "HH:MM"
    check_out = Column(String(5), nullable=True)
    status = Column(String(10), default="正常")    # 正常 / 迟到 / 早退 / 缺卡
    created_at = Column(DateTime, default=datetime.now)

    employee = relationship("Employee")
    __table_args__ = (UniqueConstraint("employee_id", "date", name="uq_att_emp_date"),)


class ApprovalRequest(Base):
    """通用审批申请：请假/加班/报销/出差"""
    __tablename__ = "approval_requests"
    id = Column(Integer, primary_key=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    request_type = Column(String(10), nullable=False)  # 请假/加班/报销/出差
    title = Column(String(100), nullable=False)        # 申请标题
    leave_type = Column(String(20), nullable=True)     # 请假类型（仅请假）
    amount = Column(Float, nullable=True)              # 金额（仅报销）
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)
    days = Column(Float, nullable=True)                # 天数（自然日）
    reason = Column(Text, default="")
    status = Column(String(10), default="待审批")       # 待审批/已通过/已驳回
    approver_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    approve_comment = Column(Text, default="")
    approved_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.now)

    employee = relationship("Employee")
    approver = relationship("User")


class Notification(Base):
    __tablename__ = "notifications"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    type = Column(String(20), default="todo")          # todo待办 / result审批结果 / announcement公告
    title = Column(String(100), nullable=False)
    content = Column(String(300), default="")
    related_id = Column(Integer, nullable=True)        # 关联业务 id（审批单/公告）
    is_read = Column(Integer, default=0)               # 0 未读 / 1 已读
    created_at = Column(DateTime, default=datetime.now)

    user = relationship("User")


class PerformanceReview(Base):
    __tablename__ = "performance_reviews"
    id = Column(Integer, primary_key=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    reviewer_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    year = Column(Integer, nullable=False)
    month = Column(Integer, nullable=False)
    score = Column(Float, nullable=False)              # 0-100
    level = Column(String(2), nullable=False)          # S/A/B/C
    comment = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.now)

    employee = relationship("Employee")
    reviewer = relationship("User")
    __table_args__ = (UniqueConstraint("employee_id", "year", "month", name="uq_perf_emp_ym"),)


class Announcement(Base):
    __tablename__ = "announcements"
    id = Column(Integer, primary_key=True)
    title = Column(String(100), nullable=False)
    content = Column(Text, default="")
    publisher_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.now)

    publisher = relationship("User")


class Salary(Base):
    __tablename__ = "salaries"
    id = Column(Integer, primary_key=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    year = Column(Integer, nullable=False)
    month = Column(Integer, nullable=False)
    base_salary = Column(Float, nullable=False)
    bonus = Column(Float, default=0)
    deduction = Column(Float, default=0)
    actual_salary = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.now)

    employee = relationship("Employee")
    __table_args__ = (UniqueConstraint("employee_id", "year", "month", name="uq_salary_emp_ym"),)
