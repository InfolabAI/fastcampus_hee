#!/usr/bin/env python3
"""
===========================================
취약한 MCP 서버 - SQL Injection 취약점 존재
===========================================

📚 강의 목적:
이 서버는 교육 목적으로 의도적으로 SQL Injection 취약점을 포함하고 있습니다.
실제 프로덕션 환경에서는 절대 이러한 패턴을 사용하면 안 됩니다!

🎯 학습 목표:
1. SQL Injection이 무엇인지 이해
2. 어떤 코드가 취약한지 파악
3. 공격자가 어떻게 악용할 수 있는지 학습
4. 실제 피해 사례 체험

⚠️ 주의사항:
- 이 코드는 교육용입니다
- 실제 서비스에 절대 사용하지 마세요
- 학습한 내용을 악의적으로 사용하지 마세요
"""

# ===========================================
# 📦 필요한 라이브러리 임포트
# ===========================================

import asyncio  # 비동기 프로그래밍을 위한 라이브러리
import sqlite3  # SQLite 데이터베이스 연결/조작을 위한 라이브러리
import json     # JSON 형식 데이터 처리를 위한 라이브러리
from typing import Any  # 타입 힌팅을 위한 라이브러리

# MCP (Model Context Protocol) 관련 라이브러리
# MCP는 AI 에이전트가 외부 시스템과 상호작용하기 위한 프로토콜입니다
from mcp.server.models import InitializationOptions
import mcp.types as types
from mcp.server import NotificationOptions, Server
import mcp.server.stdio


# ===========================================
# 🗄️ 데이터베이스 초기화 함수
# ===========================================

def init_database():
    """
    데이터베이스와 샘플 데이터를 초기화하는 함수

    📝 설명:
    - SQLite 데이터베이스 파일(vulnerable.db)을 생성합니다
    - users 테이블을 만들고 샘플 데이터를 삽입합니다
    - 매번 실행 시 깨끗한 상태로 시작하기 위해 기존 데이터를 삭제합니다

    ⚠️ 보안 참고:
    - 이 함수 자체는 안전합니다 (SQL Injection 취약점 없음)
    - 하지만 실제 서비스에서는 비밀번호를 평문으로 저장하면 안 됩니다!
    - 반드시 해싱(bcrypt, argon2 등)을 사용해야 합니다
    """

    # vulnerable.db 파일에 연결 (없으면 자동 생성)
    conn = sqlite3.connect('vulnerable.db')
    cursor = conn.cursor()

    # ==========================================
    # 📊 users 테이블 생성
    # ==========================================
    # IF NOT EXISTS: 테이블이 없을 때만 생성 (이미 있으면 무시)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,        -- 자동 증가하는 고유 ID
            username TEXT NOT NULL,        -- 사용자 이름 (필수)
            password TEXT NOT NULL,        -- 비밀번호 (필수, ⚠️ 평문 저장은 위험!)
            email TEXT,                    -- 이메일 (선택)
            role TEXT DEFAULT 'user',      -- 역할 (기본값: 'user')
            credit_card TEXT               -- 신용카드 번호 (⚠️ 민감 정보!)
        )
    ''')

    # ==========================================
    # 🧹 기존 데이터 삭제 (깨끗한 시작)
    # ==========================================
    # 실습의 일관성을 위해 매번 초기 상태로 리셋합니다
    cursor.execute("DELETE FROM users")

    # ==========================================
    # 👥 샘플 사용자 데이터 정의
    # ==========================================
    # 강의/실습을 위한 테스트 데이터
    # (username, password, email, role, credit_card) 형식
    sample_users = [
        # 관리자 계정 - 공격 대상 1번
        ('admin', 'admin123', 'admin@example.com', 'admin', '1234-5678-9012-3456'),

        # 일반 사용자 계정들 - 공격 대상 2~4번
        ('alice', 'alice123', 'alice@example.com', 'user', '2345-6789-0123-4567'),
        ('bob', 'bob123', 'bob@example.com', 'user', '3456-7890-1234-5678'),
        ('charlie', 'charlie123', 'charlie@example.com', 'user', '4567-8901-2345-6789'),
    ]

    # ==========================================
    # ✅ 안전한 데이터 삽입 방식 (Parameterized Query)
    # ==========================================
    # 📌 중요: 여기서는 ? 플레이스홀더를 사용합니다
    # 이것이 SQL Injection을 막는 올바른 방법입니다!
    #
    # ❌ 잘못된 방법: f"INSERT INTO users VALUES ('{username}', ...)"
    # ✅ 올바른 방법: "INSERT INTO users VALUES (?, ?, ...)", (username, ...)
    cursor.executemany(
        'INSERT INTO users (username, password, email, role, credit_card) VALUES (?, ?, ?, ?, ?)',
        sample_users
    )

    # 변경사항을 데이터베이스에 저장
    conn.commit()

    # 연결 종료 (리소스 정리)
    conn.close()

    # 초기화 완료 메시지 출력
    print("✅ 데이터베이스 초기화 완료")
    print("📊 샘플 사용자: admin, alice, bob, charlie")


# ===========================================
# 🖥️ MCP 서버 인스턴스 생성
# ===========================================
# "vulnerable-sql-server"라는 이름의 MCP 서버를 만듭니다
server = Server("vulnerable-sql-server")


# ===========================================
# 🔧 사용 가능한 도구(Tool) 목록 정의
# ===========================================

@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    """
    MCP 클라이언트에게 사용 가능한 도구 목록을 알려주는 함수

    📝 설명:
    - 이 서버가 제공하는 4가지 기능(도구)을 정의합니다
    - 각 도구는 이름, 설명, 입력 스키마를 가집니다
    - 클라이언트는 이 목록을 보고 어떤 기능을 사용할지 선택합니다

    🎯 제공되는 도구:
    1. login: 사용자 로그인
    2. search_user: 사용자 검색
    3. get_user_info: 사용자 정보 조회
    4. update_email: 이메일 업데이트

    ⚠️ 모든 도구가 SQL Injection에 취약합니다!
    """
    return [
        # ==========================================
        # 🔐 도구 1: 로그인 (login)
        # ==========================================
        types.Tool(
            name="login",
            description="사용자 로그인 (취약: SQL Injection 가능)",
            inputSchema={
                "type": "object",
                "properties": {
                    "username": {
                        "type": "string",
                        "description": "사용자 이름"
                    },
                    "password": {
                        "type": "string",
                        "description": "비밀번호"
                    }
                },
                "required": ["username", "password"]  # 필수 입력값
            }
        ),

        # ==========================================
        # 🔍 도구 2: 사용자 검색 (search_user)
        # ==========================================
        types.Tool(
            name="search_user",
            description="사용자 검색 (취약: SQL Injection 가능)",
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

        # ==========================================
        # 👤 도구 3: 사용자 정보 조회 (get_user_info)
        # ==========================================
        types.Tool(
            name="get_user_info",
            description="사용자 ID로 정보 조회 (취약: SQL Injection 가능)",
            inputSchema={
                "type": "object",
                "properties": {
                    "user_id": {
                        "type": "string",  # 숫자지만 string으로 받음 (취약점!)
                        "description": "사용자 ID"
                    }
                },
                "required": ["user_id"]
            }
        ),

        # ==========================================
        # ✉️ 도구 4: 이메일 업데이트 (update_email)
        # ==========================================
        types.Tool(
            name="update_email",
            description="이메일 업데이트 (취약: SQL Injection 가능)",
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
# ⚙️ 도구 실행 핸들러
# ===========================================

@server.call_tool()
async def handle_call_tool(
    name: str, arguments: dict | None
) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
    """
    클라이언트가 요청한 도구를 실행하는 함수

    📝 매개변수:
    - name: 실행할 도구의 이름 (예: "login", "search_user")
    - arguments: 도구에 전달할 인자들 (딕셔너리 형태)

    🔴 위험: 이 함수의 모든 분기에서 SQL Injection 취약점이 존재합니다!

    ⚠️ 취약점 발생 원리:
    1. 사용자 입력을 검증 없이 받아들임
    2. f-string으로 SQL 쿼리 문자열을 직접 조합
    3. 공격자가 입력에 SQL 명령을 삽입할 수 있음

    💡 예시:
    - 정상 입력: username = "admin"
      → 쿼리: SELECT * FROM users WHERE username='admin'

    - 악의적 입력: username = "admin' OR '1'='1"
      → 쿼리: SELECT * FROM users WHERE username='admin' OR '1'='1'
      → 결과: 모든 사용자 정보가 조회됨!
    """

    # ==========================================
    # ✅ 입력값 검증 (최소한의 체크)
    # ==========================================
    if not arguments:
        raise ValueError("인자가 필요합니다")

    # ==========================================
    # 🗄️ 데이터베이스 연결
    # ==========================================
    # 매 요청마다 새로운 연결을 생성합니다
    # (실제 서비스에서는 연결 풀을 사용하는 것이 효율적입니다)
    conn = sqlite3.connect('vulnerable.db')
    cursor = conn.cursor()

    try:
        # ==========================================
        # 🔐 도구 실행: login
        # ==========================================
        if name == "login":
            """
            로그인 기능 - SQL Injection 취약점 데모

            🎯 취약점 위치: 148번 라인
            ⚠️ 위험도: 🔴 매우 높음 (인증 우회 가능)

            💣 가능한 공격:
            1. 인증 우회: admin' OR '1'='1
            2. 주석 처리: admin'--
            3. UNION 공격: ' UNION SELECT ...
            """

            # 사용자 입력 받기 (검증 없음!)
            username = arguments.get("username", "")
            password = arguments.get("password", "")

            # ==========================================
            # 🔴 취약점 발생 지점!
            # ==========================================
            # ❌ 잘못된 방법: f-string으로 직접 쿼리 조합
            # 사용자 입력이 따옴표(')로 쿼리 구조를 깨뜨릴 수 있습니다
            #
            # 💡 공격 예시:
            # username = "admin' OR '1'='1"
            # password = "anything"
            #
            # 결과 쿼리:
            # SELECT * FROM users
            # WHERE username='admin' OR '1'='1' AND password='anything'
            #                         ↑ 항상 참이 됨!
            #
            # ✅ 올바른 방법:
            # query = "SELECT * FROM users WHERE username=? AND password=?"
            # cursor.execute(query, (username, password))
            query = f"SELECT * FROM users WHERE username='{username}' AND password='{password}'"

            # 실행되는 쿼리를 출력 (교육 목적)
            print(f"🔍 실행 쿼리: {query}")

            # 쿼리 실행 (공격 쿼리도 그대로 실행됨!)
            cursor.execute(query)

            # 첫 번째 결과 가져오기
            result = cursor.fetchone()

            if result:
                # ==========================================
                # ✅ 로그인 성공 - 사용자 정보 반환
                # ==========================================
                # result는 튜플: (id, username, password, email, role, credit_card)
                user_data = {
                    'id': result[0],
                    'username': result[1],
                    'email': result[3],
                    'role': result[4]
                    # 📌 주의: credit_card(result[5])는 반환하지 않음
                    # 하지만 SQL Injection으로 여전히 탈취 가능!
                }
                return [
                    types.TextContent(
                        type="text",
                        text=f"✅ 로그인 성공!\n사용자 정보: {json.dumps(user_data, indent=2, ensure_ascii=False)}"
                    )
                ]
            else:
                # ==========================================
                # ❌ 로그인 실패
                # ==========================================
                return [
                    types.TextContent(
                        type="text",
                        text="❌ 로그인 실패: 사용자 이름 또는 비밀번호가 올바르지 않습니다"
                    )
                ]

        # ==========================================
        # 🔍 도구 실행: search_user
        # ==========================================
        elif name == "search_user":
            """
            사용자 검색 기능 - SQL Injection 취약점 데모

            🎯 취약점 위치: 180번 라인
            ⚠️ 위험도: 🟠 높음 (정보 유출 가능)

            💣 가능한 공격:
            1. 모든 사용자 조회: %' OR '1'='1
            2. 민감 정보 유출: ' UNION SELECT credit_card, ...
            3. 다른 테이블 조회: ' UNION SELECT * FROM sqlite_master--
            """

            # 검색할 사용자 이름 받기
            username = arguments.get("username", "")

            # ==========================================
            # 🔴 취약점 발생 지점!
            # ==========================================
            # LIKE 쿼리에서도 SQL Injection 가능합니다
            #
            # 💡 공격 예시 1: 모든 사용자 조회
            # username = "%' OR '1'='1"
            # 결과: SELECT ... WHERE username LIKE '%%' OR '1'='1%'
            #
            # 💡 공격 예시 2: UNION 공격
            # username = "' UNION SELECT id, username, credit_card, 'hacked' FROM users--"
            # 결과: 모든 사용자의 신용카드 정보가 노출됨!
            query = f"SELECT id, username, email, role FROM users WHERE username LIKE '%{username}%'"

            print(f"🔍 실행 쿼리: {query}")

            cursor.execute(query)
            results = cursor.fetchall()  # 모든 결과 가져오기

            if results:
                # 결과를 리스트로 변환
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

        # ==========================================
        # 👤 도구 실행: get_user_info
        # ==========================================
        elif name == "get_user_info":
            """
            사용자 정보 조회 기능 - SQL Injection 취약점 데모

            🎯 취약점 위치: 215번 라인
            ⚠️ 위험도: 🟠 높음 (정보 유출 가능)

            💡 교육 포인트:
            - 숫자형 필드도 SQL Injection에 취약할 수 있습니다!
            - 따옴표 없이도 공격 가능 (WHERE id=1 OR 1=1)

            💣 가능한 공격:
            1. 모든 사용자 조회: 1 OR 1=1
            2. UNION 공격: 1 UNION SELECT credit_card, username, email, role FROM users
            3. 테이블 구조 파악: 1 UNION SELECT sql, name, '', '' FROM sqlite_master
            """

            # 사용자 ID 받기 (문자열로 받음 - 취약점!)
            user_id = arguments.get("user_id", "")

            # ==========================================
            # 🔴 취약점 발생 지점!
            # ==========================================
            # 숫자 필드도 따옴표 없이 그대로 삽입하면 취약합니다
            #
            # 💡 공격 예시 1: 모든 사용자 조회
            # user_id = "1 OR 1=1"
            # 결과: SELECT ... WHERE id=1 OR 1=1
            #       (OR 1=1은 항상 참이므로 모든 행이 선택됨)
            #
            # 💡 공격 예시 2: UNION 공격 (신용카드 정보 유출)
            # user_id = "1 UNION SELECT id, username, credit_card, role FROM users"
            # 결과: 원래 사용자 정보 + 모든 사용자의 신용카드 정보
            #
            # ✅ 올바른 방법:
            # query = "SELECT ... WHERE id=?"
            # cursor.execute(query, (user_id,))
            query = f"SELECT id, username, email, role FROM users WHERE id={user_id}"

            print(f"🔍 실행 쿼리: {query}")

            cursor.execute(query)
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

        # ==========================================
        # ✉️ 도구 실행: update_email
        # ==========================================
        elif name == "update_email":
            """
            이메일 업데이트 기능 - SQL Injection 취약점 데모

            🎯 취약점 위치: 248번 라인
            ⚠️ 위험도: 🔴 매우 높음 (데이터 변조 가능)

            💡 교육 포인트:
            - UPDATE 쿼리에서도 SQL Injection 가능
            - 의도하지 않은 데이터 변경 가능
            - 전체 데이터베이스 손상 위험

            💣 가능한 공격:
            1. 모든 사용자 이메일 변조: alice', email='hacked@evil.com' WHERE '1'='1
            2. 역할 권한 상승: alice', role='admin' WHERE username='alice
            3. 다중 컬럼 변조: alice', role='admin', credit_card='stolen' WHERE username='alice
            """

            # 입력값 받기
            username = arguments.get("username", "")
            new_email = arguments.get("new_email", "")

            # ==========================================
            # 🔴 취약점 발생 지점!
            # ==========================================
            # UPDATE 쿼리도 동일하게 취약합니다
            #
            # 💡 공격 예시 1: 권한 상승 (일반 사용자 → 관리자)
            # username = "alice"
            # new_email = "alice@example.com', role='admin' WHERE username='alice'--"
            #
            # 결과 쿼리:
            # UPDATE users SET email='alice@example.com', role='admin'
            # WHERE username='alice'--' WHERE username='alice'
            #                        ↑ 주석 처리됨
            # → alice의 역할이 admin으로 변경됨!
            #
            # 💡 공격 예시 2: 모든 사용자 데이터 변조
            # username = "alice' OR '1'='1"
            # new_email = "hacked@evil.com"
            #
            # 결과: 모든 사용자의 이메일이 변경됨!
            #
            # ✅ 올바른 방법:
            # query = "UPDATE users SET email=? WHERE username=?"
            # cursor.execute(query, (new_email, username))
            query = f"UPDATE users SET email='{new_email}' WHERE username='{username}'"

            print(f"🔍 실행 쿼리: {query}")

            cursor.execute(query)
            conn.commit()  # 변경사항을 데이터베이스에 저장

            # rowcount: 영향받은 행의 개수
            if cursor.rowcount > 0:
                return [
                    types.TextContent(
                        type="text",
                        text=f"✅ 이메일이 업데이트되었습니다 ({cursor.rowcount}개 행 영향받음)"
                    )
                ]
            else:
                return [
                    types.TextContent(
                        type="text",
                        text="❌ 사용자를 찾을 수 없습니다"
                    )
                ]

        # ==========================================
        # ❌ 알 수 없는 도구
        # ==========================================
        else:
            raise ValueError(f"알 수 없는 도구: {name}")

    # ==========================================
    # 🚨 예외 처리
    # ==========================================
    except sqlite3.Error as e:
        """
        데이터베이스 에러 처리

        🔴 또 다른 취약점!
        - 에러 메시지를 그대로 노출하면 안 됩니다
        - 데이터베이스 구조, 테이블명, 컬럼명 등이 유출될 수 있습니다

        💡 공격자는 에러 메시지를 보고:
        1. 데이터베이스 종류 파악 (MySQL, PostgreSQL, SQLite 등)
        2. 테이블 구조 추론
        3. 성공적인 공격 쿼리 작성

        ✅ 올바른 방법:
        - 일반적인 메시지만 표시: "오류가 발생했습니다"
        - 상세한 에러는 서버 로그에만 기록
        - 절대 클라이언트에게 내부 정보 노출 금지
        """
        return [
            types.TextContent(
                type="text",
                text=f"❌ 데이터베이스 오류: {str(e)}\n이 정보로 데이터베이스 구조를 파악할 수 있습니다!"
            )
        ]
    finally:
        # ==========================================
        # 🧹 리소스 정리
        # ==========================================
        # 항상 데이터베이스 연결을 닫아야 합니다
        # (리소스 누수 방지, 동시 접속 제한 문제 해결)
        conn.close()


# ===========================================
# 🚀 메인 함수 - 서버 시작
# ===========================================

async def main():
    """
    MCP 서버를 시작하는 메인 함수

    📝 실행 흐름:
    1. 데이터베이스 초기화
    2. stdio(표준 입출력)를 통한 MCP 서버 실행
    3. 클라이언트 요청 대기

    💡 stdio 방식:
    - MCP는 표준 입출력(stdin/stdout)을 통해 통신합니다
    - JSON-RPC 프로토콜을 사용합니다
    - 다른 프로세스나 도구와 쉽게 연동 가능
    """

    # ==========================================
    # 📊 데이터베이스 초기화
    # ==========================================
    init_database()

    # ==========================================
    # 🖥️ MCP 서버 실행
    # ==========================================
    # stdio_server() 컨텍스트 매니저:
    # - read_stream: 클라이언트로부터 데이터 받기
    # - write_stream: 클라이언트에게 데이터 보내기
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        # 서버 시작 메시지 출력
        print("⚠️  취약한 SQL 서버 시작됨 (SQL Injection 취약점 존재)")
        print("📝 이 서버는 교육 목적으로만 사용하세요!")

        # 서버 실행 (클라이언트 요청 처리 시작)
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="vulnerable-sql-server",
                server_version="1.0.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )


# ===========================================
# 🎬 프로그램 진입점
# ===========================================
if __name__ == "__main__":
    """
    스크립트가 직접 실행될 때만 서버를 시작합니다
    (import될 때는 실행되지 않음)

    asyncio.run(): 비동기 메인 함수를 실행하는 헬퍼 함수
    """
    asyncio.run(main())


# ===========================================
# 📚 학습 정리
# ===========================================
"""
🎓 이 파일에서 배운 내용:

1️⃣ SQL Injection이란?
   - 사용자 입력을 SQL 쿼리에 직접 삽입할 때 발생
   - 공격자가 임의의 SQL 명령을 실행할 수 있음

2️⃣ 취약한 패턴:
   ❌ f"SELECT * FROM users WHERE username='{username}'"
   ❌ f"UPDATE users SET email='{email}' WHERE id={id}"

3️⃣ 안전한 패턴:
   ✅ cursor.execute("SELECT * FROM users WHERE username=?", (username,))
   ✅ cursor.execute("UPDATE users SET email=? WHERE id=?", (email, id))

4️⃣ 공격 기법:
   - 인증 우회: ' OR '1'='1
   - 주석 처리: admin'--
   - UNION 공격: ' UNION SELECT ...
   - 데이터 변조: ', role='admin' WHERE '1'='1

5️⃣ 보안 원칙:
   ✅ 항상 Parameterized Query 사용
   ✅ 사용자 입력 검증 (화이트리스트 방식)
   ✅ 최소 권한 원칙 (DB 계정 권한 제한)
   ✅ 에러 메시지 노출 금지
   ✅ 로깅 및 모니터링

📖 다음 학습:
- test_vulnerable_server.py: 정상 동작 테스트
- attack_simulation.py: 실제 공격 시뮬레이션
- secure_server.py: 방어 메커니즘 구현
"""
