"""
JWT 토큰 검증 테스트 - CI 파이프라인용
"""

import os
from datetime import datetime, timedelta, timezone

import jwt
import pytest

# 테스트용 시크릿 (환경변수에서 가져오거나 기본값 사용)
TEST_SECRET = os.environ.get("TEST_JWT_SECRET", "test-secret-key-for-ci-pipeline")


class TestJWTCreation:
    """JWT 토큰 생성 테스트"""

    def test_create_valid_token(self):
        """유효한 JWT 토큰 생성"""
        payload = {
            "sub": "user123",
            "exp": datetime.now(timezone.utc) + timedelta(hours=1),
        }
        token = jwt.encode(payload, TEST_SECRET, algorithm="HS256")

        assert token is not None
        assert isinstance(token, str)
        assert len(token.split(".")) == 3

    def test_token_contains_claims(self):
        """토큰에 클레임이 포함되어 있는지 확인"""
        payload = {
            "sub": "user123",
            "role": "admin",
            "exp": datetime.now(timezone.utc) + timedelta(hours=1),
        }
        token = jwt.encode(payload, TEST_SECRET, algorithm="HS256")
        decoded = jwt.decode(token, TEST_SECRET, algorithms=["HS256"])

        assert decoded["sub"] == "user123"
        assert decoded["role"] == "admin"


class TestJWTValidation:
    """JWT 토큰 검증 테스트"""

    def test_valid_token_decodes(self):
        """유효한 토큰 디코딩"""
        payload = {
            "sub": "user123",
            "exp": datetime.now(timezone.utc) + timedelta(hours=1),
        }
        token = jwt.encode(payload, TEST_SECRET, algorithm="HS256")
        decoded = jwt.decode(token, TEST_SECRET, algorithms=["HS256"])

        assert decoded["sub"] == "user123"

    def test_expired_token_raises_error(self):
        """만료된 토큰은 에러 발생"""
        payload = {
            "sub": "user123",
            "exp": datetime.now(timezone.utc) - timedelta(hours=1),
        }
        token = jwt.encode(payload, TEST_SECRET, algorithm="HS256")

        with pytest.raises(jwt.ExpiredSignatureError):
            jwt.decode(token, TEST_SECRET, algorithms=["HS256"])

    def test_invalid_signature_raises_error(self):
        """잘못된 서명은 에러 발생"""
        payload = {
            "sub": "user123",
            "exp": datetime.now(timezone.utc) + timedelta(hours=1),
        }
        token = jwt.encode(payload, TEST_SECRET, algorithm="HS256")

        with pytest.raises(jwt.InvalidSignatureError):
            jwt.decode(token, "wrong-secret", algorithms=["HS256"])
