"""
JWT 토큰 검증 테스트
- 서버 없이 실행 가능한 단위 테스트
"""

from datetime import datetime, timedelta, timezone

import jwt
import pytest

# 테스트용 시크릿 키
TEST_SECRET = "test-secret-key-for-ci"


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
        assert len(token.split(".")) == 3  # header.payload.signature

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
        """유효한 토큰이 정상적으로 디코딩되는지 확인"""
        payload = {
            "sub": "user123",
            "exp": datetime.now(timezone.utc) + timedelta(hours=1),
        }
        token = jwt.encode(payload, TEST_SECRET, algorithm="HS256")
        decoded = jwt.decode(token, TEST_SECRET, algorithms=["HS256"])

        assert decoded["sub"] == "user123"

    def test_expired_token_raises_error(self):
        """만료된 토큰이 에러를 발생시키는지 확인"""
        payload = {
            "sub": "user123",
            "exp": datetime.now(timezone.utc) - timedelta(hours=1),  # 과거 시간
        }
        token = jwt.encode(payload, TEST_SECRET, algorithm="HS256")

        with pytest.raises(jwt.ExpiredSignatureError):
            jwt.decode(token, TEST_SECRET, algorithms=["HS256"])

    def test_invalid_signature_raises_error(self):
        """잘못된 서명이 에러를 발생시키는지 확인"""
        payload = {
            "sub": "user123",
            "exp": datetime.now(timezone.utc) + timedelta(hours=1),
        }
        token = jwt.encode(payload, TEST_SECRET, algorithm="HS256")

        with pytest.raises(jwt.InvalidSignatureError):
            jwt.decode(token, "wrong-secret-key", algorithms=["HS256"])

    def test_malformed_token_raises_error(self):
        """잘못된 형식의 토큰이 에러를 발생시키는지 확인"""
        with pytest.raises(jwt.DecodeError):
            jwt.decode("invalid.token.format", TEST_SECRET, algorithms=["HS256"])


class TestJWTAlgorithm:
    """JWT 알고리즘 테스트"""

    def test_hs256_algorithm(self):
        """HS256 알고리즘 테스트"""
        payload = {
            "sub": "user123",
            "exp": datetime.now(timezone.utc) + timedelta(hours=1),
        }
        token = jwt.encode(payload, TEST_SECRET, algorithm="HS256")
        decoded = jwt.decode(token, TEST_SECRET, algorithms=["HS256"])

        assert decoded["sub"] == "user123"

    def test_wrong_algorithm_raises_error(self):
        """잘못된 알고리즘 지정 시 에러 발생"""
        payload = {
            "sub": "user123",
            "exp": datetime.now(timezone.utc) + timedelta(hours=1),
        }
        token = jwt.encode(payload, TEST_SECRET, algorithm="HS256")

        with pytest.raises(jwt.InvalidAlgorithmError):
            jwt.decode(token, TEST_SECRET, algorithms=["HS512"])  # 다른 알고리즘
