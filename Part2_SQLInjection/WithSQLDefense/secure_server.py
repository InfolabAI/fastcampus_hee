#!/usr/bin/env python3
"""
보안이 강화된 MCP 서버 - SQL Injection 방어

이 서버는 Prepared Statements와 입력 검증을 통해 SQL Injection을 방어합니다.
"""

import asyncio
import sqlite3
import json
import re
from typing import Any
from mcp.server.models import InitializationOptions
import mcp.types as types
from mcp.server import NotificationOptions, Server
import mcp.server.stdio

# 입력 검증 함수들
def validate_username(username: str) -> bool:
    """사용자 이름 검증: 영문자, 숫자, 언더스코어만 허용"""
    if not username or len(username) > 50:
        return False
    pattern = r'^[a-zA-Z0-9_]+$'
    return bool(re.match(pattern, username))

def validate_email(email: str) -> bool:
    """이메일 형식 검증"""
    if not email or len(email) > 100:
        return False
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))

def validate_user_id(user_id: str) -> bool:
    """사용자 ID 검증: 숫자만 허용"""
    try:
        int_id = int(user_id)
        return 1 <= int_id <= 999999
    except (ValueError, TypeError):
        return False

# 데이터베이스 초기화
def init_database():
    """데이터베이스와 샘플 데이터 초기화"""
    conn = sqlite3.connect('secure.db')
    cursor = conn.cursor()

    # 사용자 테이블 생성
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            username TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            email TEXT,
            role TEXT DEFAULT 'user',
            credit_card TEXT
        )
    ''')

    # 샘플 데이터 삽입
    cursor.execute("DELETE FROM users")

    sample_users = [
        ('admin', 'admin123', 'admin@example.com', 'admin', '1234-5678-9012-3456'),
        ('alice', 'alice123', 'alice@example.com', 'user', '2345-6789-0123-4567'),
        ('bob', 'bob123', 'bob@example.com', 'user', '3456-7890-1234-5678'),
        ('charlie', 'charlie123', 'charlie@example.com', 'user', '4567-8901-2345-6789'),
    ]

    cursor.executemany(
        'INSERT INTO users (username, password, email, role, credit_card) VALUES (?, ?, ?, ?, ?)',
        sample_users
    )

    conn.commit()
    conn.close()
    print("✅ 보안 데이터베이스 초기화 완료")
    print("📊 샘플 사용자: admin, alice, bob, charlie")

# MCP 서버 설정
server = Server("secure-sql-server")

@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    """사용 가능한 도구 목록 반환"""
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

@server.call_tool()
async def handle_call_tool(
    name: str, arguments: dict | None
) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
    """도구 실행 처리 - 모든 SQL은 Prepared Statement 사용"""

    if not arguments:
        raise ValueError("인자가 필요합니다")

    conn = sqlite3.connect('secure.db')
    cursor = conn.cursor()

    try:
        if name == "login":
            username = arguments.get("username", "")
            password = arguments.get("password", "")

            # 🛡️ 보안 1: 입력 검증
            if not validate_username(username):
                return [
                    types.TextContent(
                        type="text",
                        text="❌ 잘못된 사용자 이름 형식입니다 (영문자, 숫자, 언더스코어만 허용)"
                    )
                ]

            # 🛡️ 보안 2: Prepared Statement 사용
            query = "SELECT * FROM users WHERE username=? AND password=?"

            print(f"🔍 실행 쿼리: {query}")
            print(f"🔍 파라미터: username={username}, password=***")

            cursor.execute(query, (username, password))
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

        elif name == "search_user":
            username = arguments.get("username", "")

            # 🛡️ 보안 1: 입력 검증
            if not validate_username(username):
                return [
                    types.TextContent(
                        type="text",
                        text="❌ 잘못된 검색어 형식입니다 (영문자, 숫자, 언더스코어만 허용)"
                    )
                ]

            # 🛡️ 보안 2: Prepared Statement로 LIKE 쿼리 처리
            query = "SELECT id, username, email, role FROM users WHERE username LIKE ?"
            search_pattern = f"%{username}%"

            print(f"🔍 실행 쿼리: {query}")
            print(f"🔍 파라미터: pattern={search_pattern}")

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

        elif name == "get_user_info":
            user_id = arguments.get("user_id", "")

            # 🛡️ 보안 1: 숫자 형식 검증
            if not validate_user_id(user_id):
                return [
                    types.TextContent(
                        type="text",
                        text="❌ 잘못된 사용자 ID 형식입니다 (1-999999 범위의 숫자만 허용)"
                    )
                ]

            # 🛡️ 보안 2: Prepared Statement 사용
            query = "SELECT id, username, email, role FROM users WHERE id=?"

            print(f"🔍 실행 쿼리: {query}")
            print(f"🔍 파라미터: user_id={user_id}")

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

        elif name == "update_email":
            username = arguments.get("username", "")
            new_email = arguments.get("new_email", "")

            # 🛡️ 보안 1: 입력 검증
            if not validate_username(username):
                return [
                    types.TextContent(
                        type="text",
                        text="❌ 잘못된 사용자 이름 형식입니다"
                    )
                ]

            if not validate_email(new_email):
                return [
                    types.TextContent(
                        type="text",
                        text="❌ 잘못된 이메일 형식입니다"
                    )
                ]

            # 🛡️ 보안 2: Prepared Statement 사용
            query = "UPDATE users SET email=? WHERE username=?"

            print(f"🔍 실행 쿼리: {query}")
            print(f"🔍 파라미터: email={new_email}, username={username}")

            cursor.execute(query, (new_email, username))
            conn.commit()

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

        else:
            raise ValueError(f"알 수 없는 도구: {name}")

    except sqlite3.Error as e:
        # 🛡️ 보안 3: 에러 메시지 최소화 (DB 구조 정보 노출 방지)
        print(f"⚠️ 데이터베이스 오류: {str(e)}")  # 서버 로그에만 기록
        return [
            types.TextContent(
                type="text",
                text="❌ 요청 처리 중 오류가 발생했습니다. 잠시 후 다시 시도해주세요."
            )
        ]
    finally:
        conn.close()

async def main():
    """서버 시작"""
    # 데이터베이스 초기화
    init_database()

    # stdio를 통해 MCP 서버 실행
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        print("🛡️  보안 SQL 서버 시작됨 (SQL Injection 방어 적용)")
        print("✅ Prepared Statements 활성화")
        print("✅ 입력 검증 활성화")
        print("✅ 에러 메시지 최소화")

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

if __name__ == "__main__":
    asyncio.run(main())
