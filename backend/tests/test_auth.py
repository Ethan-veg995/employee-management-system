"""认证模块体检：密码哈希、登录、令牌、改密码"""
import jwt
import pytest

from app.auth import create_token, hash_password, verify_password
from app.config import ALGORITHM, SECRET_KEY
from app.models import User


# ---------- 密码哈希 ----------
class TestPasswordHash:
    def test_密码哈希_校验正确密码返回True(self):
        stored = hash_password("hello123")
        assert verify_password("hello123", stored) is True

    def test_密码哈希_错误密码返回False(self):
        stored = hash_password("hello123")
        assert verify_password("wrong", stored) is False

    def test_密码哈希_相同密码两次哈希结果不同_盐值随机(self):
        assert hash_password("same") != hash_password("same")

    def test_密码哈希_损坏的存储串返回False不抛异常(self):
        assert verify_password("x", "没有盐值分隔符") is False
        assert verify_password("x", "salt$") is False
        assert verify_password("x", "") is False


# ---------- 令牌签发 ----------
class TestToken:
    def test_令牌_包含用户id和角色(self, db_session):
        user = User(id=7, username="alice", role="hr")  # 纯内存对象，不落库
        token = create_token(user)
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        assert payload["sub"] == "7"
        assert payload["role"] == "hr"
        assert payload["username"] == "alice"
        assert payload["exp"] > payload.get("iat", 0)


# ---------- 登录接口 ----------
class TestLogin:
    def test_登录_正确账号返回令牌和用户信息(self, client, seeded):
        r = client.post("/api/v1/auth/login", json={"username": "hr", "password": "hr123"})
        assert r.status_code == 200
        body = r.json()
        assert body["token"]
        assert body["user"]["username"] == "hr"
        assert body["user"]["role"] == "hr"

    def test_登录_密码错误返回400(self, client, seeded):
        r = client.post("/api/v1/auth/login", json={"username": "hr", "password": "bad"})
        assert r.status_code == 400
        assert "用户名或密码错误" in r.text

    def test_登录_用户不存在返回400(self, client, seeded):
        r = client.post("/api/v1/auth/login", json={"username": "nobody", "password": "x"})
        assert r.status_code == 400


# ---------- 当前用户接口 ----------
class TestMe:
    def test_me_带令牌返回当前用户(self, client, seeded, login):
        r = client.get("/api/v1/auth/me", headers=login("manager"))
        assert r.status_code == 200
        assert r.json()["username"] == "manager"
        assert r.json()["role"] == "manager"

    def test_me_无令牌返回401(self, client, seeded):
        r = client.get("/api/v1/auth/me")
        assert r.status_code == 401

    def test_me_伪造令牌返回401(self, client, seeded):
        r = client.get("/api/v1/auth/me", headers={"Authorization": "Bearer fake-token-123"})
        assert r.status_code == 401


# ---------- 修改密码 ----------
class TestResetPassword:
    def test_改密码_原密码错误返回400(self, client, seeded, login):
        r = client.post("/api/v1/auth/reset-password",
                        json={"old_password": "wrong", "new_password": "newpass123"},
                        headers=login("hr"))
        assert r.status_code == 400
        assert "原密码错误" in r.text

    def test_改密码_新密码太短返回400(self, client, seeded, login):
        r = client.post("/api/v1/auth/reset-password",
                        json={"old_password": "hr123", "new_password": "123"},
                        headers=login("hr"))
        assert r.status_code == 400
        assert "至少 6 位" in r.text

    def test_改密码_成功后旧密码失效新密码生效(self, client, seeded, login):
        r = client.post("/api/v1/auth/reset-password",
                        json={"old_password": "hr123", "new_password": "newpass123"},
                        headers=login("hr"))
        assert r.status_code == 200
        # 旧密码登录失败
        r1 = client.post("/api/v1/auth/login", json={"username": "hr", "password": "hr123"})
        assert r1.status_code == 400
        # 新密码登录成功
        r2 = client.post("/api/v1/auth/login", json={"username": "hr", "password": "newpass123"})
        assert r2.status_code == 200
