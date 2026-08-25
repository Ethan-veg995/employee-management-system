# 企业员工管理系统（Employee Management System）

面向中小企业的全栈人事管理系统：员工档案、部门职位、考勤打卡、多类型审批工作流（请假/加班/报销/出差）、消息通知、绩效管理、薪资核算（绩效联动）、公告中心、数据看板与智能考勤异常提醒。

- 前端：Vue 3 + Vite + Element Plus + ECharts + Pinia（多页签、面包屑、消息铃铛）
- 后端：FastAPI + SQLAlchemy + SQLite（JWT 认证，4 角色权限，13 张表）
- 支持本地运行与 CloudStudio 云端一键部署

## 快速开始

### 后端（端口 8000）

```bash
cd backend
pip install -r requirements.txt
python -m app.seed          # 初始化演示数据
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

### 前端（端口 3000）

```bash
cd frontend
npm install
npm run dev
```

浏览器访问 http://localhost:3000

## 演示账号

| 账号 | 密码 | 角色 |
| --- | --- | --- |
| admin | admin123 | 系统管理员 |
| hr | hr123 | HR |
| manager | manager123 | 部门主管 |
| employee | employee123 | 普通员工 |

## 功能清单

- 部门 / 职位 / 员工管理（含 Excel 导入导出）
- 考勤打卡 + 考勤规则配置 + 月度考勤统计
- 多类型审批工作流：请假 / 加班 / 报销 / 出差（提交 → 审批 → 通知闭环）
- 消息通知中心：待办 / 审批结果 / 公告（未读红点 + 30 秒轮询）
- 绩效管理：月度评分 → 等级（S/A/B/C）→ 薪资联动自动计算建议奖金
- 公告中心：发布 / 编辑 / 删除 + 全员通知
- 薪资录入与查询（HR）/ 员工查看本人薪资
- 数据可视化看板（6 类图表 + 渐变统计卡片）
- 智能考勤异常提醒（连续迟到、缺卡、请假超额度、部门出勤率预警）

## 文档

详见 `docs/` 目录：需求规格说明书、架构设计、数据库设计、API 接口设计、设计审查报告、测试文档、操作手册、答辩提纲。界面截图见 `docs/screenshots/`。

## 云端部署（可选）

项目已内置 CloudStudio 适配（`start.sh` 一键启动、Vite 代理配置、相对路径请求基址）。推送 GitHub 后在 cloudstudio.net 导入仓库，执行 `sh start.sh` 即可获得公网访问链接。
