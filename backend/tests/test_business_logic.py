"""业务逻辑体检：纯函数边界（绩效等级/考勤状态/工作日） + 核心业务流
（打卡、审批、绩效、薪资、公告、用户、员工、部门）
"""
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.routers.attendance import compute_status, month_range, workdays_in_month
from app.routers.performance import level_of


# ---------- 纯函数：绩效分数 -> 等级 ----------
class Test绩效等级:
    @pytest.mark.parametrize("score,level", [
        (100, "S"), (90, "S"),      # 边界：90 分恰好是 S
        (89.9, "A"), (80, "A"),     # 边界：80 分恰好是 A
        (79.9, "B"), (70, "B"),     # 边界：70 分恰好是 B
        (69.9, "C"), (0, "C"),      # 低于 70 一律 C
    ])
    def test_分数映射等级(self, score, level):
        assert level_of(score) == level


# ---------- 纯函数：考勤状态计算 ----------
class Test考勤状态:
    RULE = SimpleNamespace(work_start="09:00", work_end="18:00", late_tolerance_minutes=10)

    def test_正常_准点及容忍范围内不算迟到(self):
        assert compute_status(self.RULE, "08:55", None) == "正常"
        assert compute_status(self.RULE, "09:00", None) == "正常"
        assert compute_status(self.RULE, "09:10", None) == "正常"  # 容忍 10 分钟边界

    def test_迟到_超出容忍时间(self):
        assert compute_status(self.RULE, "09:11", None) == "迟到"
        assert compute_status(self.RULE, "10:00", "18:30") == "迟到"

    def test_早退_下班前离开(self):
        assert compute_status(self.RULE, "09:00", "17:59") == "早退"
        assert compute_status(self.RULE, "09:00", "18:00") == "正常"  # 准点下班不算早退

    def test_缺卡_没有上班打卡(self):
        assert compute_status(self.RULE, None, None) == "缺卡"

    def test_迟到优先于早退(self):
        assert compute_status(self.RULE, "09:11", "17:59") == "迟到"


# ---------- 纯函数：月份解析与工作日统计 ----------
class Test月份工具:
    def test_月份解析_合法输入(self):
        assert month_range("2026-08") == (2026, 8)

    def test_月份解析_格式错误返回400(self):
        with pytest.raises(HTTPException) as exc:
            month_range("abc")
        assert exc.value.status_code == 400

    def test_工作日统计_2026年8月共21个工作日(self):
        assert workdays_in_month(2026, 8) == 21


# ---------- 考勤打卡流程 ----------
class Test打卡流程:
    def test_完整打卡_上班下班成功_重复打卡被拒(self, client, seeded, login):
        h = login("employee")
        r1 = client.post("/api/v1/attendance/punch", json={"type": "check_in"}, headers=h)
        assert r1.status_code == 200
        assert r1.json()["message"].startswith("上班打卡成功")
        assert r1.json()["record"]["check_in"]

        r2 = client.post("/api/v1/attendance/punch", json={"type": "check_in"}, headers=h)
        assert r2.status_code == 400  # 不能重复打上班卡

        r3 = client.post("/api/v1/attendance/punch", json={"type": "check_out"}, headers=h)
        assert r3.status_code == 200
        assert r3.json()["message"].startswith("下班打卡成功")
        assert r3.json()["record"]["check_out"]

        r4 = client.post("/api/v1/attendance/punch", json={"type": "check_out"}, headers=h)
        assert r4.status_code == 400  # 不能重复打下班卡

    def test_未上班卡直接打下班卡被拒(self, client, seeded, login):
        r = client.post("/api/v1/attendance/punch", json={"type": "check_out"},
                        headers=login("employee"))
        assert r.status_code == 400

    def test_未关联员工档案的账号不能打卡(self, client, seeded, login):
        r = client.post("/api/v1/attendance/punch", json={"type": "check_in"},
                        headers=login("admin"))
        assert r.status_code == 400

    def test_非法打卡类型被拒(self, client, seeded, login):
        r = client.post("/api/v1/attendance/punch", json={"type": "sleep"},
                        headers=login("employee"))
        assert r.status_code == 400

    def test_查看当月考勤_返回统计字段(self, client, seeded, login):
        r = client.get("/api/v1/attendance/my", headers=login("employee"))
        assert r.status_code == 200
        stats = r.json()["stats"]
        for key in ("workdays", "attended", "late", "early", "absent", "rate"):
            assert key in stats

    def test_查看考勤_月份格式错误返回400(self, client, seeded, login):
        r = client.get("/api/v1/attendance/my?month=abc", headers=login("employee"))
        assert r.status_code == 400

    def test_查看考勤_月份越界应返回400(self, client, seeded, login):
        """已知缺陷：month=2026-13 目前会 500（calendar.monthrange 崩），应返回 400"""
        r = client.get("/api/v1/attendance/my?month=2026-13", headers=login("employee"))
        assert r.status_code == 400


# ---------- 薪资 ----------
class Test薪资:
    def test_新增薪资_实发金额自动计算(self, client, seeded, login):
        r = client.post("/api/v1/salaries",
                        json={"employee_id": 3, "year": 2026, "month": 8,
                              "base_salary": 10000, "bonus": 500.5, "deduction": 200},
                        headers=login("hr"))
        assert r.status_code == 200
        body = r.json()
        assert body["actual_salary"] == 10300.5  # 10000 + 500.5 - 200

    def test_新增薪资_同员工同月份重复被拒(self, client, seeded, login):
        data = {"employee_id": 3, "year": 2026, "month": 8, "base_salary": 10000}
        assert client.post("/api/v1/salaries", json=data, headers=login("hr")).status_code == 200
        r = client.post("/api/v1/salaries", json=data, headers=login("hr"))
        assert r.status_code == 400

    def test_新增薪资_员工不存在被拒(self, client, seeded, login):
        r = client.post("/api/v1/salaries",
                        json={"employee_id": 999, "year": 2026, "month": 8,
                              "base_salary": 10000},
                        headers=login("hr"))
        assert r.status_code == 400

    def test_修改薪资_实发金额重新计算(self, client, seeded, login):
        r = client.post("/api/v1/salaries",
                        json={"employee_id": 3, "year": 2026, "month": 8,
                              "base_salary": 10000, "bonus": 0, "deduction": 0},
                        headers=login("hr"))
        sid = r.json()["id"]
        r2 = client.put(f"/api/v1/salaries/{sid}",
                        json={"employee_id": 3, "year": 2026, "month": 8,
                              "base_salary": 8000, "bonus": 0, "deduction": 100},
                        headers=login("hr"))
        assert r2.status_code == 200
        assert r2.json()["actual_salary"] == 7900

    def test_员工查看自己的薪资列表(self, client, seeded, login):
        client.post("/api/v1/salaries",
                    json={"employee_id": 3, "year": 2026, "month": 8, "base_salary": 10000},
                    headers=login("hr"))
        r = client.get("/api/v1/salaries/my", headers=login("employee"))
        assert r.status_code == 200
        assert len(r.json()) == 1
        assert r.json()[0]["employee_id"] == 3


# ---------- 审批申请 ----------
class Test审批申请:
    def test_提交请假_天数自动计算(self, client, seeded, login):
        r = client.post("/api/v1/approvals",
                        json={"request_type": "请假", "title": "年度年假",
                              "leave_type": "年假",
                              "start_date": "2026-09-01", "end_date": "2026-09-03"},
                        headers=login("employee"))
        assert r.status_code == 200
        assert r.json()["days"] == 3
        assert r.json()["status"] == "待审批"

    def test_提交请假_结束日期早于开始日期被拒(self, client, seeded, login):
        r = client.post("/api/v1/approvals",
                        json={"request_type": "请假", "title": "x", "leave_type": "年假",
                              "start_date": "2026-09-03", "end_date": "2026-09-01"},
                        headers=login("employee"))
        assert r.status_code == 400

    def test_提交请假_时间重叠被拒(self, client, seeded, login):
        h = login("employee")
        client.post("/api/v1/approvals",
                    json={"request_type": "请假", "title": "第一次", "leave_type": "年假",
                          "start_date": "2026-09-01", "end_date": "2026-09-03"},
                    headers=h)
        r = client.post("/api/v1/approvals",
                        json={"request_type": "请假", "title": "第二次", "leave_type": "年假",
                              "start_date": "2026-09-02", "end_date": "2026-09-04"},
                        headers=h)
        assert r.status_code == 400

    def test_提交报销_金额必须为正(self, client, seeded, login):
        r = client.post("/api/v1/approvals",
                        json={"request_type": "报销", "title": "打车", "amount": 0},
                        headers=login("employee"))
        assert r.status_code == 400

    def test_申请类型不合法被拒(self, client, seeded, login):
        r = client.post("/api/v1/approvals",
                        json={"request_type": "抢银行", "title": "x"},
                        headers=login("employee"))
        assert r.status_code == 400


# ---------- 审批处理 ----------
class Test审批处理:
    def _create_leave(self, client, headers, title, leave_type="年假",
                      start="2026-09-01", end="2026-09-03"):
        r = client.post("/api/v1/approvals",
                        json={"request_type": "请假", "title": title,
                              "leave_type": leave_type,
                              "start_date": start, "end_date": end},
                        headers=headers)
        assert r.status_code == 200
        return r.json()["id"]

    def test_员工不能审批(self, client, seeded, login):
        rid = self._create_leave(client, login("employee"), "普通员工的请假")
        r = client.post(f"/api/v1/approvals/{rid}/approve",
                        json={"action": "通过", "comment": ""}, headers=login("employee"))
        assert r.status_code == 403

    def test_主管审批本部门员工_通过(self, client, seeded, login):
        rid = self._create_leave(client, login("employee"), "技术部员工的请假")
        r = client.post(f"/api/v1/approvals/{rid}/approve",
                        json={"action": "通过", "comment": "同意"}, headers=login("manager"))
        assert r.status_code == 200
        assert r.json()["status"] == "已通过"
        assert r.json()["approve_comment"] == "同意"

    def test_主管不能审批其他部门员工(self, client, seeded, login):
        rid = self._create_leave(client, login("hr"), "人事部员工的请假")  # hr 账号关联赵敏(人事部)
        r = client.post(f"/api/v1/approvals/{rid}/approve",
                        json={"action": "通过", "comment": ""}, headers=login("manager"))
        assert r.status_code == 403

    def test_已审批过的申请不能重复审批(self, client, seeded, login):
        rid = self._create_leave(client, login("employee"), "技术部员工的请假")
        client.post(f"/api/v1/approvals/{rid}/approve",
                    json={"action": "通过", "comment": ""}, headers=login("manager"))
        r = client.post(f"/api/v1/approvals/{rid}/approve",
                        json={"action": "通过", "comment": ""}, headers=login("manager"))
        assert r.status_code == 400

    def test_非法的审批动作被拒(self, client, seeded, login):
        rid = self._create_leave(client, login("employee"), "技术部员工的请假")
        r = client.post(f"/api/v1/approvals/{rid}/approve",
                        json={"action": "通过一下", "comment": ""}, headers=login("manager"))
        assert r.status_code == 400

    def test_待审批列表_主管只看本部门(self, client, seeded, login):
        self._create_leave(client, login("employee"), "技术部李娜的请假")  # 李娜在技术部
        self._create_leave(client, login("hr"), "人事部赵敏的请假")       # 赵敏在人事部
        r = client.get("/api/v1/approvals/pending", headers=login("manager"))
        assert r.status_code == 200
        titles = [item["title"] for item in r.json()]
        assert titles == ["技术部李娜的请假"]  # 只看到自己部门的

    def test_待审批列表_HR看到全部(self, client, seeded, login):
        self._create_leave(client, login("employee"), "技术部李娜的请假")
        self._create_leave(client, login("hr"), "人事部赵敏的请假")
        r = client.get("/api/v1/approvals/pending", headers=login("hr"))
        assert len(r.json()) == 2

    def test_审批后申请人收到结果通知_审批人生成待办通知(self, client, seeded, login):
        # 员工提交请假 -> 主管收到待办
        rid = self._create_leave(client, login("employee"), "通知测试请假")
        notifs = client.get("/api/v1/notifications", headers=login("manager")).json()
        assert any(n["type"] == "todo" and "通知测试请假" in n["content"] for n in notifs)
        # 主管审批通过 -> 员工收到结果
        client.post(f"/api/v1/approvals/{rid}/approve",
                    json={"action": "通过", "comment": "同意"}, headers=login("manager"))
        notifs = client.get("/api/v1/notifications", headers=login("employee")).json()
        assert any(n["type"] == "result" and "已通过" in n["title"] for n in notifs)


# ---------- 绩效 ----------
class Test绩效:
    def test_主管为本部门员工评分_自动定级(self, client, seeded, login):
        r = client.post("/api/v1/performance",
                        json={"employee_id": 3, "year": 2026, "month": 8, "score": 95},
                        headers=login("manager"))
        assert r.status_code == 200
        assert r.json()["level"] == "S"

    def test_员工不能评分(self, client, seeded, login):
        r = client.post("/api/v1/performance",
                        json={"employee_id": 3, "year": 2026, "month": 8, "score": 95},
                        headers=login("employee"))
        assert r.status_code == 403

    def test_主管不能给其他部门员工评分(self, client, seeded, login):
        r = client.post("/api/v1/performance",
                        json={"employee_id": 2, "year": 2026, "month": 8, "score": 95},
                        headers=login("manager"))
        assert r.status_code == 403

    def test_分数超出范围被拒(self, client, seeded, login):
        r = client.post("/api/v1/performance",
                        json={"employee_id": 3, "year": 2026, "month": 8, "score": 101},
                        headers=login("manager"))
        assert r.status_code == 400

    def test_同员工同月份重复评分被拒(self, client, seeded, login):
        h = login("manager")
        data = {"employee_id": 3, "year": 2026, "month": 8, "score": 95}
        assert client.post("/api/v1/performance", json=data, headers=h).status_code == 200
        r = client.post("/api/v1/performance", json=data, headers=h)
        assert r.status_code == 400

    def test_绩效奖金建议_有绩效有薪资时按系数计算(self, client, seeded, login):
        # 李娜(员工3)：薪资 10000 + 绩效 S（系数1.5，奖金率20%）
        client.post("/api/v1/salaries",
                    json={"employee_id": 3, "year": 2026, "month": 8, "base_salary": 10000},
                    headers=login("hr"))
        client.post("/api/v1/performance",
                    json={"employee_id": 3, "year": 2026, "month": 8, "score": 95},
                    headers=login("manager"))
        r = client.get("/api/v1/performance/suggest?employee_id=3&year=2026&month=8",
                       headers=login("hr"))
        assert r.status_code == 200
        body = r.json()
        assert body["level"] == "S"
        assert body["coefficient"] == 1.5
        assert body["suggested_bonus"] == 3000.0  # 10000 * 1.5 * 0.2

    def test_绩效奖金建议_无绩效时返回空建议(self, client, seeded, login):
        r = client.get("/api/v1/performance/suggest?employee_id=3&year=2026&month=8",
                       headers=login("hr"))
        assert r.status_code == 200
        assert r.json()["level"] is None
        assert r.json()["suggested_bonus"] == 0


# ---------- 公告 ----------
class Test公告:
    def test_公告标题不能为空(self, client, seeded, login):
        r = client.post("/api/v1/announcements",
                        json={"title": "   ", "content": ""}, headers=login("hr"))
        assert r.status_code == 400

    def test_发布公告后全员收到通知(self, client, seeded, login):
        r = client.post("/api/v1/announcements",
                        json={"title": "重要公告", "content": "内容"}, headers=login("hr"))
        assert r.status_code == 200
        notifs = client.get("/api/v1/notifications", headers=login("employee")).json()
        assert any(n["type"] == "announcement" and n["title"] == "新公告发布" for n in notifs)


# ---------- 用户管理（admin 专属） ----------
class Test用户管理:
    def test_新增用户_用户名重复被拒(self, client, seeded, login):
        r = client.post("/api/v1/users",
                        json={"username": "hr", "password": "abc123", "role": "hr"},
                        headers=login("admin"))
        assert r.status_code == 400

    def test_新增用户_角色不合法被拒(self, client, seeded, login):
        r = client.post("/api/v1/users",
                        json={"username": "boss", "password": "abc123", "role": "boss"},
                        headers=login("admin"))
        assert r.status_code == 400

    def test_新增用户_成功后可登录(self, client, seeded, login):
        r = client.post("/api/v1/users",
                        json={"username": "newhr", "password": "abc123", "role": "hr"},
                        headers=login("admin"))
        assert r.status_code == 200
        r2 = client.post("/api/v1/auth/login", json={"username": "newhr", "password": "abc123"})
        assert r2.status_code == 200

    def test_不能删除当前登录账号(self, client, seeded, login):
        r = client.delete("/api/v1/users/1", headers=login("admin"))
        assert r.status_code == 400

    def test_删除用户后该账号无法登录(self, client, seeded, login):
        r = client.delete("/api/v1/users/2", headers=login("admin"))
        assert r.status_code == 200
        r2 = client.post("/api/v1/auth/login", json={"username": "hr", "password": "hr123"})
        assert r2.status_code == 400


# ---------- 员工管理 ----------
class Test员工管理:
    def test_新增员工_工号重复被拒(self, client, seeded, login):
        r = client.post("/api/v1/employees",
                        json={"name": "张三", "employee_no": "EMP001", "gender": "男",
                              "department_id": 1, "position_id": 1,
                              "hire_date": "2026-01-01"},
                        headers=login("hr"))
        assert r.status_code == 400

    def test_新增员工_部门不存在被拒(self, client, seeded, login):
        r = client.post("/api/v1/employees",
                        json={"name": "张三", "employee_no": "EMP999", "gender": "男",
                              "department_id": 999, "position_id": 1,
                              "hire_date": "2026-01-01"},
                        headers=login("hr"))
        assert r.status_code == 400

    def test_删除员工_已关联账号的被拒(self, client, seeded, login):
        r = client.delete("/api/v1/employees/3", headers=login("hr"))  # 李娜关联 employee 账号
        assert r.status_code == 400

    def test_删除员工_未关联账号的可以删除(self, client, seeded, login):
        r = client.post("/api/v1/employees",
                        json={"name": "张三", "employee_no": "EMP999", "gender": "男",
                              "department_id": 1, "position_id": 1,
                              "hire_date": "2026-01-01"},
                        headers=login("hr"))
        new_id = r.json()["id"]
        r2 = client.delete(f"/api/v1/employees/{new_id}", headers=login("hr"))
        assert r2.status_code == 200


# ---------- 部门管理 ----------
class Test部门管理:
    def test_新增部门_重名被拒(self, client, seeded, login):
        r = client.post("/api/v1/departments",
                        json={"name": "技术部", "description": ""}, headers=login("hr"))
        assert r.status_code == 400

    def test_删除部门_有员工时被拒(self, client, seeded, login):
        r = client.delete("/api/v1/departments/1", headers=login("hr"))
        assert r.status_code == 400


# ---------- 数据看板 ----------
class Test数据看板:
    def test_汇总看板_返回统计字段(self, client, seeded, login):
        r = client.get("/api/v1/dashboard/summary", headers=login("hr"))
        assert r.status_code == 200
        body = r.json()
        assert body["total_employees"] == 3
        assert sum(d["value"] for d in body["dept_distribution"]) == 3
        assert len(body["salary_trend"]) == 6

    def test_智能提醒_返回列表(self, client, seeded, login):
        r = client.get("/api/v1/alerts", headers=login("hr"))
        assert r.status_code == 200
        assert isinstance(r.json(), list)
