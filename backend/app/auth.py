import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Optional

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from .config import SECRET_KEY, ALGORITHM, TOKEN_EXPIRE_HOURS, ROLES
from .database import get_db
from .models import User

bearer_scheme = HTTPBearer(auto_error=False)


def hash_password(password: str) -> str:
    salt = secrets.token_hex(8)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 100_000).hex()
    return f"{salt}${digest}"


def verify_password(password: str, stored: str) -> bool:
    try:
        salt, digest = stored.split("$")
        check = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 100_000).hex()
        return secrets.compare_digest(check, digest)
    except Exception:
        return False


def create_token(user: User) -> str:
    payload = {
        "sub": str(user.id),
        "username": user.username,
        "role": user.role,
        "exp": datetime.utcnow() + timedelta(hours=TOKEN_EXPIRE_HOURS),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    if credentials is None:
        raise HTTPException(status_code=401, detail="未登录")
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="登录已过期，请重新登录")
    user = db.get(User, int(payload["sub"]))
    if not user:
        raise HTTPException(status_code=401, detail="用户不存在")
    return user


def require_roles(*allowed: str):
    def checker(user: User = Depends(get_current_user)) -> User:
        if user.role not in allowed:
            raise HTTPException(status_code=403, detail="没有权限执行该操作")
        return user
    return checker


def require_hr(user: User = Depends(require_roles("hr"))) -> User:
    return user


def require_admin(user: User = Depends(require_roles("admin"))) -> User:
    return user


def require_login(user: User = Depends(get_current_user)) -> User:
    return user
