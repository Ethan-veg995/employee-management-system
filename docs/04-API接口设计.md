# 企业员工管理系统 — API 接口设计

| 文档版本 | V2.0（新增审批/通知/绩效/公告接口） |
| 基础路径 | `/api/v1` |
| 鉴权 | 请求头 `Authorization: Bearer <JWT>` |
| 交互文档 | 后端启动后访问 `http://localhost:8000/docs`（Swagger UI） |

## 1. 通用约定

- 统一 JSON 响应；错误返回 `{"detail": "错误信息"}`，HTTP 状态码 400（参数/业务错误）、401（未登录/过期）、403（无权限）、404（不存在）
- 角色标记：✅ 全部角色 / 👤 员工 / 👔 主管 / 👩💼 HR

## 2. 认证模块 `/auth`

| 方法 | 路径 | 权限 | 说明 |
| --- | --- | --- | --- |
| POST | /auth/login | ✅ | 登录，入参 `{username, password}`，返回 `{token, user}` |
| GET | /auth/me | ✅ | 获取当前登录用户信息 |
| POST | /auth/reset-password | ✅ | 修改密码 `{old_password, new_password}` |

## 3. 部门 `/departments`（👩💼 HR）

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | /departments | 部门列表（含 employee_count 人员统计） |
| POST | /departments | 新增 `{name, description}` |
| PUT | /departments/{id} | 修改 |
| DELETE | /departments/{id} | 删除（有员工/职位时拒绝） |

## 4. 职位 `/positions`（👩💼 HR）

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | /positions | 职位列表（含部门名、职级） |
| POST | /positions | 新增 `{name, department_id, level}` |
| PUT | /positions/{id} | 修改 |
| DELETE | /positions/{id} | 删除（有员工时拒绝） |

## 5. 员工 `/employees`（👩💼 HR）

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | /employees | 分页列表，参数 `keyword, department_id, status, page, size`，返回 `{total, items}` |
| GET | /employees/all | 全部员工（下拉用） |
| GET | /employees/{id} | 详情 |
| POST | /employees | 新增 `{name, employee_no, gender, phone, email, department_id, position_id, hire_date, status}` |
| PUT | /employees/{id} | 修改 |
| DELETE | /employees/{id} | 删除（已关联账号时拒绝） |
| GET | /employees/export/excel | 按筛选条件导出 .xlsx |
| POST | /employees/import/excel | 上传 .xlsx 批量导入（multipart，字段名 file） |

## 6. 考勤 `/attendance`

| 方法 | 路径 | 权限 | 说明 |
| --- | --- | --- | --- |
| GET | /attendance/rules | 👩💼/🛡 | 获取考勤规则 |
| PUT | /attendance/rules | 👩💼/🛡 | 更新 `{work_start, work_end, late_tolerance_minutes}` |
| POST | /attendance/punch | 👤/👔 | 打卡 `{type: check_in/check_out}`，返回 `{message, record}` |
| GET | /attendance/my | 👤/👔 | 本人某月考勤 `{month: YYYY-MM}`，返回 `{stats, records}` |
| GET | /attendance/records | 👩💼/🛡 | 明细查询 `month, department_id, employee_id` |
| GET | /attendance/monthly | 👩💼/🛡 | 月度统计 `month, department_id`，返回每人 `{workdays, attended, late, early, missing_punch, leave_days, absent, rate}` |

## 7. 审批工作流 `/approvals`（通用：请假/加班/报销/出差）

| 方法 | 路径 | 权限 | 说明 |
| --- | --- | --- | --- |
| POST | /approvals | 👤/👔 | 发起申请 `{request_type, title, leave_type?, amount?, start_date?, end_date?, reason}`；请假校验同时间段待审批冲突，报销必填金额 |
| GET | /approvals/my | 👤/👔 | 本人申请 `status, request_type` 筛选 |
| GET | /approvals/pending | 👔(本部门)/👩💼/🛡 | 待审批列表 |
| GET | /approvals | 👩💼/🛡 | 全部记录 `status, request_type, department_id` 筛选 |
| GET | /approvals/{id} | ✅ | 详情 |
| POST | /approvals/{id}/approve | 👔(本部门)/👩💼/🛡 | 审批 `{action: 通过/驳回, comment}`；通过/驳回自动通知申请人 |

## 8. 消息通知 `/notifications`

| 方法 | 路径 | 权限 | 说明 |
| --- | --- | --- | --- |
| GET | /notifications | ✅ | 消息列表 `unread_only, limit` |
| GET | /notifications/unread-count | ✅ | 未读数（前端 30 秒轮询） |
| POST | /notifications/{id}/read | ✅ | 标记单条已读 |
| POST | /notifications/read-all | ✅ | 全部已读 |

触发点：提交申请→通知审批人（todo）；审批完成→通知申请人（result）；发布公告→通知全员（announcement）

## 9. 绩效管理 `/performance`

| 方法 | 路径 | 权限 | 说明 |
| --- | --- | --- | --- |
| GET | /performance | 👔/👩💼/🛡（👤仅本人） | 查询 `year, month, department_id, employee_id` |
| GET | /performance/my | 👤/👔 | 本人绩效 |
| GET | /performance/suggest | 👩💼/🛡 | 薪资联动建议 `employee_id, year, month` → `{level, coefficient, suggested_bonus, base_salary}` |
| POST | /performance | 👔(本部门)/👩💼/🛡 | 评分 `{employee_id, year, month, score, comment}`，等级自动映射 |
| PUT | /performance/{id} | 👩💼/🛡 | 修改 |
| DELETE | /performance/{id} | 👩💼/🛡 | 删除 |

等级映射：S≥90 / A≥80 / B≥70 / C<70；建议绩效奖金 = 系数 × 基本工资 × 20%

## 10. 公告中心 `/announcements`

| 方法 | 路径 | 权限 | 说明 |
| --- | --- | --- | --- |
| GET | /announcements | ✅ | 公告列表（全员） |
| POST | /announcements | 👩💼/🛡 | 发布 `{title, content}`，自动通知全员 |
| PUT | /announcements/{id} | 👩💼/🛡 | 编辑 |
| DELETE | /announcements/{id} | 👩💼/🛡 | 删除 |

## 11. 薪资管理 `/salaries`

| 方法 | 路径 | 权限 | 说明 |
| --- | --- | --- | --- |
| GET | /salaries | 👩💼/🛡 | 查询 `year, month, employee_id, department_id` |
| GET | /salaries/years | 👩💼/🛡 | 年份列表（筛选用） |
| GET | /salaries/my | 👤/👔 | 本人薪资 |
| POST | /salaries | 👩💼/🛡 | 录入 `{employee_id, year, month, base_salary, bonus, deduction}`，实发自动计算；当月有绩效时前端自动带出建议绩效奖金 |
| PUT | /salaries/{id} | 👩💼/🛡 | 修改 |
| DELETE | /salaries/{id} | 👩💼/🛡 | 删除 |

## 12. 数据看板 `/dashboard`

| 方法 | 路径 | 权限 | 说明 |
| --- | --- | --- | --- |
| GET | /dashboard/summary | 👩💼/🛡 | 汇总：员工总数、本月入职/累计离职、部门分布、职级分布、本月出勤率（含上月对比）、请假统计、近 6 月薪资趋势 |
| GET | /dashboard/my | 👤/👔 | 个人工作台：档案、今日状态、本月考勤、请假天数、最近薪资 |

## 13. 智能提醒 `/alerts`（👩💼 HR）

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | /alerts | 返回异常列表 `[{level: warning/danger, title, detail, employee_id, employee_name}]` |

规则：①连续 3 天及以上迟到（danger）②本月缺卡 ≥3 次 ③年度请假超额度（年假 5 天/事假 10 天）④部门出勤率 < 90%

## 14. 用户管理 `/users`（🛡 管理员）

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | /users | 用户列表（含角色名、关联员工名） |
| POST | /users | 新增 `{username, password, role, employee_id}` |
| PUT | /users/{id} | 修改 `{password?, role?, employee_id?}` |
| DELETE | /users/{id} | 删除（不能删除自己） |

## 15. 接口示例（员工发起请假 → 主管审批 → 申请人收到通知）

```
① 员工发起申请
POST /api/v1/approvals
Authorization: Bearer eyJhbGciOi...
{"request_type": "请假", "title": "感冒请假", "leave_type": "病假",
 "start_date": "2026-08-25", "end_date": "2026-08-26", "reason": "感冒发烧"}

200 OK → {"id": 14, "request_type": "请假", "title": "感冒请假",
          "status": "待审批", "days": 2, ...}

② 主管审批通过（提交时生成"待办"通知给主管；审批后生成"结果"通知给申请人）
POST /api/v1/approvals/14/approve
{"action": "通过", "comment": "同意"}

200 OK → {"id": 14, "status": "已通过", "approve_comment": "同意", ...}

③ 申请人查看未读通知
GET /api/v1/notifications/unread-count → {"count": 2}
```
