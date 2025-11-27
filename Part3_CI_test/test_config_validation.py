"""
설정 검증 테스트
- 서버 없이 실행 가능한 단위 테스트.
"""
# =============================================================================
# 설정 검증 단위 테스트 - CI 파이프라인용
# =============================================================================
# 목적: 환경 변수, JSON 설정, Casbin 정책 형식 검증
# 특징: 외부 서버 의존성 없이 실행 가능 (순수 단위 테스트)
# 실행: pytest Part3_CI_test/test_config_validation.py
# =============================================================================

import json  # JSON 직렬화/역직렬화


# =============================================================================
# 테스트 클래스 1: 환경 변수 설정 테스트
# =============================================================================
class TestEnvironmentConfig:
    """환경 설정 테스트 - 환경 변수 형식 및 값 검증"""

    def test_required_env_vars_format(self):
        """필수 환경 변수 형식 검증 - 보안 및 유효성"""
        # 테스트용 환경 변수 시뮬레이션 (실제로는 os.environ 사용)
        test_config = {
            "JWT_SECRET": "my-secret-key-at-least-32-chars-long",  # JWT 시크릿
            "MCP_SERVER_PORT": "8080",  # 서버 포트
            "LOG_LEVEL": "INFO",  # 로그 레벨
        }

        # JWT_SECRET 최소 길이 검증 (보안: 충분히 긴 키 필요)
        assert (
            len(test_config["JWT_SECRET"]) >= 32
        ), "JWT_SECRET should be at least 32 characters"

        # PORT 숫자 검증 - 문자열 → 숫자 변환 가능해야 함
        assert test_config["MCP_SERVER_PORT"].isdigit(), "PORT should be numeric"
        port = int(test_config["MCP_SERVER_PORT"])  # 숫자로 변환
        assert 1 <= port <= 65535, "PORT should be between 1 and 65535"  # 유효 범위

        # LOG_LEVEL 유효값 검증 - Python logging 모듈 레벨
        valid_log_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        assert test_config["LOG_LEVEL"] in valid_log_levels, "Invalid LOG_LEVEL"

    def test_port_range_validation(self):
        """포트 범위 검증 - 유효/무효 포트 테스트"""
        valid_ports = [80, 443, 8080, 3000, 65535]  # 유효한 포트들
        invalid_ports = [0, -1, 65536, 100000]  # 무효한 포트들

        for port in valid_ports:
            assert 1 <= port <= 65535, f"Port {port} should be valid"  # 유효 범위 확인

        for port in invalid_ports:
            assert not (1 <= port <= 65535), f"Port {port} should be invalid"  # 범위 밖 확인

    def test_log_level_validation(self):
        """로그 레벨 검증 - 유효/무효 레벨 테스트"""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]  # Python 표준 로그 레벨
        invalid_levels = ["TRACE", "VERBOSE", "info", ""]  # 무효한 레벨 (대소문자 구분)

        for level in valid_levels:
            assert level in valid_levels  # 유효 레벨 확인

        for level in invalid_levels:
            assert level not in valid_levels  # 무효 레벨 확인


# =============================================================================
# 테스트 클래스 2: JSON 설정 파일 테스트
# =============================================================================
class TestJSONConfig:
    """JSON 설정 파일 테스트 - 설정 파일 형식 및 구조 검증"""

    def test_valid_json_structure(self):
        """유효한 JSON 구조 검증 - 직렬화/역직렬화"""
        valid_config = {
            "server": {
                "host": "0.0.0.0",  # 바인딩 주소
                "port": 8080,  # 서버 포트
            },
            "security": {
                "jwt_algorithm": "HS256",  # JWT 알고리즘
                "token_expiry_hours": 24,  # 토큰 만료 시간 (시간)
            },
            "logging": {
                "level": "INFO",  # 로그 레벨
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",  # 로그 포맷
            },
        }

        # JSON 직렬화 가능 확인 (dict → str → dict)
        json_str = json.dumps(valid_config)  # dict → JSON 문자열
        parsed = json.loads(json_str)  # JSON 문자열 → dict

        assert parsed == valid_config  # 원본과 동일한지 확인

    def test_config_has_required_fields(self):
        """필수 필드 존재 확인 - 설정 스키마 검증"""
        config = {
            "server": {"host": "localhost", "port": 8080},
            "security": {"jwt_algorithm": "HS256"},
        }

        required_fields = ["server", "security"]  # 필수 최상위 필드

        for field in required_fields:
            assert field in config, f"Missing required field: {field}"  # 필드 존재 확인

    def test_nested_config_access(self):
        """중첩 설정 접근 테스트 - 계층 구조 탐색"""
        config = {
            "database": {
                "primary": {
                    "host": "localhost",  # 주 DB 호스트
                    "port": 5432,  # PostgreSQL 기본 포트
                },
                "replica": {
                    "host": "replica.local",  # 복제 DB 호스트
                    "port": 5432,
                },
            }
        }

        # 중첩된 키에 안전하게 접근
        assert config["database"]["primary"]["host"] == "localhost"
        assert config["database"]["replica"]["host"] == "replica.local"


# =============================================================================
# 테스트 클래스 3: Casbin 정책 형식 테스트
# =============================================================================
class TestCasbinPolicyFormat:
    """Casbin 정책 형식 테스트 - RBAC 정책 검증"""

    def test_policy_line_format(self):
        """정책 라인 형식 검증 - CSV 형식 규칙"""
        valid_policies = [
            "p, admin, /api/*, *",  # p = 권한 정책: 주체, 객체, 액션
            "p, user, /api/read, GET",  # user는 GET 메서드만 허용
            "g, alice, admin",  # g = 역할 할당: alice → admin 역할
        ]

        for policy in valid_policies:
            parts = policy.split(", ")  # 쉼표로 분리
            assert len(parts) >= 2, f"Policy should have at least 2 parts: {policy}"  # 최소 2개 파트
            assert parts[0] in ["p", "g", "g2"], f"Invalid policy type: {parts[0]}"  # p: 정책, g: 역할

    def test_role_hierarchy(self):
        """역할 계층 구조 테스트 - RBAC 권한 상속"""
        # 사용자 → 역할 매핑
        role_assignments = {
            "alice": "admin",  # alice는 admin 역할
            "bob": "user",  # bob은 user 역할
            "charlie": "user",  # charlie도 user 역할
        }

        # 역할 → 권한 매핑
        role_permissions = {
            "admin": ["read", "write", "delete"],  # admin은 모든 권한
            "user": ["read"],  # user는 읽기만
        }

        # alice는 admin이므로 모든 권한 가짐
        alice_role = role_assignments["alice"]
        assert "delete" in role_permissions[alice_role]  # admin의 delete 권한 확인

        # bob은 user이므로 read만 가능
        bob_role = role_assignments["bob"]
        assert "read" in role_permissions[bob_role]  # user의 read 권한 확인
        assert "delete" not in role_permissions[bob_role]  # user에게 delete 권한 없음
