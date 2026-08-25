from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .database import Base, engine
from .routers import (alerts, announcements, approvals, attendance, auth,
                      dashboard, departments, employees, notifications,
                      performance, positions, salaries, users)

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="企业员工管理系统 API",
    version="2.0.0",
    description="面向中小企业的员工信息管理系统后端接口（含审批工作流/消息通知/绩效/公告）",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

API_PREFIX = "/api/v1"
for r in (auth, departments, positions, employees, attendance,
          approvals, salaries, dashboard, users, alerts,
          notifications, performance, announcements):
    app.include_router(r.router, prefix=API_PREFIX)


@app.get("/")
def root():
    return {"app": "企业员工管理系统", "docs": "/docs"}
