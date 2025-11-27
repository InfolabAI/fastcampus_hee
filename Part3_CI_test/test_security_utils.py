"""
보안 유틸리티 테스트
- 서버 없이 실행 가능한 단위 테스트
"""

import hashlib
import re
import secrets


class TestInputValidation:
    """입력 검증 테스트"""

    def test_sql_injection_pattern_detection(self):
        """SQL Injection 패턴 탐지"""
        dangerous_patterns = [
            "' OR '1'='1",
            "'; DROP TABLE users;--",
            "'; DELETE FROM users;--",
            "admin'--",
        ]

        # 간단한 SQL Injection 패턴: 따옴표 + SQL 키워드 또는 주석
        sql_injection_regex = re.compile(
            r"('.*\b(OR|AND|DROP|DELETE|SELECT|INSERT|UPDATE)\b)|('.*--)",
            re.IGNORECASE,
        )

        for pattern in dangerous_patterns:
            assert (
                sql_injection_regex.search(pattern) is not None
            ), f"Should detect: {pattern}"

    def test_safe_input_passes(self):
        """안전한 입력은 통과"""
        safe_inputs = [
            "john_doe",
            "user@example.com",
            "Hello World",
            "12345",
        ]

        sql_injection_regex = re.compile(
            r"('.*\b(OR|AND|DROP|DELETE|SELECT|INSERT|UPDATE)\b)|('.*--)",
            re.IGNORECASE,
        )

        for input_str in safe_inputs:
            assert (
                sql_injection_regex.search(input_str) is None
            ), f"Should pass: {input_str}"

    def test_xss_pattern_detection(self):
        """XSS 패턴 탐지"""
        dangerous_patterns = [
            "<script>alert('xss')</script>",
            "<img src=x onerror=alert('xss')>",
            "javascript:alert('xss')",
        ]

        xss_regex = re.compile(r"<script|javascript:|onerror=|onclick=", re.IGNORECASE)

        for pattern in dangerous_patterns:
            assert xss_regex.search(pattern) is not None, f"Should detect: {pattern}"


class TestPasswordHashing:
    """비밀번호 해싱 테스트"""

    def test_hash_is_deterministic(self):
        """같은 입력에 대해 같은 해시 생성"""
        password = "test_password_123"
        salt = "fixed_salt_for_testing"

        hash1 = hashlib.sha256((password + salt).encode()).hexdigest()
        hash2 = hashlib.sha256((password + salt).encode()).hexdigest()

        assert hash1 == hash2

    def test_different_passwords_different_hashes(self):
        """다른 비밀번호는 다른 해시 생성"""
        salt = "fixed_salt"

        hash1 = hashlib.sha256(("password1" + salt).encode()).hexdigest()
        hash2 = hashlib.sha256(("password2" + salt).encode()).hexdigest()

        assert hash1 != hash2

    def test_hash_length(self):
        """SHA256 해시 길이 확인 (64자)"""
        password_hash = hashlib.sha256("test".encode()).hexdigest()

        assert len(password_hash) == 64


class TestSecureRandomGeneration:
    """보안 난수 생성 테스트"""

    def test_token_uniqueness(self):
        """토큰 고유성 테스트"""
        tokens = [secrets.token_hex(32) for _ in range(100)]
        unique_tokens = set(tokens)

        assert len(tokens) == len(unique_tokens), "All tokens should be unique"

    def test_token_length(self):
        """토큰 길이 테스트"""
        token = secrets.token_hex(32)

        assert len(token) == 64  # 32 bytes = 64 hex characters

    def test_token_is_hexadecimal(self):
        """토큰이 16진수 문자열인지 확인"""
        token = secrets.token_hex(16)

        assert all(c in "0123456789abcdef" for c in token)


class TestEmailValidation:
    """이메일 검증 테스트"""

    def test_valid_emails(self):
        """유효한 이메일 형식"""
        valid_emails = [
            "user@example.com",
            "user.name@example.com",
            "user+tag@example.co.kr",
            "user123@sub.example.org",
        ]

        email_regex = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")

        for email in valid_emails:
            assert email_regex.match(email) is not None, f"Should be valid: {email}"

    def test_invalid_emails(self):
        """유효하지 않은 이메일 형식"""
        invalid_emails = [
            "userexample.com",  # @ 없음
            "user@",  # 도메인 없음
            "@example.com",  # 사용자명 없음
            "user@.com",  # 도메인 이름 없음
        ]

        email_regex = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")

        for email in invalid_emails:
            assert email_regex.match(email) is None, f"Should be invalid: {email}"
