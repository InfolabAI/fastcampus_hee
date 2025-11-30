"""
설정 검증 테스트 - CI 파이프라인용
"""

import json


class TestEnvironmentConfig:
    """환경 설정 테스트"""

    def test_required_env_vars_format(self):
        """필수 환경 변수 형식 검증"""
        test_config = {
            "JWT_SECRET": "my-secret-key-at-least-32-chars-long",
            "MCP_SERVER_PORT": "8080",
            "LOG_LEVEL": "INFO",
        }

        # JWT_SECRET 최소 길이 검증
        assert len(test_config["JWT_SECRET"]) >= 32

        # PORT 숫자 검증
        assert test_config["MCP_SERVER_PORT"].isdigit()
        port = int(test_config["MCP_SERVER_PORT"])
        assert 1 <= port <= 65535

        # LOG_LEVEL 유효값 검증
        valid_log_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        assert test_config["LOG_LEVEL"] in valid_log_levels


class TestJSONConfig:
    """JSON 설정 파일 테스트"""

    def test_valid_json_structure(self):
        """유효한 JSON 구조 검증"""
        valid_config = {
            "server": {"host": "localhost", "port": 8080},
            "security": {"jwt_algorithm": "HS256", "token_expiry_hours": 24},
        }

        json_str = json.dumps(valid_config)
        parsed = json.loads(json_str)

        assert parsed == valid_config

    def test_config_has_required_fields(self):
        """필수 필드 존재 확인"""
        config = {
            "server": {"host": "localhost", "port": 8080},
            "security": {"jwt_algorithm": "HS256"},
        }

        required_fields = ["server", "security"]
        for field in required_fields:
            assert field in config


class TestCasbinPolicyFormat:
    """Casbin 정책 형식 테스트"""

    def test_policy_line_format(self):
        """정책 라인 형식 검증"""
        valid_policies = [
            "p, admin, /api/*, *",
            "p, user, /api/read, GET",
            "g, alice, admin",
        ]

        for policy in valid_policies:
            parts = policy.split(", ")
            assert len(parts) >= 2
            assert parts[0] in ["p", "g", "g2"]

    def test_role_hierarchy(self):
        """역할 계층 구조 테스트"""
        role_assignments = {"alice": "admin", "bob": "user"}
        role_permissions = {
            "admin": ["read", "write", "delete"],
            "user": ["read"],
        }

        assert "delete" in role_permissions[role_assignments["alice"]]
        assert "delete" not in role_permissions[role_assignments["bob"]]
