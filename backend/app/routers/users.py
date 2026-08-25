from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..auth import hash_password, require_admin
from ..config import ROLES
from ..database import get_db
from ..models import Employee, User
from ..schemas import UserDetailOut, UserIn, UserUpdate

router = APIRouter(prefix="/users", tags=["用户管理"], dependencies=[Depends(require_admin)])


def user_out(u: User) -> UserDetailOut:
    return UserDetailOut(
        id=u.id, username=u.username, role=u.role,
        role_name={"admin": "系统管理员", "hr": "HR", "manager": "部门主管",
                   "employee": "普通员工"}.get(u.role, u.role),
        employee_id=u.employee_id,
        employee_name=u.employee.name if u.employee else "",
        created_at=u.created_at,
    )


def check_employee_link(db: Session, employee_id: int | None, exclude_user_id: int | None = None):
    if not employee_id:
        return
    emp = db.get(Employee, employee_id)
    if not emp:
        raise HTTPException(status_code=400, detail="关联员工不存在")
    q = db.query(User).filter(User.employee_id == employee_id)
    if exclude_user_id:
        q = q.filter(User.id != exclude_user_id)
    if q.first():
        raise HTTPException(status_code=400, detail="该员工已关联其他账号")


@router.get("", response_model=list[UserDetailOut])
def list_users(db: Session = Depends(get_db)):
    return [user_out(u) for u in db.query(User).order_by(User.id).all()]


@router.post("", response_model=UserDetailOut)
def create_user(body: UserIn, db: Session = Depends(get_db)):
    if db.query(User).filter(User.username == body.username).first():
        raise HTTPException(status_code=400, detail="用户名已存在")
    if body.role not in ROLES:
        raise HTTPException(status_code=400, detail="角色不合法")
    check_employee_link(db, body.employee_id)
    user = User(username=body.username, password_hash=hash_password(body.password),
                role=body.role, employee_id=body.employee_id)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user_out(user)


@router.put("/{user_id}", response_model=UserDetailOut)
def update_user(user_id: int, body: UserUpdate, db: Session = Depends(get_db)):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    data = body.model_dump(exclude_unset=True)
    if "password" in data and data["password"]:
        user.password_hash = hash_password(data["password"])
    if "role" in data and data["role"]:
        if data["role"] not in ROLES:
            raise HTTPException(status_code=400, detail="角色不合法")
        user.role = data["role"]
    if "employee_id" in data:
        check_employee_link(db, data["employee_id"], exclude_user_id=user_id)
        user.employee_id = data["employee_id"]
    db.commit()
    db.refresh(user)
    return user_out(user)


@router.delete("/{user_id}")
def delete_user(user_id: int, current: User = Depends(require_admin), db: Session = Depends(get_db)):
    if user_id == current.id:
        raise HTTPException(status_code=400, detail="不能删除当前登录账号")
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    db.delete(user)
    db.commit()
    return {"message": "删除成功"}
