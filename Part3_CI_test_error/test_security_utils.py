# B105: 하드코딩된 비밀번호
HARDCODED_PASSWORD = "super_secret_password_123"
DB_PASSWORD = "admin123"

# B307: eval 사용 (코드 인젝션 취약점)


def unsafe_eval(user_input):
    return eval(user_input)

# B102: exec 사용 (코드 실행 취약점)


def unsafe_exec(code):
    exec(code)


# B104: 모든 인터페이스 바인딩
SERVER_HOST = "0.0.0.0"
