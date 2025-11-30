"""
보안 유틸리티 테스트 - CI 파이프라인용
"""

import hashlib
import re
import secrets


class TestInputValidation:
    """입력 검증 테스트 - SQL Injection 및 XSS 패턴 탐지"""

    def test_sql_injection_pattern_detection(self):
        """SQL Injection 패턴 탐지"""
        dangerous_patterns = [
            "' OR '1'='1",
            "'; DROP TABLE users;--",
            "admin'--",
        ]

        sql_injection_regex = re.compile(
            r"('.*\b(OR|AND|DROP|DELETE|SELECT|INSERT|UPDATE)\b)|('.*--)",
            re.IGNORECASE,
        )

        for pattern in dangerous_patterns:
            assert sql_injection_regex.search(pattern) is not None

    def test_safe_input_passes(self):
        """안전한 입력은 통과"""
        safe_inputs = ["john_doe", "user@example.com", "Hello World"]

        sql_injection_regex = re.compile(
            r"('.*\b(OR|AND|DROP|DELETE|SELECT|INSERT|UPDATE)\b)|('.*--)",
            re.IGNORECASE,
        )

        for input_str in safe_inputs:
            assert sql_injection_regex.search(input_str) is None

    def test_xss_pattern_detection(self):
        """XSS 패턴 탐지"""
        dangerous_patterns = [
            "<script>alert('xss')</script>",
            "<img src=x onerror=alert('xss')>",
        ]

        xss_regex = re.compile(r"<script|onerror=|onclick=", re.IGNORECASE)

        for pattern in dangerous_patterns:
            assert xss_regex.search(pattern) is not None


class TestPasswordHashing:
    """비밀번호 해싱 테스트"""

    def test_hash_is_deterministic(self):
        """같은 입력은 같은 해시 생성"""
        test_input = "test_input_123"
        salt = "fixed_salt_for_testing"

        hash1 = hashlib.sha256((test_input + salt).encode()).hexdigest()
        hash2 = hashlib.sha256((test_input + salt).encode()).hexdigest()

        assert hash1 == hash2

    def test_different_inputs_different_hashes(self):
        """다른 입력은 다른 해시 생성"""
        salt = "fixed_salt"

        hash1 = hashlib.sha256(("input1" + salt).encode()).hexdigest()
        hash2 = hashlib.sha256(("input2" + salt).encode()).hexdigest()

        assert hash1 != hash2

    def test_hash_length(self):
        """SHA256 해시 길이 확인 (64자)"""
        result = hashlib.sha256("test".encode()).hexdigest()
        assert len(result) == 64


class TestSecureRandomGeneration:
    """보안 난수 생성 테스트"""

    def test_token_uniqueness(self):
        """토큰 고유성 테스트"""
        tokens = [secrets.token_hex(32) for _ in range(100)]
        assert len(tokens) == len(set(tokens))

    def test_token_length(self):
        """토큰 길이 테스트"""
        token = secrets.token_hex(32)
        assert len(token) == 64

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
        ]

        email_regex = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")

        for email in valid_emails:
            assert email_regex.match(email) is not None

    def test_invalid_emails(self):
        """유효하지 않은 이메일 형식"""
        invalid_emails = ["userexample.com", "user@", "@example.com"]

        email_regex = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")

        for email in invalid_emails:
            assert email_regex.match(email) is None
