from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)
DB_PATH = DATA_DIR / "ems.db"

# 演示项目密钥，正式环境应通过环境变量注入
SECRET_KEY = "ems-demo-secret-key-2026"
ALGORITHM = "HS256"
TOKEN_EXPIRE_HOURS = 12

ROLES = ["admin", "hr", "manager", "employee"]
ROLE_NAMES = {"admin": "系统管理员", "hr": "HR", "manager": "部门主管", "employee": "普通员工"}

# 请假年额度（天）：用于智能提醒
LEAVE_QUOTA = {"年假": 5, "事假": 10}

# 部门出勤率预警阈值
ATTENDANCE_WARN_RATE = 0.90

# 审批申请类型
REQUEST_TYPES = ["请假", "加班", "报销", "出差"]
LEAVE_TYPES = ["事假", "病假", "年假", "调休", "婚假"]

# 绩效等级映射：score 分数 → 等级 → 绩效系数（绩效奖金 = 系数 × 基本工资 × PERF_BONUS_RATE）
PERF_LEVELS = [("S", 90), ("A", 80), ("B", 70), ("C", 0)]
PERF_COEFF = {"S": 1.5, "A": 1.2, "B": 1.0, "C": 0.6}
PERF_BONUS_RATE = 0.2
