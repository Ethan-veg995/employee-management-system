"""权限边界体检：验证"收权改造"后的接口角色限制
改造目标：
- admin 只管用户管理（/users），不再管人事业务
- 人事业务接口（employees/departments/positions/salaries/performance/
  announcements 写操作/alerts/attendance/dashboard/approvals 列表等）只允许 hr
- approvals/pending 只允许 manager 和 hr
"""
import pytest

# 只允许 hr 的接口（admin/manager/employee 访问都应 403）
HR_ONLY_GET = [
    "/api/v1/employees",
    "/api/v1/departments",
    "/api/v1/positions",
    "/api/v1/salaries",
    "/api/v1/alerts",
    "/api/v1/dashboard/summary",
    "/api/v1/attendance/rules",
    "/api/v1/attendance/monthly",
    "/api/v1/approvals",
    "/api/v1/performance/suggest?employee_id=3&year=2026&month=8",
]


class Test未登录:
    @pytest.mark.parametrize("path", ["/api/v1/auth/me", "/api/v1/employees", "/api/v1/users", "/api/v1/approvals/pending"])
    def test_未登录访问受保护接口一律401(self, client, seeded, path):
        r = client.get(path)
        assert r.status_code == 401


class Test管理员admin:
    """admin 只保留用户管理权限，人事业务一律 403"""

    def test_admin_可以访问用户管理(self, client, seeded, login):
        r = client.get("/api/v1/users", headers=login("admin"))
        assert r.status_code == 200
        assert len(r.json()) == 4

    @pytest.mark.parametrize("path", HR_ONLY_GET)
    def test_admin_访问人事业务接口一律403(self, client, seeded, login, path):
        r = client.get(path, headers=login("admin"))
        assert r.status_code == 403, f"admin 不应访问 {path}"

    def test_admin_不能发布公告(self, client, seeded, login):
        r = client.post("/api/v1/announcements",
                        json={"title": "测试", "content": ""}, headers=login("admin"))
        assert r.status_code == 403

    def test_admin_不能进行绩效评分(self, client, seeded, login):
        r = client.post("/api/v1/performance",
                        json={"employee_id": 3, "year": 2026, "month": 8, "score": 95},
                        headers=login("admin"))
        assert r.status_code == 403

    def test_admin_不能查看待审批列表(self, client, seeded, login):
        r = client.get("/api/v1/approvals/pending", headers=login("admin"))
        assert r.status_code == 403


class TestHR:
    """hr 是人事业务的主要操作者"""

    @pytest.mark.parametrize("path", HR_ONLY_GET)
    def test_hr_可以访问人事业务接口(self, client, seeded, login, path):
        r = client.get(path, headers=login("hr"))
        assert r.status_code == 200, f"hr 应能访问 {path}，实际 {r.status_code}"

    def test_hr_可以查看待审批列表(self, client, seeded, login):
        r = client.get("/api/v1/approvals/pending", headers=login("hr"))
        assert r.status_code == 200

    def test_hr_可以发布公告(self, client, seeded, login):
        r = client.post("/api/v1/announcements",
                        json={"title": "全员通知", "content": "测试内容"}, headers=login("hr"))
        assert r.status_code == 200

    def test_hr_不能访问用户管理(self, client, seeded, login):
        r = client.get("/api/v1/users", headers=login("hr"))
        assert r.status_code == 403


class Test普通员工employee:
    """员工只能看自己的数据，不能碰任何管理接口"""

    def test_员工_可以看公告(self, client, seeded, login):
        r = client.get("/api/v1/announcements", headers=login("employee"))
        assert r.status_code == 200

    def test_员工_可以看自己的薪资(self, client, seeded, login):
        r = client.get("/api/v1/salaries/my", headers=login("employee"))
        assert r.status_code == 200

    def test_员工_可以看自己的申请(self, client, seeded, login):
        r = client.get("/api/v1/approvals/my", headers=login("employee"))
        assert r.status_code == 200

    def test_员工_可以看自己的考勤(self, client, seeded, login):
        r = client.get("/api/v1/attendance/my", headers=login("employee"))
        assert r.status_code == 200

    def test_员工_可以看自己的绩效(self, client, seeded, login):
        r = client.get("/api/v1/performance/my", headers=login("employee"))
        assert r.status_code == 200

    @pytest.mark.parametrize("path", HR_ONLY_GET + ["/api/v1/users"])
    def test_员工_访问管理接口一律403(self, client, seeded, login, path):
        r = client.get(path, headers=login("employee"))
        assert r.status_code == 403, f"员工不应访问 {path}"

    def test_员工_不能查看待审批列表(self, client, seeded, login):
        r = client.get("/api/v1/approvals/pending", headers=login("employee"))
        assert r.status_code == 403

    def test_员工_不能发布公告(self, client, seeded, login):
        r = client.post("/api/v1/announcements",
                        json={"title": "x", "content": ""}, headers=login("employee"))
        assert r.status_code == 403

    def test_员工_不能进行绩效评分(self, client, seeded, login):
        r = client.post("/api/v1/performance",
                        json={"employee_id": 3, "year": 2026, "month": 8, "score": 95},
                        headers=login("employee"))
        assert r.status_code == 403


class Test主管manager:
    """主管能看本部门待审批，但不能用 hr 的全局接口"""

    def test_主管_可以查看待审批列表(self, client, seeded, login):
        r = client.get("/api/v1/approvals/pending", headers=login("manager"))
        assert r.status_code == 200

    def test_主管_不能查看全局审批列表(self, client, seeded, login):
        r = client.get("/api/v1/approvals", headers=login("manager"))
        assert r.status_code == 403

    def test_主管_不能看全局薪资(self, client, seeded, login):
        r = client.get("/api/v1/salaries", headers=login("manager"))
        assert r.status_code == 403

    def test_主管_不能看数据看板汇总(self, client, seeded, login):
        r = client.get("/api/v1/dashboard/summary", headers=login("manager"))
        assert r.status_code == 403

    def test_主管_可以看自己的薪资(self, client, seeded, login):
        r = client.get("/api/v1/salaries/my", headers=login("manager"))
        assert r.status_code == 200
