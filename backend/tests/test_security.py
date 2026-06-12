"""
单元测试: 安全模块 (Security)
测试 JWT Token 创建/解码/类型校验、密码哈希/验证
纯单元测试，不依赖数据库
"""
import pytest
from datetime import timedelta

from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)


class TestPasswordHashing:
    """密码哈希与验证"""

    def test_hash_and_verify(self):
        plain = "mySecretPassword123"
        hashed = hash_password(plain)
        assert hashed != plain
        assert verify_password(plain, hashed)

    def test_verify_wrong_password(self):
        hashed = hash_password("correct_password")
        assert not verify_password("wrong_password", hashed)

    def test_hash_is_stable(self):
        """Same password should produce different hashes (salt)"""
        pwd = "same_password"
        assert hash_password(pwd) != hash_password(pwd)


class TestAccessToken:
    """Access Token 生成与解码"""

    def test_create_and_decode(self):
        token = create_access_token({"sub": "user-123", "role": "admin"})
        payload = decode_token(token)
        assert payload is not None
        assert payload["sub"] == "user-123"
        assert payload["role"] == "admin"
        assert payload["type"] == "access"
        assert "exp" in payload

    def test_custom_expiry(self):
        token = create_access_token({"sub": "user-456"}, expires_delta=timedelta(seconds=1))
        payload = decode_token(token)
        assert payload is not None
        assert payload["sub"] == "user-456"

    def test_invalid_token(self):
        payload = decode_token("this.is.not.a.valid.jwt.token")
        assert payload is None

    def test_empty_token(self):
        payload = decode_token("")
        assert payload is None

    def test_token_with_extra_data(self):
        token = create_access_token({
            "sub": "user-789",
            "role": "staff",
            "company_id": "comp-001",
        })
        payload = decode_token(token)
        assert payload is not None
        assert payload["sub"] == "user-789"
        assert payload["company_id"] == "comp-001"


class TestRefreshToken:
    """Refresh Token 生成与解码"""

    def test_create_and_decode(self):
        token = create_refresh_token({"sub": "user-abc"})
        payload = decode_token(token)
        assert payload is not None
        assert payload["sub"] == "user-abc"
        assert payload["type"] == "refresh"
        assert "exp" in payload

    def test_type_is_refresh_not_access(self):
        """Refresh token 的 type 应为 'refresh'"""
        token = create_refresh_token({"sub": "user-xyz"})
        payload = decode_token(token)
        assert payload is not None
        assert payload["type"] == "refresh"
        assert payload["type"] != "access"
