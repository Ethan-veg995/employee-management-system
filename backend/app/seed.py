"""种子数据脚本：清空并重建演示数据库（python seed.py）
提供 4 个演示账号：admin/hr/manager/employee（密码见 USER_ACCOUNTS）
"""
import random
from datetime import date, datetime, timedelta

from app.database import Base, SessionLocal, engine
from app.auth import hash_password
from app.models import (Announcement, ApprovalRequest, AttendanceRecord,
                        AttendanceRule, Department, Employee, Notification,
                        PerformanceReview, Position, Salary, User)

rng = random.Random(42)

DEPARTMENTS = ["技术部", "人事部", "财务部", "市场部", "运营部"]

POSITIONS = {
    "技术部": [("后端工程师", "中级"), ("前端工程师", "初级"), ("技术总监", "资深"), ("测试工程师", "初级")],
    "人事部": [("人事专员", "初级"), ("HR经理", "高级")],
    "财务部": [("会计", "中级"), ("财务经理", "高级")],
    "市场部": [("市场专员", "初级"), ("市场经理", "高级")],
    "运营部": [("运营专员", "初级"), ("运营经理", "高级")],
}

# (姓名, 部门, 职位, 工号, 入职日期, 状态, 性别)
EMPLOYEES = [
    ("张伟", "技术部", "技术总监", "EMP001", "2019-03-11", "在职", "男"),
    ("王芳", "技术部", "后端工程师", "EMP002", "2020-06-15", "在职", "女"),
    ("李娜", "技术部", "前端工程师", "EMP003", "2021-09-01", "在职", "女"),
    ("刘强", "技术部", "后端工程师", "EMP004", "2022-02-20", "在职", "男"),
    ("陈静", "技术部", "测试工程师", "EMP005", "2023-04-10", "在职", "女"),
    ("杨洋", "技术部", "前端工程师", "EMP006", "2024-01-08", "在职", "男"),
    ("赵敏", "人事部", "HR经理", "EMP007", "2020-08-17", "在职", "女"),
    ("黄磊", "人事部", "人事专员", "EMP008", "2023-03-06", "在职", "男"),
    ("周涛", "财务部", "财务经理", "EMP009", "2019-11-25", "在职", "男"),
    ("吴倩", "财务部", "会计", "EMP010", "2021-07-12", "在职", "女"),
    ("徐明", "市场部", "市场经理", "EMP011", "2020-05-18", "在职", "男"),
    ("孙悦", "市场部", "市场专员", "EMP012", "2023-10-09", "在职", "女"),
    ("马超", "运营部", "运营经理", "EMP013", "2021-12-01", "在职", "男"),
    ("朱琳", "运营部", "运营专员", "EMP014", "2024-04-15", "在职", "女"),
    ("胡军", "市场部", "市场专员", "EMP015", "2022-09-05", "离职", "男"),
    ("林芳", "运营部", "运营专员", "EMP016", "2023-06-20", "离职", "女"),
]

# 演示账号：(用户名, 密码, 角色, 关联员工姓名)
USER_ACCOUNTS = [
    ("admin", "admin123", "admin", None),
    ("hr", "hr123", "hr", "赵敏"),
    ("manager", "manager123", "manager", "张伟"),
    ("employee", "employee123", "employee", "李娜"),
]

LEVEL_BASE = {"初级": 6000, "中级": 9000, "高级": 13000, "资深": 17000}


def workdays_between(start: date, end: date) -> list[date]:
    days = []
    d = start
    while d <= end:
        if d.weekday() < 5 and d != date.today():
            days.append(d)
        d += timedelta(days=1)
    return days


def seed():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    # 考勤规则
    db.add(AttendanceRule(id=1, work_start="09:00", work_end="18:00", late_tolerance_minutes=10))

    # 部门 & 职位
    dept_ids = {}
    for name in DEPARTMENTS:
        d = Department(name=name, description=f"{name}负责公司相关业务")
        db.add(d)
        db.flush()
        dept_ids[name] = d.id
        for pos_name, level in POSITIONS[name]:
            db.add(Position(name=pos_name, department_id=d.id, level=level))

    # 员工
    emp_ids = {}
    for name, dept, pos, no, hire, status, gender in EMPLOYEES:
        pos_obj = db.query(Position).filter(Position.name == pos, Position.department_id == dept_ids[dept]).first()
        e = Employee(name=name, employee_no=no, gender=gender, phone=f"138{rng.randint(10000000, 99999999)}",
                     email=f"{name}@example.com", department_id=dept_ids[dept],
                     position_id=pos_obj.id, hire_date=datetime.strptime(hire, "%Y-%m-%d").date(),
                     status=status)
        db.add(e)
        db.flush()
        emp_ids[name] = e.id

    # 账号
    user_ids = {}
    for username, password, role, emp_name in USER_ACCOUNTS:
        u = User(username=username, password_hash=hash_password(password), role=role,
                 employee_id=emp_ids.get(emp_name) if emp_name else None)
        db.add(u)
        db.flush()
        user_ids[username] = u.id

    # 考勤记录：最近3个月的工作日（不含今天），带一些迟到/早退/缺卡
    today = date.today()
    for emp_name, dept, pos, no, hire, status, gender in EMPLOYEES:
        if status != "在职":
            continue
        eid = emp_ids[emp_name]
        for d in workdays_between(today - timedelta(days=92), today - timedelta(days=1)):
            r = rng.random()
            if r < 0.08:      # 迟到
                check_in = f"{rng.choice([9, 10]):02d}:{rng.randint(11, 50):02d}"
                check_out = f"{rng.randint(17, 19):02d}:{rng.randint(0, 59):02d}"
                status_str = "迟到"
            elif r < 0.13:    # 早退
                check_in = f"{rng.randint(8, 9):02d}:{rng.randint(5, 55):02d}"
                check_out = f"{rng.choice([16, 17]):02d}:{rng.randint(0, 55):02d}"
                status_str = "早退"
            elif r < 0.15:    # 缺卡（只打了上班卡）
                check_in = f"{rng.randint(8, 9):02d}:{rng.randint(5, 55):02d}"
                check_out = None
                status_str = "缺卡"
            else:             # 正常
                check_in = f"{rng.randint(8, 9):02d}:{rng.randint(5, 55):02d}"
                check_out = f"{rng.randint(18, 19):02d}:{rng.randint(0, 59):02d}"
                status_str = "正常"
            db.add(AttendanceRecord(employee_id=eid, date=d, check_in=check_in,
                                    check_out=check_out, status=status_str))

    # 通用审批记录：请假/加班/报销/出差
    today = date.today()
    approvals = [
        # (员工, 类型, 标题, 请假类型/金额, 起, 止, 事由, 状态)
        ("李娜", "请假", "年度年假出行", ("年假", None), today - timedelta(days=45), today - timedelta(days=43), "外出旅行", "已通过"),
        ("王芳", "请假", "处理家事", ("事假", None), today - timedelta(days=20), today - timedelta(days=19), "家里有事需要处理", "已通过"),
        ("李娜", "请假", "第二次年假", ("年假", None), today - timedelta(days=10), today - timedelta(days=8), "外出旅行", "已通过"),
        ("陈静", "请假", "感冒请假", ("病假", None), today + timedelta(days=1), today + timedelta(days=2), "感冒发烧需要休息", "待审批"),
        ("刘强", "请假", "调休", ("调休", None), today - timedelta(days=5), today - timedelta(days=5), "周末加班调休", "已驳回"),
        ("王芳", "请假", "探亲", ("年假", None), today - timedelta(days=60), today - timedelta(days=58), "回老家探亲", "已通过"),
        ("黄磊", "请假", "办理个人事务", ("事假", None), today - timedelta(days=3), today - timedelta(days=2), "办理个人事务", "已通过"),
        ("吴倩", "请假", "身体不适", ("病假", None), today - timedelta(days=15), today - timedelta(days=14), "身体不适", "已通过"),
        ("朱琳", "请假", "婚假申请", ("婚假", None), today + timedelta(days=5), today + timedelta(days=9), "结婚休婚假", "待审批"),
        ("王芳", "报销", "项目打车报销", (None, 520.0), None, None, "项目联调期间往返打车", "已通过"),
        ("杨洋", "加班", "版本上线加班", (None, None), today - timedelta(days=2), today - timedelta(days=2), "配合 v1.2 版本上线", "待审批"),
        ("张伟", "出差", "客户现场支持", (None, None), today - timedelta(days=25), today - timedelta(days=22), "客户现场技术支持", "已通过"),
    ]
    for name, rtype, title, extra, start, end, reason, status in approvals:
        if rtype == "请假":
            leave_type, amount = extra
        elif rtype == "报销":
            leave_type, amount = None, extra[1]
        else:
            leave_type, amount = None, None
        days = (end - start).days + 1 if start and end else None
        db.add(ApprovalRequest(
            employee_id=emp_ids[name], request_type=rtype, title=title,
            leave_type=leave_type, amount=amount, start_date=start, end_date=end,
            days=days, reason=reason, status=status,
            approver_id=user_ids.get("manager") if status == "已通过" else None,
            approved_at=datetime.now() if status == "已通过" else None))

    # 绩效：本月全部在职员工（HR 评分）
    cur_y, cur_m = today.year, today.month
    for emp_name, dept, pos, no, hire, status, gender in EMPLOYEES:
        if status != "在职":
            continue
        score = rng.randint(72, 96)
        level = "S" if score >= 90 else "A" if score >= 80 else "B" if score >= 70 else "C"
        db.add(PerformanceReview(
            employee_id=emp_ids[emp_name], reviewer_id=user_ids["hr"],
            year=cur_y, month=cur_m, score=score, level=level,
            comment=rng.choice(["工作认真负责，完成质量高", "表现稳定，交付及时",
                                "团队协作良好", "本月亮点突出，主动承担任务"])))

    # 公告
    announcements = [
        ("关于 2026 年中秋节放假安排的通知",
         "根据国家法定节假日规定，中秋节 9 月 26 日（周六）至 9 月 28 日（周一）放假调休，共 3 天。9 月 29 日（周二）正常上班。祝大家中秋快乐！"),
        ("新版考勤制度宣导",
         "为进一步规范考勤管理，自本月起：1. 上班打卡时间为 09:00，容忍 10 分钟；2. 请假需提前 1 天提交申请；3. 出差需在系统内提交出差申请并审批通过。请各部门同事知悉并遵守。"),
        ("公司内部培训计划（第三季度）",
         "第三季度培训安排：9 月将举办《高效沟通》专题培训（全体成员）、10 月《项目管理基础》（骨干成员）。具体时间另行通知，欢迎大家踊跃报名。"),
    ]
    for title, content in announcements:
        db.add(Announcement(title=title, content=content, publisher_id=user_ids["hr"]))

    # 通知：给演示账号预置几条，让铃铛有未读红点
    notifs = [
        (user_ids["employee"], "announcement", "新公告发布", "「关于 2026 年中秋节放假安排的通知」已发布，请及时查看", 1, 0),
        (user_ids["employee"], "result", "请假申请已通过", "「年度年假出行」审批结果：已通过，意见：同意", None, 1),
        (user_ids["manager"], "todo", "新的请假申请待审批", "陈静 提交了「感冒请假」，请及时处理", 4, 0),
        (user_ids["manager"], "todo", "新的加班申请待审批", "杨洋 提交了「版本上线加班」，请及时处理", 11, 0),
        (user_ids["hr"], "announcement", "新公告发布", "「新版考勤制度宣导」已发布，请及时查看", 2, 1),
    ]
    for uid, ntype, title, content, related, is_read in notifs:
        db.add(Notification(user_id=uid, type=ntype, title=title, content=content,
                            related_id=related, is_read=is_read))

    # 薪资：最近6个月
    for emp_name, dept, pos, no, hire, status, gender in EMPLOYEES:
        eid = emp_ids[emp_name]
        pos_obj = db.query(Position).filter(Position.name == pos).first()
        base = LEVEL_BASE.get(pos_obj.level, 6000)
        if dept == "技术部":
            base += 2000
        y, m = today.year, today.month
        for _ in range(6):
            bonus = round(rng.choice([0, 500, 1000, 1500, 2000]) * (1 + rng.random()), 2) if status == "在职" else 0
            deduction = rng.choice([0, 0, 0, 200, 350])
            db.add(Salary(employee_id=eid, year=y, month=m, base_salary=base, bonus=bonus,
                          deduction=deduction, actual_salary=round(base + bonus - deduction, 2)))
            m -= 1
            if m == 0:
                y, m = y - 1, 12

    db.commit()
    print("✅ 种子数据初始化完成")
    print("演示账号：admin/admin123  hr/hr123  manager/manager123  employee/employee123")


if __name__ == "__main__":
    seed()
