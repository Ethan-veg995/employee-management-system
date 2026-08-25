from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..auth import require_hr, require_login
from ..config import LEAVE_TYPES, REQUEST_TYPES
from ..database import get_db
from ..models import ApprovalRequest, Employee, User
from ..routers.notifications import create_notification
from ..schemas import ApprovalIn, ApprovalOut, ApproveIn

router = APIRouter(prefix="/approvals", tags=["审批管理"])


def approval_out(r: ApprovalRequest) -> ApprovalOut:
    return ApprovalOut(
        id=r.id,
        employee_id=r.employee_id,
        employee_name=r.employee.name if r.employee else "",
        department_name=r.employee.department.name if r.employee and r.employee.department else "",
        request_type=r.request_type,
        title=r.title,
        leave_type=r.leave_type,
        amount=r.amount,
        start_date=r.start_date,
        end_date=r.end_date,
        days=r.days,
        reason=r.reason,
        status=r.status,
        approve_comment=r.approve_comment,
        approver_name=r.approver.username if r.approver else "",
        created_at=r.created_at,
    )


def require_employee_link(user: User) -> Employee:
    if not user.employee_id:
        raise HTTPException(status_code=400, detail="当前账号未关联员工档案")
    return user.employee


def find_approver(db: Session, emp: Employee) -> User | None:
    """审批人：本部门 manager 角色的用户；无则取第一个 hr"""
    manager = (db.query(User)
               .filter(User.role == "manager", User.employee_id.isnot(None))
               .join(Employee)
               .filter(Employee.department_id == emp.department_id)
               .first())
    if manager:
        return manager
    return db.query(User).filter(User.role == "hr").first()


@router.post("", response_model=ApprovalOut)
def create_approval(body: ApprovalIn, user=Depends(require_login), db: Session = Depends(get_db)):
    emp = require_employee_link(user)
    if body.request_type not in REQUEST_TYPES:
        raise HTTPException(status_code=400, detail="申请类型不合法")
    if not body.title:
        raise HTTPException(status_code=400, detail="请填写申请标题")
    if body.request_type == "请假":
        if body.leave_type not in LEAVE_TYPES:
            raise HTTPException(status_code=400, detail="请选择请假类型")
        if not body.start_date or not body.end_date:
            raise HTTPException(status_code=400, detail="请选择起止日期")
        if body.end_date < body.start_date:
            raise HTTPException(status_code=400, detail="结束日期不能早于开始日期")
        overlap = (db.query(ApprovalRequest)
                   .filter(ApprovalRequest.employee_id == emp.id,
                           ApprovalRequest.request_type == "请假",
                           ApprovalRequest.status == "待审批",
                           ApprovalRequest.start_date <= body.end_date,
                           ApprovalRequest.end_date >= body.start_date)
                   .first())
        if overlap:
            raise HTTPException(status_code=400, detail="该时间段已有待审批的请假申请")
    if body.request_type == "报销" and (body.amount is None or body.amount <= 0):
        raise HTTPException(status_code=400, detail="请填写正确的报销金额")
    if body.request_type in ("出差", "加班") and (not body.start_date or not body.end_date):
        raise HTTPException(status_code=400, detail="请选择起止日期")

    days = None
    if body.start_date and body.end_date:
        days = (body.end_date - body.start_date).days + 1
    req = ApprovalRequest(
        employee_id=emp.id,
        request_type=body.request_type,
        title=body.title,
        leave_type=body.leave_type if body.request_type == "请假" else None,
        amount=body.amount if body.request_type == "报销" else None,
        start_date=body.start_date,
        end_date=body.end_date,
        days=days,
        reason=body.reason,
    )
    db.add(req)
    db.commit()
    db.refresh(req)

    approver = find_approver(db, emp)
    if approver:
        create_notification(db, approver.id, "todo",
                            f"新的{body.request_type}申请待审批",
                            f"{emp.name} 提交了「{body.title}」，请及时处理", req.id)
    return approval_out(req)


@router.get("/my")
def my_approvals(status: str = "", request_type: str = "",
                 user=Depends(require_login), db: Session = Depends(get_db)):
    emp = require_employee_link(user)
    q = db.query(ApprovalRequest).filter(ApprovalRequest.employee_id == emp.id)
    if status:
        q = q.filter(ApprovalRequest.status == status)
    if request_type:
        q = q.filter(ApprovalRequest.request_type == request_type)
    rows = q.order_by(ApprovalRequest.created_at.desc()).all()
    return [approval_out(r) for r in rows]


@router.get("/pending")
def pending_approvals(user=Depends(require_login), db: Session = Depends(get_db)):
    if user.role not in ("manager", "hr"):
        raise HTTPException(status_code=403, detail="没有权限查看待审批列表")
    q = db.query(ApprovalRequest).filter(ApprovalRequest.status == "待审批")
    if user.role == "manager":
        emp = require_employee_link(user)
        q = q.join(Employee).filter(Employee.department_id == emp.department_id)
    rows = q.order_by(ApprovalRequest.created_at.desc()).all()
    return [approval_out(r) for r in rows]


@router.get("")
def all_approvals(status: str = "", request_type: str = "", department_id: int | None = None,
                  user=Depends(require_hr), db: Session = Depends(get_db)):
    q = db.query(ApprovalRequest)
    if status:
        q = q.filter(ApprovalRequest.status == status)
    if request_type:
        q = q.filter(ApprovalRequest.request_type == request_type)
    if department_id:
        q = q.join(Employee).filter(Employee.department_id == department_id)
    rows = q.order_by(ApprovalRequest.created_at.desc()).all()
    return [approval_out(r) for r in rows]


@router.get("/{req_id}", response_model=ApprovalOut)
def get_approval(req_id: int, user=Depends(require_login), db: Session = Depends(get_db)):
    req = db.get(ApprovalRequest, req_id)
    if not req:
        raise HTTPException(status_code=404, detail="申请不存在")
    if user.role == "employee":
        if not user.employee_id or req.employee_id != user.employee_id:
            raise HTTPException(status_code=403, detail="没有权限查看该申请")
    elif user.role == "manager":
        if not user.employee_id or req.employee.department_id != user.employee.department_id:
            raise HTTPException(status_code=403, detail="只能查看本部门员工的申请")
    elif user.role == "admin":
        raise HTTPException(status_code=403, detail="没有权限查看该申请")
    return approval_out(req)


@router.post("/{req_id}/approve", response_model=ApprovalOut)
def approve_request(req_id: int, body: ApproveIn,
                    user=Depends(require_login), db: Session = Depends(get_db)):
    if user.role not in ("manager", "hr"):
        raise HTTPException(status_code=403, detail="没有权限审批")
    if body.action not in ("通过", "驳回"):
        raise HTTPException(status_code=400, detail="action 仅支持 通过/驳回")
    req = db.get(ApprovalRequest, req_id)
    if not req:
        raise HTTPException(status_code=404, detail="申请不存在")
    if req.status != "待审批":
        raise HTTPException(status_code=400, detail="该申请已审批过")
    if user.role == "manager":
        emp = require_employee_link(user)
        if req.employee.department_id != emp.department_id:
            raise HTTPException(status_code=403, detail="只能审批本部门员工的申请")
    req.status = "已通过" if body.action == "通过" else "已驳回"
    req.approver_id = user.id
    req.approve_comment = body.comment
    req.approved_at = datetime.now()
    db.commit()
    db.refresh(req)

    if req.employee.user:
        create_notification(db, req.employee.user.id, "result",
                            f"{req.request_type}申请{req.status}",
                            f"「{req.title}」审批结果：{req.status}"
                            + (f"，意见：{body.comment}" if body.comment else ""), req.id)
    return approval_out(req)
