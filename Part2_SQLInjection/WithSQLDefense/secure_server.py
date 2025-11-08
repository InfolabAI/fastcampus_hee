#!/usr/bin/env python3
"""
===========================================
보안 MCP 서버 - SQL Injection 방어
===========================================

강의 목적:
이 파일은 SQL Injection 공격을 방어하는 안전한 서버 구현을 보여줍니다.

핵심 방어 기법:
1. Prepared Statements (Parameterized Query) 사용
2. 입력 검증 (Input Validation)
3. 에러 메시지 최소화 (정보 노출 방지)

학습 포인트:
1. Prepared Statement vs String Concatenation의 차이
2. 입력 검증의 중요성과 구현 방법
3. 화이트리스트 기반 검증 (정규표현식 활용)
4. 방어 계층화 (Defense in Depth)

참고:
- vulnerable_server.py와 비교하며 학습하세요
- 같은 기능이지만 완전히 다른 보안 수준
"""

# ===========================================
# 필요한 라이브러리 임포트
# ===========================================

import asyncio  # 비동기 프로그래밍
import sqlite3  # SQLite 데이터베이스
import json     # JSON 데이터 처리
import re       # 정규표현식 (입력 검증에 사용)
from typing import Any
# MCP 서버 라이브러리
from mcp.server.models import InitializationOptions
import mcp.types as types
from mcp.server import NotificationOptions, Server
import mcp.server.stdio

# ===========================================
# 입력 검증 함수들 (화이트리스트 기반)
# ===========================================
# 보안 원칙: "허용할 것을 명시" (Whitelist)
# 블랙리스트 방식(금지할 것을 나열)은 우회 가능성이 높음

def validate_username(username: str) -> bool:
    """
    사용자 이름 검증 - 화이트리스트 방식

    검증 규칙:
    1. 길이 제한: 1~50자 (비어있거나 너무 길면 거부)
    2. 허용 문자: 영문자(a-z, A-Z), 숫자(0-9), 언더스코어(_)만 허용
    3. 특수문자 완전 차단: ', ", -, %, 등 SQL 메타문자 차단

    차단되는 공격 시도 예시:
    - "admin'--" (SQL 주석)
    - "admin' OR '1'='1" (OR 조건 삽입)
    - "admin%' AND 1=1--" (LIKE + 조건 삽입)

    정규표현식 설명:
    - ^: 문자열 시작
    - [a-zA-Z0-9_]+: 영문자/숫자/언더스코어가 1개 이상
    - $: 문자열 끝
    → 이 패턴 외의 모든 문자는 거부됨
    """
    # 길이 검증
    if not username or len(username) > 50:
        return False

    # 화이트리스트 패턴 매칭
    pattern = r'^[a-zA-Z0-9_]+$'
    return bool(re.match(pattern, username))


def validate_email(email: str) -> bool:
    """
    이메일 형식 검증

    검증 규칙:
    1. 길이 제한: 1~100자
    2. 이메일 형식: 로컬부분@도메인.TLD
    3. 허용 문자 제한

    정규표현식 설명:
    - ^[a-zA-Z0-9._%+-]+: 로컬 부분 (@ 앞)
    - @: 필수 구분자
    - [a-zA-Z0-9.-]+: 도메인 부분
    - \.[a-zA-Z]{2,}$: 최상위 도메인 (최소 2글자)

    차단되는 예시:
    - "test@example.com' OR '1'='1" (SQL Injection 시도)
    - "test<script>alert(1)</script>@example.com" (XSS 시도)
    """
    # 길이 검증
    if not email or len(email) > 100:
        return False

    # 이메일 패턴 매칭
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def validate_user_id(user_id: str) -> bool:
    """
    사용자 ID 검증 - 타입 검증 + 범위 제한

    검증 규칙:
    1. 타입 검증: 정수로 변환 가능해야 함
    2. 범위 제한: 1 ~ 999999 사이의 값만 허용

    차단되는 공격 시도 예시:
    - "1 OR 1=1" (OR 조건 삽입)
    - "1 UNION SELECT ..." (UNION 공격)
    - "1; DROP TABLE users--" (다중 쿼리)

    방어 메커니즘:
    - int() 변환 실패 시 False 반환
    - 범위 밖의 값 거부
    - SQL 구문이 포함된 문자열은 int() 변환 단계에서 차단됨
    """
    try:
        # 문자열을 정수로 변환 시도
        # "1 OR 1=1" 같은 문자열은 여기서 ValueError 발생
        int_id = int(user_id)

        # 범위 검증 (1~999999)
        return 1 <= int_id <= 999999

    except (ValueError, TypeError):
        # 숫자가 아니거나 잘못된 타입인 경우 거부
        return False

# ===========================================
# 데이터베이스 초기화
# ===========================================

def init_database():
    """
    보안 데이터베이스 초기화

    기능:
    - secure.db 파일 생성 (없으면)
    - users 테이블 생성
    - 샘플 사용자 데이터 삽입

    주의:
    - vulnerable_server.py와 동일한 스키마 사용
    - 동일한 테스트 데이터 사용 (비교를 위해)
    - 차이점은 데이터 삽입 시 Parameterized Query 사용
    """
    # secure.db 데이터베이스 연결
    conn = sqlite3.connect('secure.db')
    cursor = conn.cursor()

    # ===========================================
    # 테이블 스키마 생성
    # ===========================================
    # vulnerable_server.py와 동일한 구조
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,        -- 자동 증가 ID
            username TEXT NOT NULL UNIQUE, -- 사용자명 (중복 불가)
            password TEXT NOT NULL,        -- 비밀번호 (평문 - 실제론 해싱 필요)
            email TEXT,                    -- 이메일
            role TEXT DEFAULT 'user',      -- 역할 (user 또는 admin)
            credit_card TEXT               -- 신용카드 번호 (민감 정보)
        )
    ''')

    # ===========================================
    # 기존 데이터 삭제 (초기화를 위해)
    # ===========================================
    cursor.execute("DELETE FROM users")

    # ===========================================
    # 샘플 사용자 데이터 (vulnerable_server와 동일)
    # ===========================================
    sample_users = [
        # 관리자 계정
        ('admin', 'admin123', 'admin@example.com', 'admin', '1234-5678-9012-3456'),
        # 일반 사용자들
        ('alice', 'alice123', 'alice@example.com', 'user', '2345-6789-0123-4567'),
        ('bob', 'bob123', 'bob@example.com', 'user', '3456-7890-1234-5678'),
        ('charlie', 'charlie123', 'charlie@example.com', 'user', '4567-8901-2345-6789'),
    ]

    # ===========================================
    # Parameterized Query로 데이터 삽입
    # ===========================================
    # 중요: 여기서도 Parameterized Query 사용!
    # ? placeholder를 사용하여 SQL Injection 원천 차단
    #
    # 이것이 올바른 방법:
    #   cursor.executemany("INSERT ... VALUES (?, ?, ...)", data)
    #
    # 잘못된 방법 (vulnerable_server는 이렇게 안 함):
    #   for user in sample_users:
    #       query = f"INSERT ... VALUES ('{user[0]}', '{user[1]}', ...)"
    #       cursor.execute(query)
    cursor.executemany(
        'INSERT INTO users (username, password, email, role, credit_card) VALUES (?, ?, ?, ?, ?)',
        sample_users
    )

    # 변경사항 저장
    conn.commit()

    # 연결 종료
    conn.close()

    # 초기화 완료 메시지
    print("✅ 보안 데이터베이스 초기화 완료")
    print("📊 샘플 사용자: admin, alice, bob, charlie")

# ===========================================
# 글로벌 MCP 서버 인스턴스
# ===========================================
# 서버 이름: "secure-sql-server"
# vulnerable_server와 구분하기 위해 다른 이름 사용
server = Server("secure-sql-server")


# ===========================================
# 도구(Tool) 목록 정의
# ===========================================

@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    """
    MCP 클라이언트에게 제공할 도구 목록 반환

    제공하는 도구:
    1. login: 사용자 로그인
    2. search_user: 사용자 검색
    3. get_user_info: 사용자 정보 조회
    4. update_email: 이메일 업데이트

    모든 도구는 입력 검증 + Prepared Statement로 보호됨
    """
    return [
        types.Tool(
            name="login",
            description="사용자 로그인 (보안: Prepared Statement 사용)",
            inputSchema={
                "type": "object",
                "properties": {
                    "username": {
                        "type": "string",
                        "description": "사용자 이름 (영문자, 숫자, 언더스코어만 허용)"
                    },
                    "password": {
                        "type": "string",
                        "description": "비밀번호"
                    }
                },
                "required": ["username", "password"]
            }
        ),
        types.Tool(
            name="search_user",
            description="사용자 검색 (보안: Prepared Statement 사용)",
            inputSchema={
                "type": "object",
                "properties": {
                    "username": {
                        "type": "string",
                        "description": "검색할 사용자 이름"
                    }
                },
                "required": ["username"]
            }
        ),
        types.Tool(
            name="get_user_info",
            description="사용자 ID로 정보 조회 (보안: 입력 검증 + Prepared Statement)",
            inputSchema={
                "type": "object",
                "properties": {
                    "user_id": {
                        "type": "string",
                        "description": "사용자 ID (숫자만 허용)"
                    }
                },
                "required": ["user_id"]
            }
        ),
        types.Tool(
            name="update_email",
            description="이메일 업데이트 (보안: 이메일 형식 검증 + Prepared Statement)",
            inputSchema={
                "type": "object",
                "properties": {
                    "username": {
                        "type": "string",
                        "description": "사용자 이름"
                    },
                    "new_email": {
                        "type": "string",
                        "description": "새 이메일 주소"
                    }
                },
                "required": ["username", "new_email"]
            }
        )
    ]

# ===========================================
# 도구 실행 핸들러
# ===========================================

@server.call_tool()
async def handle_call_tool(
    name: str, arguments: dict | None
) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
    """
    클라이언트가 요청한 도구를 실행하는 핸들러

    중요:
    - 모든 SQL 쿼리는 Prepared Statement 사용
    - 모든 입력은 검증 후 사용
    - 에러 메시지는 최소화 (정보 노출 방지)

    보안 계층:
    1단계: 입력 검증 (validate_* 함수)
    2단계: Parameterized Query (? placeholder)
    3단계: 에러 처리 (상세 정보 숨김)
    """

    # ===========================================
    # 인자 검증
    # ===========================================
    if not arguments:
        raise ValueError("인자가 필요합니다")

    # ===========================================
    # 데이터베이스 연결
    # ===========================================
    conn = sqlite3.connect('secure.db')
    cursor = conn.cursor()

    try:
        # ===========================================
        # 도구 1: login (로그인)
        # ===========================================
        if name == "login":
            """
            보안 로그인 구현

            vulnerable_server.py와의 차이점:
            1. 입력 검증 추가 (validate_username)
            2. Prepared Statement 사용 (? placeholder)
            3. 디버그 출력에 파라미터 분리 표시

            방어되는 공격:
            - "admin' OR '1'='1" → 입력 검증에서 차단 (작은따옴표 불허)
            - "admin'--" → 입력 검증에서 차단
            - "' UNION SELECT ..." → 입력 검증에서 차단
            """

            # 인자 추출
            username = arguments.get("username", "")
            password = arguments.get("password", "")

            # ===========================================
            # 보안 1단계: 입력 검증
            # ===========================================
            # SQL을 실행하기 전에 입력 형식부터 검증
            # 잘못된 형식이면 즉시 거부 (SQL 실행 안 함)
            if not validate_username(username):
                return [
                    types.TextContent(
                        type="text",
                        text="❌ 잘못된 사용자 이름 형식입니다 (영문자, 숫자, 언더스코어만 허용)"
                    )
                ]

            # ===========================================
            # 보안 2단계: Prepared Statement 사용
            # ===========================================
            # 핵심 차이점!
            #
            # vulnerable_server의 취약한 코드:
            #   query = f"SELECT * FROM users WHERE username='{username}' AND password='{password}'"
            #   cursor.execute(query)
            #
            # 이 코드는 username과 password를 직접 문자열에 삽입하므로
            # username = "admin' OR '1'='1" 같은 입력이 SQL 구문으로 해석됨
            #
            # secure_server의 안전한 코드:
            query = "SELECT * FROM users WHERE username=? AND password=?"
            #
            # ? placeholder를 사용하고, 실제 값은 튜플로 전달
            # 데이터베이스 드라이버가 자동으로 이스케이프 처리
            # 어떤 입력도 SQL 구문으로 해석되지 않음!
            #
            # 작동 원리:
            # 1. SQL 쿼리 구조를 먼저 파싱 (WHERE username=? AND password=?)
            # 2. 파라미터 값을 데이터로 바인딩 ('admin', 'password123')
            # 3. 값은 절대 SQL 구문으로 해석되지 않음

            # 디버그 출력 (로그용)
            print(f"🔍 실행 쿼리: {query}")
            print(f"🔍 파라미터: username={username}, password=***")

            # ===========================================
            # Prepared Statement 실행
            # ===========================================
            # 두 번째 인자로 파라미터 튜플 전달
            # 이것이 핵심: 쿼리와 데이터를 분리!
            cursor.execute(query, (username, password))

            # 결과 조회
            result = cursor.fetchone()

            if result:
                user_data = {
                    'id': result[0],
                    'username': result[1],
                    'email': result[3],
                    'role': result[4]
                }
                return [
                    types.TextContent(
                        type="text",
                        text=f"✅ 로그인 성공!\n사용자 정보: {json.dumps(user_data, indent=2, ensure_ascii=False)}"
                    )
                ]
            else:
                return [
                    types.TextContent(
                        type="text",
                        text="❌ 로그인 실패: 사용자 이름 또는 비밀번호가 올바르지 않습니다"
                    )
                ]

        # ===========================================
        # 도구 2: search_user (사용자 검색)
        # ===========================================
        elif name == "search_user":
            """
            보안 사용자 검색 구현

            vulnerable_server와의 차이점:
            1. 입력 검증으로 SQL 메타문자 차단
            2. LIKE 패턴도 Prepared Statement로 처리

            방어되는 공격:
            - "%' OR '1'='1" → 입력 검증에서 차단
            - "' UNION SELECT credit_card ..." → 차단
            - "%'; DROP TABLE users--" → 차단

            LIKE 쿼리의 안전한 처리:
            - 패턴 생성은 Python에서 (f"%{username}%")
            - 생성된 패턴을 파라미터로 전달
            - SQL 구문 자체는 변경되지 않음
            """

            # 인자 추출
            username = arguments.get("username", "")

            # ===========================================
            # 보안 1단계: 입력 검증
            # ===========================================
            if not validate_username(username):
                return [
                    types.TextContent(
                        type="text",
                        text="❌ 잘못된 검색어 형식입니다 (영문자, 숫자, 언더스코어만 허용)"
                    )
                ]

            # ===========================================
            # 보안 2단계: Prepared Statement로 LIKE 쿼리 처리
            # ===========================================
            # vulnerable_server의 취약한 코드:
            #   query = f"SELECT ... WHERE username LIKE '%{username}%'"
            #   cursor.execute(query)
            #
            # secure_server의 안전한 코드:
            query = "SELECT id, username, email, role FROM users WHERE username LIKE ?"
            #
            # LIKE 패턴 생성:
            # - Python에서 % 와일드카드를 추가
            # - 생성된 문자열을 파라미터로 전달
            # - username이 "admin' OR '1'='1" 이어도
            #   LIKE 패턴 "%admin' OR '1'='1%" 으로 처리됨
            #   (SQL 구문이 아닌 검색 문자열로 취급)
            search_pattern = f"%{username}%"

            print(f"🔍 실행 쿼리: {query}")
            print(f"🔍 파라미터: pattern={search_pattern}")

            # Prepared Statement 실행
            cursor.execute(query, (search_pattern,))
            results = cursor.fetchall()

            if results:
                users = [
                    {
                        'id': row[0],
                        'username': row[1],
                        'email': row[2],
                        'role': row[3]
                    }
                    for row in results
                ]
                return [
                    types.TextContent(
                        type="text",
                        text=f"🔍 검색 결과 ({len(users)}명):\n{json.dumps(users, indent=2, ensure_ascii=False)}"
                    )
                ]
            else:
                return [
                    types.TextContent(
                        type="text",
                        text="❌ 검색 결과가 없습니다"
                    )
                ]

        # ===========================================
        # 도구 3: get_user_info (사용자 정보 조회)
        # ===========================================
        elif name == "get_user_info":
            """
            보안 사용자 정보 조회 구현

            vulnerable_server와의 차이점:
            1. 숫자 검증 (int 변환 + 범위 체크)
            2. Prepared Statement 사용

            방어되는 공격:
            - "1 OR 1=1" → int() 변환 실패로 차단
            - "1 UNION SELECT credit_card ..." → 차단
            - "1; DROP TABLE users--" → 차단

            주의사항:
            - user_id는 문자열로 받지만 정수로 검증
            - validate_user_id()에서 타입 변환 시도
            - 변환 실패 시 False 반환하여 공격 차단
            """

            # 인자 추출
            user_id = arguments.get("user_id", "")

            # ===========================================
            # 보안 1단계: 숫자 형식 검증
            # ===========================================
            # validate_user_id() 함수가 하는 일:
            # 1. int(user_id) 시도 → 실패 시 False
            # 2. 범위 검증 (1~999999)
            #
            # 이렇게 하면:
            # - "1 OR 1=1" → int() 변환 실패
            # - "1 UNION SELECT ..." → int() 변환 실패
            # - "999999999" → 범위 초과로 거부
            if not validate_user_id(user_id):
                return [
                    types.TextContent(
                        type="text",
                        text="❌ 잘못된 사용자 ID 형식입니다 (1-999999 범위의 숫자만 허용)"
                    )
                ]

            # ===========================================
            # 보안 2단계: Prepared Statement 사용
            # ===========================================
            # vulnerable_server의 취약한 코드:
            #   query = f"SELECT ... WHERE id={user_id}"
            #   cursor.execute(query)
            #
            # secure_server의 안전한 코드:
            query = "SELECT id, username, email, role FROM users WHERE id=?"

            print(f"🔍 실행 쿼리: {query}")
            print(f"🔍 파라미터: user_id={user_id}")

            # int(user_id)로 명시적 변환 후 전달
            # 이미 validate_user_id()에서 검증했으므로 안전
            cursor.execute(query, (int(user_id),))
            result = cursor.fetchone()

            if result:
                user_data = {
                    'id': result[0],
                    'username': result[1],
                    'email': result[2],
                    'role': result[3]
                }
                return [
                    types.TextContent(
                        type="text",
                        text=f"👤 사용자 정보:\n{json.dumps(user_data, indent=2, ensure_ascii=False)}"
                    )
                ]
            else:
                return [
                    types.TextContent(
                        type="text",
                        text="❌ 사용자를 찾을 수 없습니다"
                    )
                ]

        # ===========================================
        # 도구 4: update_email (이메일 업데이트)
        # ===========================================
        elif name == "update_email":
            """
            보안 이메일 업데이트 구현

            vulnerable_server와의 차이점:
            1. username과 email 모두 검증
            2. Prepared Statement로 UPDATE 쿼리 보호

            방어되는 공격:
            - new_email = "test@test.com', role='admin' WHERE '1'='1"
              → 이메일 형식 검증에서 차단
            - username = "alice' OR '1'='1"
              → username 검증에서 차단

            UPDATE 쿼리의 위험성:
            - vulnerable_server에서는 new_email을 통해
              다른 컬럼(role, credit_card 등)도 변경 가능
            - secure_server에서는 이메일 형식 검증으로
              SQL 메타문자 자체가 차단됨
            """

            # 인자 추출
            username = arguments.get("username", "")
            new_email = arguments.get("new_email", "")

            # ===========================================
            # 보안 1단계: 입력 검증
            # ===========================================
            # username 검증
            if not validate_username(username):
                return [
                    types.TextContent(
                        type="text",
                        text="❌ 잘못된 사용자 이름 형식입니다"
                    )
                ]

            # email 검증 (형식 확인)
            # "test', role='admin'..." 같은 공격은 여기서 차단됨
            if not validate_email(new_email):
                return [
                    types.TextContent(
                        type="text",
                        text="❌ 잘못된 이메일 형식입니다"
                    )
                ]

            # ===========================================
            # 보안 2단계: Prepared Statement 사용
            # ===========================================
            # vulnerable_server의 취약한 코드:
            #   query = f"UPDATE users SET email='{new_email}' WHERE username='{username}'"
            #   cursor.execute(query)
            #
            # 이렇게 하면:
            # new_email = "test@test.com', role='admin' WHERE '1'='1"
            # 실제 쿼리:
            # UPDATE users SET email='test@test.com', role='admin' WHERE '1'='1' WHERE username='alice'
            #                                         ↑ 추가 컬럼 변경!
            #
            # secure_server의 안전한 코드:
            query = "UPDATE users SET email=? WHERE username=?"

            print(f"🔍 실행 쿼리: {query}")
            print(f"🔍 파라미터: email={new_email}, username={username}")

            # Prepared Statement 실행
            # 파라미터가 데이터로만 취급되므로
            # 어떤 값을 넣어도 email 필드만 업데이트됨
            cursor.execute(query, (new_email, username))
            conn.commit()  # UPDATE는 commit 필요

            if cursor.rowcount > 0:
                return [
                    types.TextContent(
                        type="text",
                        text=f"✅ 이메일이 업데이트되었습니다"
                    )
                ]
            else:
                return [
                    types.TextContent(
                        type="text",
                        text="❌ 사용자를 찾을 수 없습니다"
                    )
                ]

        # ===========================================
        # 알 수 없는 도구 이름
        # ===========================================
        else:
            raise ValueError(f"알 수 없는 도구: {name}")

    # ===========================================
    # 에러 처리
    # ===========================================
    except sqlite3.Error as e:
        """
        보안 3단계: 에러 메시지 최소화

        목적:
        - 데이터베이스 구조 정보 노출 방지
        - 공격자에게 유용한 정보 제공 금지

        vulnerable_server의 문제:
        - 에러 메시지를 그대로 클라이언트에 반환
        - "syntax error near 'admin'" 같은 메시지로
          공격자가 SQL 구문 구조 파악 가능

        secure_server의 방어:
        - 상세 에러는 서버 로그에만 기록
        - 클라이언트에는 일반적인 메시지만 반환
        - 공격자가 시스템 정보를 얻을 수 없음

        에러 기반 SQL Injection 차단:
        - 에러 메시지를 통한 정보 수집 방지
        - Blind SQL Injection 난이도 증가
        """
        # 서버 로그에만 상세 정보 기록 (관리자용)
        print(f"⚠️ 데이터베이스 오류: {str(e)}")

        # 클라이언트에는 일반적인 메시지만 반환
        return [
            types.TextContent(
                type="text",
                text="❌ 요청 처리 중 오류가 발생했습니다. 잠시 후 다시 시도해주세요."
            )
        ]
    finally:
        # ===========================================
        # 리소스 정리
        # ===========================================
        # 에러 발생 여부와 관계없이 항상 실행
        # 데이터베이스 연결 종료로 리소스 누수 방지
        conn.close()


# ===========================================
# 메인 함수 - 서버 시작점
# ===========================================

async def main():
    """
    보안 SQL 서버 시작

    실행 순서:
    1. 데이터베이스 초기화 (secure.db)
    2. stdio를 통한 MCP 서버 시작
    3. 클라이언트 연결 대기

    보안 기능 요약:
    - ✅ Prepared Statements (? placeholder)
    - ✅ 입력 검증 (화이트리스트 기반)
    - ✅ 에러 메시지 최소화
    - ✅ 타입 검증 (숫자 필드)
    - ✅ 길이 제한
    - ✅ 정규표현식 검증

    테스트 방법:
    - test_secure_server.py: 정상 동작 확인
    - secure_attack_simulation.py: 공격 차단 확인
    """

    # ===========================================
    # 1단계: 데이터베이스 초기화
    # ===========================================
    init_database()

    # ===========================================
    # 2단계: MCP 서버 시작
    # ===========================================
    # stdio_server(): 표준 입출력을 통한 통신
    # - read_stream: 클라이언트로부터 요청 받기
    # - write_stream: 클라이언트에게 응답 보내기
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        # 서버 시작 메시지
        print("🛡️  보안 SQL 서버 시작됨 (SQL Injection 방어 적용)")
        print("✅ Prepared Statements 활성화")
        print("✅ 입력 검증 활성화")
        print("✅ 에러 메시지 최소화")

        # ===========================================
        # 3단계: 서버 실행 (무한 루프)
        # ===========================================
        # 클라이언트 요청을 계속 처리
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="secure-sql-server",
                server_version="1.0.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )


# ===========================================
# 프로그램 진입점
# ===========================================

if __name__ == "__main__":
    """
    스크립트가 직접 실행될 때만 서버 시작

    실행 방법:
    python3 secure_server.py

    또는 Docker 환경:
    make shell python3 Part2_SQLInjection/WithSQLDefense/secure_server.py
    """
    asyncio.run(main())


# ===========================================
# 학습 정리
# ===========================================
"""
이 파일에서 배운 SQL Injection 방어 기법:

1⃣ Prepared Statements (가장 중요!)
   - ? placeholder 사용
   - 쿼리 구조와 데이터 분리
   - 데이터베이스 드라이버가 자동 이스케이프

2⃣ 입력 검증 (Defense in Depth)
   - 화이트리스트 기반 (허용할 것만 명시)
   - 정규표현식으로 형식 검증
   - 타입 검증 (문자열 → 정수)
   - 길이 제한

3⃣ 에러 메시지 최소화
   - 상세 정보는 서버 로그에만
   - 클라이언트에는 일반 메시지
   - 에러 기반 공격 차단

4⃣ 다층 방어 (Layered Security)
   - 입력 검증 (1차 방어)
   - Prepared Statement (2차 방어)
   - 에러 최소화 (3차 방어)

비교 학습:
- vulnerable_server.py: f-string 사용, 검증 없음
- secure_server.py: Prepared Statement, 검증 있음
- attack_simulation.py: 공격이 성공하는 이유
- secure_attack_simulation.py: 공격이 차단되는 이유

다음 단계:
- test_secure_server.py로 정상 동작 확인
- secure_attack_simulation.py로 방어 확인
- 두 서버의 코드를 직접 비교해보세요!
"""
