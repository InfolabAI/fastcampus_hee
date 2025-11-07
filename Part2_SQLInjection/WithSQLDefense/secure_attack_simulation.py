#!/usr/bin/env python3
"""
보안 서버에 대한 SQL Injection 공격 방어 테스트

모든 SQL Injection 공격이 차단되는지 확인합니다.
"""

import asyncio
import json
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def run_defense_test():
    """SQL Injection 공격 방어 테스트"""

    print("=" * 70)
    print("🛡️  SQL INJECTION 방어 테스트")
    print("=" * 70)
    print("✅ 모든 공격이 차단되는지 확인합니다")
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

            attack_count = 0
            blocked_count = 0

            # 방어 테스트 1: 인증 우회 시도
            print("\n🎯 방어 테스트 1: 인증 우회 시도")
            print("-" * 70)
            print("📝 공격 시도: ' OR '1'='1")
            attack_count += 1

            result = await session.call_tool("login", arguments={
                "username": "admin' OR '1'='1",
                "password": "anything"
            })
            response = result.content[0].text

            if "❌" in response or "잘못된" in response:
                print(f"✅ 차단 성공!\n{response}")
                blocked_count += 1
            else:
                print(f"❌ 차단 실패!\n{response}")

            # 방어 테스트 2: UNION SELECT 시도
            print("\n🎯 방어 테스트 2: UNION SELECT 데이터 추출 시도")
            print("-" * 70)
            print("📝 공격 시도: UNION SELECT")
            attack_count += 1

            result = await session.call_tool("search_user", arguments={
                "username": "' UNION SELECT id, username, password, credit_card FROM users--"
            })
            response = result.content[0].text

            if "❌" in response or "잘못된" in response:
                print(f"✅ 차단 성공!\n{response}")
                blocked_count += 1
            else:
                print(f"❌ 차단 실패!\n{response}")

            # 방어 테스트 3: 숫자 필드 SQL Injection
            print("\n🎯 방어 테스트 3: 숫자 필드 SQL Injection 시도")
            print("-" * 70)
            print("📝 공격 시도: UNION SELECT in numeric field")
            attack_count += 1

            result = await session.call_tool("get_user_info", arguments={
                "user_id": "1 UNION SELECT id, username, password, credit_card FROM users"
            })
            response = result.content[0].text

            if "❌" in response or "잘못된" in response:
                print(f"✅ 차단 성공!\n{response}")
                blocked_count += 1
            else:
                print(f"❌ 차단 실패!\n{response}")

            # 방어 테스트 4: UPDATE Injection
            print("\n🎯 방어 테스트 4: UPDATE Injection 시도")
            print("-" * 70)
            print("📝 공격 시도: SQL Injection in UPDATE")
            attack_count += 1

            result = await session.call_tool("update_email", arguments={
                "username": "alice",
                "new_email": "hacked@evil.com' WHERE '1'='1"
            })
            response = result.content[0].text

            if "❌" in response or "잘못된" in response:
                print(f"✅ 차단 성공!\n{response}")
                blocked_count += 1
            else:
                print(f"❌ 차단 실패!\n{response}")

            # 방어 테스트 5: SQL 주석 우회
            print("\n🎯 방어 테스트 5: SQL 주석(--) 우회 시도")
            print("-" * 70)
            print("📝 공격 시도: admin'--")
            attack_count += 1

            result = await session.call_tool("login", arguments={
                "username": "admin'--",
                "password": "ignored"
            })
            response = result.content[0].text

            if "❌" in response or "잘못된" in response:
                print(f"✅ 차단 성공!\n{response}")
                blocked_count += 1
            else:
                print(f"❌ 차단 실패!\n{response}")

            # 방어 테스트 6: 세미콜론을 이용한 다중 쿼리
            print("\n🎯 방어 테스트 6: Stacked Queries 시도")
            print("-" * 70)
            print("📝 공격 시도: '; DROP TABLE users--")
            attack_count += 1

            result = await session.call_tool("search_user", arguments={
                "username": "alice'; DROP TABLE users--"
            })
            response = result.content[0].text

            if "❌" in response or "잘못된" in response:
                print(f"✅ 차단 성공!\n{response}")
                blocked_count += 1
            else:
                print(f"❌ 차단 실패!\n{response}")

            # 방어 테스트 7: 특수문자 삽입
            print("\n🎯 방어 테스트 7: 특수문자 삽입 시도")
            print("-" * 70)
            print("📝 공격 시도: <script>alert('XSS')</script>")
            attack_count += 1

            result = await session.call_tool("search_user", arguments={
                "username": "<script>alert('XSS')</script>"
            })
            response = result.content[0].text

            if "❌" in response or "잘못된" in response:
                print(f"✅ 차단 성공!\n{response}")
                blocked_count += 1
            else:
                print(f"⚠️  입력 허용됨 (XSS 방어는 별도 필요)\n{response}")

            # 방어 테스트 8: Blind SQL Injection 시도
            print("\n🎯 방어 테스트 8: Blind SQL Injection 시도")
            print("-" * 70)
            print("📝 공격 시도: Time-based blind injection")
            attack_count += 1

            result = await session.call_tool("search_user", arguments={
                "username": "' OR SLEEP(5)--"
            })
            response = result.content[0].text

            if "❌" in response or "잘못된" in response:
                print(f"✅ 차단 성공!\n{response}")
                blocked_count += 1
            else:
                print(f"❌ 차단 실패!\n{response}")

            # 정상 동작 확인
            print("\n🎯 보너스 테스트: 정상 사용자 접근")
            print("-" * 70)
            result = await session.call_tool("login", arguments={
                "username": "alice",
                "password": "alice123"
            })
            response = result.content[0].text

            if "✅" in response or "성공" in response:
                print(f"✅ 정상 접근 허용\n{response}")
            else:
                print(f"⚠️  정상 접근 차단됨\n{response}")

            # 데이터베이스 무결성 확인
            print("\n🎯 데이터베이스 무결성 확인")
            print("-" * 70)
            result = await session.call_tool("search_user", arguments={
                "username": "alice"
            })
            print(f"데이터베이스 상태: {result.content[0].text}")

    print("\n" + "=" * 70)
    print("🛡️  방어 테스트 완료")
    print("=" * 70)
    print()
    print(f"📊 방어 통계:")
    print(f"  총 공격 시도: {attack_count}회")
    print(f"  차단 성공: {blocked_count}회")
    print(f"  차단 성공률: {(blocked_count/attack_count*100):.1f}%")
    print()

    if blocked_count == attack_count:
        print("✅ 완벽한 방어! 모든 SQL Injection 공격이 차단되었습니다")
    elif blocked_count >= attack_count * 0.8:
        print("🛡️  우수한 방어! 대부분의 공격이 차단되었습니다")
    else:
        print("⚠️  방어 강화 필요! 일부 공격이 성공했습니다")

    print()
    print("🔑 적용된 보안 기법:")
    print("  ✓ Prepared Statements - SQL과 데이터 분리")
    print("  ✓ Input Validation - 입력값 형식 검증")
    print("  ✓ 파라미터화된 쿼리 - 동적 쿼리 방지")
    print("  ✓ 에러 메시지 최소화 - DB 구조 정보 노출 방지")
    print("  ✓ 화이트리스트 검증 - 허용된 문자만 사용")
    print()
    print("💡 추가 권장 사항:")
    print("  • ORM 프레임워크 사용 (SQLAlchemy, Django ORM)")
    print("  • WAF(Web Application Firewall) 적용")
    print("  • 정기적인 보안 감사 및 취약점 스캔")
    print("  • 데이터베이스 접근 권한 최소화")
    print("  • 보안 로깅 및 모니터링 시스템 구축")
    print("=" * 70)

if __name__ == "__main__":
    asyncio.run(run_defense_test())
