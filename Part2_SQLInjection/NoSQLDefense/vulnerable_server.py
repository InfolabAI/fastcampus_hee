#!/usr/bin/env python3
"""
===========================================
 MCP 서버 - SQL Injection 취약점 데모
===========================================

 목적:
     교육용 SQL Injection 취약점 시연 코드입니다.
        절대 실제 서비스에 사용하지 마세요!

 주요 기능:
1. SQL Injection 취약점 시연
2. 로그인 기능
3. 사용자 검색 기능
4. 이메일 업데이트

 특징:
- 의도적으로 취약한 코드
- 학습 목적으로만 사용
- 안전한 코드는 secure_server.py 참조
"""

# ===========================================
# 필요한 라이브러리 임포트
# ===========================================

import asyncio  # 비동기 프로그래밍 지원
import sqlite3  # SQLite 데이터베이스 연결/조작
import json     # JSON 데이터 직렬화/역직렬화
from typing import Any  # 타입 힌팅

# MCP (Model Context Protocol) 라이브러리
# MCP는 AI 모델과 도구를 연결하는 프로토콜입니다
from mcp.server.models import InitializationOptions
import mcp.types as types
from mcp.server import NotificationOptions, Server
import mcp.server.stdio


# ===========================================
# 데이터베이스 초기화 함수
# ===========================================

def init_database():
    """
    취약한 데이터베이스 초기화 함수

    수행 작업:
    - SQLite 데이터베이스 (vulnerable.db) 생성
    - users 테이블 생성
    - 샘플 사용자 데이터 삽입

    보안 경고:
    - 평문으로 비밀번호 저장 (SQL Injection 시연용)
    - 절대 실제 서비스에 사용하지 마세요!
    - 실제로는 해싱 (bcrypt, argon2 등) 필수
    """

    # vulnerable.db 파일로 연결 (없으면 생성)
    conn = sqlite3.connect('vulnerable.db')
    cursor = conn.cursor()

    # ==========================================
    # 사용자 users 테이블 생성
    # ==========================================
    # IF NOT EXISTS: 이미 존재하면 건너뜀 (중복 방지)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,        -- 고유 사용자 ID
            username TEXT NOT NULL,        -- 사용자명 (필수)
            password TEXT NOT NULL,        -- 비밀번호 (경고: 평문 저장 - 취약!)
            email TEXT,                    -- 이메일 (선택)
            role TEXT DEFAULT 'user',      -- 권한 (기본값: 'user')
            credit_card TEXT               -- 신용카드 번호 (절대 평문 저장 금지!)
        )
    ''')

    # ==========================================
    # 기존 데이터 삭제 (초기화 목적)
    # ==========================================
    # 매번 새로운 데이터로 시작
    cursor.execute("DELETE FROM users")

    # ==========================================
    # 샘플 사용자 데이터 준비
    # ==========================================
    # 튜플 형식으로 사용자 정보 저장
    # (username, password, email, role, credit_card) 순서
    sample_users = [
        # 관리자 계정 - 라인 1
        ('admin', 'admin123', 'admin@example.com', 'admin', '1234-5678-9012-3456'),

        # 일반 사용자들 - 라인 2~4
        ('alice', 'alice123', 'alice@example.com', 'user', '2345-6789-0123-4567'),
        ('bob', 'bob123', 'bob@example.com', 'user', '3456-7890-1234-5678'),
        ('charlie', 'charlie123', 'charlie@example.com', 'user', '4567-8901-2345-6789'),
    ]

    # ==========================================
    # 안전한 방식으로 데이터 삽입 (Parameterized Query)
    # ==========================================
    # 참고: 여기서는 ? 플레이스홀더 사용
    # 이 방식은 SQL Injection 공격을 차단합니다!
    #
    # 위험한 방식: f"INSERT INTO users VALUES ('{username}', ...)"
    # 안전한 방식: "INSERT INTO users VALUES (?, ?, ...)", (username, ...)
    cursor.executemany(
        'INSERT INTO users (username, password, email, role, credit_card) VALUES (?, ?, ?, ?, ?)',
        sample_users
    )

    # 변경사항 저장
    conn.commit()

    # 데이터베이스 연결 종료 (리소스 정리)
    conn.close()

    # 초기화 완료 메시지
    print("데이터베이스 초기화 완료")
    print("테스트 계정: admin, alice, bob, charlie")


# ===========================================
# MCP 서버 인스턴스 생성
# ===========================================
# "vulnerable-sql-server"라는 이름의 MCP 서버 객체
server = Server("vulnerable-sql-server")


# ===========================================
# 사용 가능한 도구 (Tool) 목록 등록
# ===========================================

@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    """
    MCP 클라이언트에게 사용 가능한 도구 목록 반환

    제공되는 도구:
    - 총 4개의 도구 (모두 취약함)
    - 각 도구는 로그인, 검색, 조회 등의 기능
    - 모든 도구가 SQL Injection에 취약하도록 설계

    등록된 도구 목록:
    1. login: 사용자 로그인
    2. search_user: 사용자 검색
    3. get_user_info: 사용자 정보 조회
    4. update_email: 이메일 업데이트

    주의: 모두 SQL Injection 취약점 포함!
    """
    return [
        # ==========================================
        # 도구 1: 로그인 (login)
        # ==========================================
        types.Tool(
            name="login",
            description="사용자 로그인 (주의: SQL Injection 취약)",
            inputSchema={
                "type": "object",
                "properties": {
                    "username": {
                        "type": "string",
                        "description": "사용자명"
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
        # 도구 2: 사용자 검색 (search_user)
        # ==========================================
        types.Tool(
            name="search_user",
            description="사용자 검색 (주의: SQL Injection 취약)",
            inputSchema={
                "type": "object",
                "properties": {
                    "username": {
                        "type": "string",
                        "description": "검색할 사용자명"
                    }
                },
                "required": ["username"]
            }
        ),

        # ==========================================
        # 도구 3: 사용자 정보 조회 (get_user_info)
        # ==========================================
        types.Tool(
            name="get_user_info",
            description="사용자 ID로 정보 조회 (주의: SQL Injection 취약)",
            inputSchema={
                "type": "object",
                "properties": {
                    "user_id": {
                        "type": "string",  # 의도적으로 string 타입 (취약점!)
                        "description": "사용자 ID"
                    }
                },
                "required": ["user_id"]
            }
        ),

        # ==========================================
        # 도구 4: 이메일 업데이트 (update_email)
        # ==========================================
        types.Tool(
            name="update_email",
            description="이메일 업데이트 (주의: SQL Injection 취약)",
            inputSchema={
                "type": "object",
                "properties": {
                    "username": {
                        "type": "string",
                        "description": "사용자명"
                    },
                    "new_email": {
                        "type": "string",
                        "description": "새로운 이메일"
                    }
                },
                "required": ["username", "new_email"]
            }
        )
    ]


# ===========================================
#    
# ===========================================

@server.call_tool()
async def handle_call_tool(
    name: str, arguments: dict | None
) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
    """
        

     :
    - name:    (: "login", "search_user")
    - arguments:    ( )

     :     SQL Injection  !

       :
    1.     
    2. f-string SQL    
    3.   SQL    

     :
    -  : username = "admin"
      → : SELECT * FROM users WHERE username='admin'

    -  : username = "admin' OR '1'='1"
      → : SELECT * FROM users WHERE username='admin' OR '1'='1'
      → :    !
    """

    # ==========================================
    #    ( )
    # ==========================================
    if not arguments:
        raise ValueError(" ")

    # ==========================================
    #   
    # ==========================================
    #     
    # (      )
    conn = sqlite3.connect('vulnerable.db')
    cursor = conn.cursor()

    try:
        # ==========================================
        # 도구 실행: login
        # ==========================================
        if name == "login":
            """
            로그인 기능 - SQL Injection 취약

            도구 정의: 라인 148
            위험도: 🔴 매우 높음 (인증 우회)

            공격 예시:
            1. 인증 우회: admin' OR '1'='1
            2. 주석 처리: admin'--
            3. UNION 공격: ' UNION SELECT ...
            """

            # 사용자 입력 받기 (검증 없음!)
            username = arguments.get("username", "")
            password = arguments.get("password", "")

            # ==========================================
            # 🚨 취약한 쿼리 작성 - 위험!
            # ==========================================
            # 문제점: f-string으로 직접 결합
            # 사용자 입력의 따옴표(')가 쿼리 구조를 변경
            #
            # 공격 예시:
            # username = "admin' OR '1'='1"
            # password = "anything"
            #
            # 생성되는 쿼리:
            # SELECT * FROM users
            # WHERE username='admin' OR '1'='1' AND password='anything'
            #                         ↑ 항상 참!
            #
            # 안전한 방법:
            # query = "SELECT * FROM users WHERE username=? AND password=?"
            # cursor.execute(query, (username, password))
            query = f"SELECT * FROM users WHERE username='{username}' AND password='{password}'"

            # 실행할 쿼리 출력 (교육 목적)
            print(f"실행 쿼리: {query}")

            # 쿼리 실행 (입력값 검증 없음!)
            cursor.execute(query)

            # 첫 번째 결과 가져오기
            result = cursor.fetchone()

            if result:
                # ==========================================
                # 로그인 성공 - 사용자 정보 반환
                # ==========================================
                # result 튜플: (id, username, password, email, role, credit_card)
                user_data = {
                    'id': result[0],
                    'username': result[1],
                    'email': result[3],
                    'role': result[4]
                    # 주의: credit_card(result[5])는 숨김
                    # 하지만 SQL Injection으로 추출 가능!
                }
                return [
                    types.TextContent(
                        type="text",
                        text=f"로그인 성공!\n사용자 정보: {json.dumps(user_data, indent=2, ensure_ascii=False)}"
                    )
                ]
            else:
                # ==========================================
                # 로그인 실패
                # ==========================================
                return [
                    types.TextContent(
                        type="text",
                        text="로그인 실패: 사용자명 또는 비밀번호가 잘못되었습니다"
                    )
                ]

        # ==========================================
        # 도구 실행: search_user
        # ==========================================
        elif name == "search_user":
            """
            사용자 검색 기능 - SQL Injection 취약

            도구 정의: 라인 180
            위험도: 🟠 높음 (정보 노출)

            공격 예시:
            1. 전체 조회: %' OR '1'='1
            2. 데이터 추출: ' UNION SELECT credit_card, ...
            3. 테이블 구조 탐색: ' UNION SELECT * FROM sqlite_master--
            """

            # 검색어 입력 받기
            username = arguments.get("username", "")

            # ==========================================
            # 🚨 취약한 검색 쿼리 - 위험!
            # ==========================================
            # LIKE 패턴과 SQL Injection 조합
            #
            # 공격 예시 1: 전체 검색
            # username = "%' OR '1'='1"
            # 쿼리: SELECT ... WHERE username LIKE '%%' OR '1'='1%'
            #
            # 공격 예시 2: UNION 공격
            # username = "' UNION SELECT id, username, credit_card, 'hacked' FROM users--"
            # 결과: 신용카드 정보 노출!
            query = f"SELECT id, username, email, role FROM users WHERE username LIKE '%{username}%'"

            print(f"실행 쿼리: {query}")

            cursor.execute(query)
            results = cursor.fetchall()  # 모든 결과 가져오기

            if results:
                # 결과를 딕셔너리 리스트로 변환
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
                        text=f"검색 결과 ({len(users)}명):\n{json.dumps(users, indent=2, ensure_ascii=False)}"
                    )
                ]
            else:
                return [
                    types.TextContent(
                        type="text",
                        text="검색 결과가 없습니다"
                    )
                ]

        # ==========================================
        # 도구 실행: get_user_info
        # ==========================================
        elif name == "get_user_info":
            """
            사용자 정보 조회 - SQL Injection 취약

            도구 정의: 라인 215
            위험도: 🟠 높음 (정보 노출)

            특징:
            - 숫자형 SQL Injection 취약점!
            - 따옴표 없어도 공격 가능 (WHERE id=1 OR 1=1)

            공격 예시:
            1. 조건 우회: 1 OR 1=1
            2. UNION 공격: 1 UNION SELECT credit_card, username, email, role FROM users
            3. 스키마 탐색: 1 UNION SELECT sql, name, '', '' FROM sqlite_master
            """

            # 사용자 ID 받기 (타입 검증 없음 - 취약!)
            user_id = arguments.get("user_id", "")

            # ==========================================
            # 🚨 취약한 숫자형 쿼리 - 위험!
            # ==========================================
            # 따옴표 없는 숫자 조건도 취약
            #
            # 공격 예시 1: 조건 우회
            # user_id = "1 OR 1=1"
            # 쿼리: SELECT ... WHERE id=1 OR 1=1
            # 결과: 모든 사용자 조회 (OR 1=1이 항상 참)
            #
            # 공격 예시 2: UNION 공격 (민감 정보 추출)
            # user_id = "1 UNION SELECT id, username, credit_card, role FROM users"
            # 결과: 정상 정보 + 신용카드 정보
            #
            # 안전한 방법:
            # query = "SELECT ... WHERE id=?"
            # cursor.execute(query, (user_id,))
            query = f"SELECT id, username, email, role FROM users WHERE id={user_id}"

            print(f"실행 쿼리: {query}")

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
                        text=f"사용자 정보:\n{json.dumps(user_data, indent=2, ensure_ascii=False)}"
                    )
                ]
            else:
                return [
                    types.TextContent(
                        type="text",
                        text="사용자를 찾을 수 없습니다"
                    )
                ]

        # ==========================================
        # 도구 실행: update_email
        # ==========================================
        elif name == "update_email":
            """
            이메일 업데이트 - SQL Injection 취약

            도구 정의: 라인 248
            위험도: 🔴 매우 높음 (권한 상승)

            위험 요소:
            - UPDATE 구문의 SQL Injection 취약
            - 권한 상승 공격 가능
            - 대량 데이터 변조 위험

            공격 예시:
            1. 다중 업데이트: alice', email='hacked@evil.com' WHERE '1'='1
            2. 권한 상승: alice', role='admin' WHERE username='alice
            3. 복합 변조: alice', role='admin', credit_card='stolen' WHERE username='alice
            """

            # 입력값 받기
            username = arguments.get("username", "")
            new_email = arguments.get("new_email", "")

            # ==========================================
            # 🚨 취약한 UPDATE 쿼리 - 매우 위험!
            # ==========================================
            # UPDATE 구문 SQL Injection
            #
            # 공격 예시 1: 권한 상승 (일반 사용자 → 관리자)
            # username = "alice"
            # new_email = "alice@example.com', role='admin' WHERE username='alice'--"
            #
            # 생성 쿼리:
            # UPDATE users SET email='alice@example.com', role='admin'
            # WHERE username='alice'--' WHERE username='alice'
            #                        ↑ 주석 처리
            # → alice가 admin 권한 획득!
            #
            # 공격 예시 2: 대량 변조
            # username = "alice' OR '1'='1"
            # new_email = "hacked@evil.com"
            #
            # 결과: 모든 사용자 이메일 변경!
            #
            # 안전한 방법:
            # query = "UPDATE users SET email=? WHERE username=?"
            # cursor.execute(query, (new_email, username))
            query = f"UPDATE users SET email='{new_email}' WHERE username='{username}'"

            print(f"실행 쿼리: {query}")

            cursor.execute(query)
            conn.commit()  # 변경사항 저장

            # rowcount: 영향받은 행 수
            if cursor.rowcount > 0:
                return [
                    types.TextContent(
                        type="text",
                        text=f"이메일 업데이트 완료 ({cursor.rowcount}명 영향)"
                    )
                ]
            else:
                return [
                    types.TextContent(
                        type="text",
                        text="사용자를 찾을 수 없습니다"
                    )
                ]

        # ==========================================
        # 알 수 없는 도구 이름
        # ==========================================
        else:
            raise ValueError(f"알 수 없는 도구: {name}")

    # ==========================================
    # 예외 처리
    # ==========================================
    except sqlite3.Error as e:
        """
        데이터베이스 에러 처리

        교육적 주의사항!
        - 에러 메시지로 DB 구조 노출 위험
        - 공격자가 테이블명, 컬럼명, 타입 정보 획득 가능

        SQL Injection 에러 유형:
        1. 문법 에러 (MySQL, PostgreSQL, SQLite 등)
        2. 타입 에러
        3. 제약조건 위반

        보안 개선 방법:
        - 상세 에러는 로그에만 기록: "문제가 발생했습니다"
        - 클라이언트에는 일반 메시지만 반환
        - 에러 정보로 시스템 구조 유추 불가하게
        """
        return [
            types.TextContent(
                type="text",
                text=f"데이터베이스 오류: {str(e)}\n(실제 서비스에서는 상세 에러 노출 금지!)"
            )
        ]
    finally:
        # ==========================================
        # 리소스 정리
        # ==========================================
        # 항상 연결 종료 보장
        # (성공 여부와 관계없이 항상 실행)
        conn.close()


# ===========================================
# 메인 함수 - 서버 시작점
# ===========================================

async def main():
    """
    MCP 서버 메인 함수

    실행 순서:
    1. 데이터베이스 초기화
    2. stdio(표준 입출력)로 MCP 서버 시작
    3. 클라이언트 요청 대기

    stdio 통신 방식:
    - MCP 프로토콜은 stdin/stdout으로 통신
    - JSON-RPC 메시지 형식
    - 클라이언트와 양방향 통신
    """

    # ==========================================
    # 데이터베이스 초기화
    # ==========================================
    init_database()

    # ==========================================
    # MCP 서버 시작
    # ==========================================
    # stdio_server() 컨텍스트 매니저:
    # - read_stream: 입력 스트림
    # - write_stream: 출력 스트림
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        # 서버 시작 메시지
        print("취약한 SQL 서버 시작 (SQL Injection 교육용)")
        print("주의: 절대 실제 서비스에 사용하지 마세요!")

        # 서버 실행 (무한 루프로 요청 처리)
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
# 프로그램 진입점
# ===========================================
if __name__ == "__main__":
    """
    스크립트가 직접 실행될 때만 실행
    (import되면 실행되지 않음)

    asyncio.run(): 비동기 함수를 실행하는 진입점
    """
    asyncio.run(main())


# ===========================================
# 학습 가이드
# ===========================================
"""
강의 핵심 내용:

1⃣ SQL Injection이란?
   - 사용자 입력이 SQL 쿼리 구조를 변경
   - 인증 우회, SQL 쿼리 조작 가능

2⃣ 취약한 코드:
    f"SELECT * FROM users WHERE username='{username}'"
    f"UPDATE users SET email='{email}' WHERE id={id}"

3⃣ 안전한 코드:
    cursor.execute("SELECT * FROM users WHERE username=?", (username,))
    cursor.execute("UPDATE users SET email=? WHERE id=?", (email, id))

4⃣ 공격 기법:
   - 인증 우회: ' OR '1'='1
   - 주석 처리: admin'--
   - UNION 공격: ' UNION SELECT ...
   - 권한 상승: ', role='admin' WHERE '1'='1

5⃣ 방어 방법:
   ✅ Parameterized Query 사용 (필수)
   ✅ 입력값 검증 (화이트리스트 방식)
   ✅ 최소 권한 원칙 (DB 계정 권한 제한)
   ✅ 에러 메시지 숨김
   ✅ WAF 사용

관련 파일:
- test_vulnerable_server.py: 기능 테스트
- attack_simulation.py: 공격 시뮬레이션
- secure_server.py: 안전한 구현 예제
"""
