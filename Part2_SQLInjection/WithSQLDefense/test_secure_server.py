#!/usr/bin/env python3
"""
보안 서버 테스트 클라이언트

정상적인 사용 시나리오를 테스트합니다.
"""

import asyncio
import json
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def test_secure_server():
    """보안 서버의 정상 동작 테스트"""

    print("=" * 70)
    print("🧪 보안 SQL 서버 - 정상 동작 테스트")
    print("=" * 70)

    import os
    script_dir = os.path.dirname(os.path.abspath(__file__))

    server_params = StdioServerParameters(
        command="python3",
        args=[os.path.join(script_dir, "secure_server.py")],
        env=None
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            # 1. 정상 로그인 테스트
            print("\n📝 테스트 1: 정상 로그인")
            print("-" * 70)
            result = await session.call_tool("login", arguments={
                "username": "alice",
                "password": "alice123"
            })
            print(f"결과: {result.content[0].text}")

            # 2. 사용자 검색 테스트
            print("\n📝 테스트 2: 사용자 검색")
            print("-" * 70)
            result = await session.call_tool("search_user", arguments={
                "username": "bob"
            })
            print(f"결과: {result.content[0].text}")

            # 3. 사용자 정보 조회 테스트
            print("\n📝 테스트 3: 사용자 ID로 조회")
            print("-" * 70)
            result = await session.call_tool("get_user_info", arguments={
                "user_id": "2"
            })
            print(f"결과: {result.content[0].text}")

            # 4. 이메일 업데이트 테스트
            print("\n📝 테스트 4: 이메일 업데이트")
            print("-" * 70)
            result = await session.call_tool("update_email", arguments={
                "username": "alice",
                "new_email": "alice.secure@example.com"
            })
            print(f"결과: {result.content[0].text}")

            # 5. 업데이트 확인
            print("\n📝 테스트 5: 업데이트 확인")
            print("-" * 70)
            result = await session.call_tool("search_user", arguments={
                "username": "alice"
            })
            print(f"결과: {result.content[0].text}")

            # 6. 잘못된 로그인 테스트
            print("\n📝 테스트 6: 잘못된 비밀번호")
            print("-" * 70)
            result = await session.call_tool("login", arguments={
                "username": "alice",
                "password": "wrongpassword"
            })
            print(f"결과: {result.content[0].text}")

    print("\n" + "=" * 70)
    print("✅ 모든 정상 테스트 완료")
    print("=" * 70)

if __name__ == "__main__":
    asyncio.run(test_secure_server())
