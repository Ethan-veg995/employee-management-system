"""测试公共设施：内存数据库 + 测试客户端 + 最小种子数据 + 登录辅助

用法（在 backend 目录下执行）：
    pip install -r requirements-dev.txt
    pytest
"""
import sys
from datetime import date
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# 让 `import app` 无论从哪里执行 pytest 都能找到 backend 包
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.auth import hash_password
from app.database import Base, get_db
from app.main import app
from app.models import Department, Employee, Position, User

# 演示账号：用户名 -> 密码（角色与用户名一致）
ACCOUNTS = {
    "admin": "admin123",
    "hr": "hr123",
    "manager": "manager123",
    "employee": "employee123",
}


@pytest.fixture()
def db_session():
    """每个测试独享一个内存数据库，互不影响"""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def seeded(db_session):
    """最小种子数据：
    - 部门：技术部 / 人事部
    - 职位：工程师(技术部) / 人事专员(人事部)
    - 员工：张伟(技术部,id=1) / 赵敏(人事部,id=2) / 李娜(技术部,id=3)
    - 账号：admin / hr(赵敏) / manager(张伟) / employee(李娜)
    """
    tech = Department(name="技术部", description="技术")
    hr_dept = Department(name="人事部", description="人事")
    db_session.add_all([tech, hr_dept])
    db_session.flush()

    pos_tech = Position(name="工程师", department_id=tech.id, level="中级")
    pos_hr = Position(name="人事专员", department_id=hr_dept.id, level="初级")
    db_session.add_all([pos_tech, pos_hr])
    db_session.flush()

    emp_zhang = Employee(name="张伟", employee_no="EMP001", gender="男",
                         department_id=tech.id, position_id=pos_tech.id,
                         hire_date=date(2020, 1, 1), status="在职")
    emp_zhao = Employee(name="赵敏", employee_no="EMP007", gender="女",
                        department_id=hr_dept.id, position_id=pos_hr.id,
                        hire_date=date(2020, 1, 1), status="在职")
    emp_li = Employee(name="李娜", employee_no="EMP002", gender="女",
                      department_id=tech.id, position_id=pos_tech.id,
                      hire_date=date(2020, 1, 1), status="在职")
    db_session.add_all([emp_zhang, emp_zhao, emp_li])
    db_session.flush()

    admin = User(username="admin", password_hash=hash_password("admin123"), role="admin")
    hr = User(username="hr", password_hash=hash_password("hr123"), role="hr",
              employee_id=emp_zhao.id)
    manager = User(username="manager", password_hash=hash_password("manager123"),
                   role="manager", employee_id=emp_zhang.id)
    employee = User(username="employee", password_hash=hash_password("employee123"),
                    role="employee", employee_id=emp_li.id)
    db_session.add_all([admin, hr, manager, employee])
    db_session.commit()
    return {"tech_dept": tech, "hr_dept": hr_dept,
            "emp_zhang": emp_zhang, "emp_zhao": emp_zhao, "emp_li": emp_li}


@pytest.fixture()
def client(db_session):
    """测试客户端：所有接口请求都走内存数据库（替换 get_db 依赖）"""
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    # raise_server_exceptions=False：接口内部异常会变成 500 响应，便于断言
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture()
def login(client):
    """登录辅助：返回带角色 token 的请求头，例如 headers = login("hr")"""
    def _login(username: str) -> dict:
        pwd = ACCOUNTS[username]
        r = client.post("/api/v1/auth/login", json={"username": username, "password": pwd})
        assert r.status_code == 200, f"登录失败 {username}: {r.text}"
        return {"Authorization": f"Bearer {r.json()['token']}"}

    return _login
