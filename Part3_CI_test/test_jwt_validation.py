"""
JWT 토큰 검증 테스트
- 서버 없이 실행 가능한 단위 테스트
"""

# =============================================================================
# JWT 토큰 검증 단위 테스트 - CI 파이프라인용
# =============================================================================
# 목적: JWT 토큰의 생성, 검증, 알고리즘 테스트
# 특징: 외부 서버 의존성 없이 실행 가능 (순수 단위 테스트)
# 실행: pytest Part3_CI_test/test_jwt_validation.py
# =============================================================================

from datetime import datetime, timedelta, timezone  # 시간 처리

import jwt  # PyJWT 라이브러리 (JWT 인코딩/디코딩)
import pytest  # 테스트 프레임워크

# -----------------------------------------------------------------------------
# 테스트 설정
# -----------------------------------------------------------------------------
TEST_SECRET = "test-secret-key-for-ci"  # 테스트용 시크릿 (프로덕션에서는 환경변수 사용)


# =============================================================================
# 테스트 클래스 1: JWT 토큰 생성 테스트
# =============================================================================
class TestJWTCreation:
    """JWT 토큰 생성 테스트 - 토큰이 올바르게 생성되는지 검증"""

    def test_create_valid_token(self):
        """유효한 JWT 토큰 생성 테스트"""
        payload = {
            "sub": "user123",  # subject: 토큰 주체 (사용자 ID)
            "exp": datetime.now(timezone.utc)
            + timedelta(hours=1),  # expiration: 1시간 후 만료
        }
        token = jwt.encode(
            payload, TEST_SECRET, algorithm="HS256"
        )  # HS256 알고리즘으로 서명

        assert token is not None  # 토큰이 생성되었는지 확인
        assert isinstance(token, str)  # 문자열 타입인지 확인
        assert len(token.split(".")) == 3  # JWT 형식 확인: header.payload.signature

    def test_token_contains_claims(self):
        """토큰에 클레임(claim)이 포함되어 있는지 확인"""
        payload = {
            "sub": "user123",  # subject 클레임
            "role": "admin",  # 커스텀 클레임: 역할
            "exp": datetime.now(timezone.utc) + timedelta(hours=1),  # 만료 시간
        }
        token = jwt.encode(payload, TEST_SECRET, algorithm="HS256")  # 토큰 생성
        decoded = jwt.decode(token, TEST_SECRET, algorithms=["HS256"])  # 토큰 디코딩

        assert decoded["sub"] == "user123"  # subject 클레임 확인
        assert decoded["role"] == "admin"  # role 클레임 확인


# =============================================================================
# 테스트 클래스 2: JWT 토큰 검증 테스트
# =============================================================================
class TestJWTValidation:
    """JWT 토큰 검증 테스트 - 다양한 검증 시나리오"""

    def test_valid_token_decodes(self):
        """유효한 토큰이 정상적으로 디코딩되는지 확인"""
        payload = {
            "sub": "user123",
            "exp": datetime.now(timezone.utc) + timedelta(hours=1),  # 유효한 만료 시간
        }
        token = jwt.encode(payload, TEST_SECRET, algorithm="HS256")
        decoded = jwt.decode(token, TEST_SECRET, algorithms=["HS256"])  # 정상 디코딩

        assert decoded["sub"] == "user123"  # 클레임 검증

    def test_expired_token_raises_error(self):
        """만료된 토큰이 ExpiredSignatureError를 발생시키는지 확인"""
        payload = {
            "sub": "user123",
            "exp": datetime.now(timezone.utc)
            - timedelta(hours=1),  # 과거 시간 = 만료됨
        }
        token = jwt.encode(payload, TEST_SECRET, algorithm="HS256")

        with pytest.raises(jwt.ExpiredSignatureError):  # 만료 에러 예상
            jwt.decode(token, TEST_SECRET, algorithms=["HS256"])

    def test_invalid_signature_raises_error(self):
        """잘못된 서명(시크릿)이 InvalidSignatureError를 발생시키는지 확인"""
        payload = {
            "sub": "user123",
            "exp": datetime.now(timezone.utc) + timedelta(hours=1),
        }
        token = jwt.encode(
            payload, TEST_SECRET, algorithm="HS256"
        )  # 올바른 시크릿으로 서명

        with pytest.raises(jwt.InvalidSignatureError):  # 서명 불일치 에러 예상
            jwt.decode(
                token, "wrong-secret-key", algorithms=["HS256"]
            )  # 잘못된 시크릿으로 검증

    def test_malformed_token_raises_error(self):
        """잘못된 형식의 토큰이 DecodeError를 발생시키는지 확인"""
        with pytest.raises(jwt.DecodeError):  # 디코딩 에러 예상
            jwt.decode(
                "invalid.token.format", TEST_SECRET, algorithms=["HS256"]
            )  # 유효하지 않은 토큰


# =============================================================================
# 테스트 클래스 3: JWT 알고리즘 테스트
# =============================================================================
class TestJWTAlgorithm:
    """JWT 알고리즘 테스트 - 알고리즘 검증 및 보안"""

    def test_hs256_algorithm(self):
        """HS256 알고리즘 정상 동작 테스트"""
        payload = {
            "sub": "user123",
            "exp": datetime.now(timezone.utc) + timedelta(hours=1),
        }
        token = jwt.encode(payload, TEST_SECRET, algorithm="HS256")  # HMAC-SHA256
        decoded = jwt.decode(
            token, TEST_SECRET, algorithms=["HS256"]
        )  # 같은 알고리즘으로 검증

        assert decoded["sub"] == "user123"  # 정상 디코딩 확인

    def test_wrong_algorithm_raises_error(self):
        """잘못된 알고리즘 지정 시 InvalidAlgorithmError 발생"""
        payload = {
            "sub": "user123",
            "exp": datetime.now(timezone.utc) + timedelta(hours=1),
        }
        token = jwt.encode(payload, TEST_SECRET, algorithm="HS256")  # HS256으로 서명

        with pytest.raises(jwt.InvalidAlgorithmError):  # 알고리즘 불일치 에러 예상
            jwt.decode(
                token, TEST_SECRET, algorithms=["HS512"]
            )  # HS512로 검증 시도 (불일치)
