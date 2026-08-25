from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..auth import create_token, get_current_user, verify_password, hash_password
from ..database import get_db
from ..models import User
from ..schemas import LoginIn, LoginOut, UserOut

router = APIRouter(prefix="/auth", tags=["认证"])


@router.post("/login", response_model=LoginOut)
def login(body: LoginIn, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == body.username).first()
    if not user or not verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=400, detail="用户名或密码错误")
    token = create_token(user)
    return LoginOut(token=token, user=UserOut.model_validate(user))


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)):
    return UserOut.model_validate(user)


@router.post("/reset-password")
def reset_password(body: dict, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    old_pwd = body.get("old_password", "")
    new_pwd = body.get("new_password", "")
    if not verify_password(old_pwd, user.password_hash):
        raise HTTPException(status_code=400, detail="原密码错误")
    if len(new_pwd) < 6:
        raise HTTPException(status_code=400, detail="新密码至少 6 位")
    user.password_hash = hash_password(new_pwd)
    db.commit()
    return {"message": "密码修改成功"}
