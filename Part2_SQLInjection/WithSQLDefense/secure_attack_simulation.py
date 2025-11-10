#!/usr/bin/env python3
"""
===========================================
보안 서버 SQL Injection 공격 방어 테스트
===========================================

강의 목적:
이 파일은 attack_simulation.py와 동일한 공격을 보안 서버에 시도합니다.
모든 공격이 차단되는 것을 확인하여 방어 메커니즘의 효과를 입증합니다.

학습 포인트:
1. 같은 공격, 다른 결과 (성공 → 차단)
2. 각 방어 계층이 어떻게 작동하는지
3. Prepared Statement + 입력 검증의 효과
4. 공격 차단 메시지 분석

비교 학습:
- attack_simulation.py: 모든 공격 성공 (vulnerable_server)
- secure_attack_simulation.py: 모든 공격 차단 (secure_server)
- 같은 공격 페이로드 사용
- 다른 결과를 통해 방어 효과 확인
"""

# ===========================================
# 필요한 라이브러리 임포트
# ===========================================

import asyncio
import json
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# ===========================================
# 메인 방어 테스트 함수
# ===========================================

async def run_defense_test():
    """
    SQL Injection 공격 방어 테스트

    목적:
    - attack_simulation.py와 동일한 공격 시도
    - 보안 서버(secure_server.py)가 모든 공격을 차단하는지 확인
    - 방어 메커니즘의 효과 측정

    테스트 항목:
    1. 인증 우회 (OR '1'='1)
    2. UNION SELECT 데이터 추출
    3. 숫자 필드 Injection
    4. UPDATE Injection
    5. SQL 주석 우회
    6. Stacked Queries
    7. 특수문자 삽입
    8. Blind SQL Injection
    """

    print("=" * 70)
    print("🛡️  SQL INJECTION 방어 테스트")
    print("=" * 70)
    print("✅ 모든 공격이 차단되는지 확인합니다")
    print("=" * 70)

    # 서버 파일 경로
    import os
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # secure_server.py 실행
    server_params = StdioServerParameters(
        command="python3",
        args=[os.path.join(script_dir, "secure_server.py")],
        env=None
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            # 공격 통계
            attack_count = 0      # 시도한 공격 수
            blocked_count = 0     # 차단된 공격 수

            # ===========================================
            # 방어 테스트 1: 인증 우회 시도
            # ===========================================
            print("\n🎯 방어 테스트 1: 인증 우회 시도")
            print("-" * 70)
            print("📝 공격 시도: ' OR '1'='1")
            attack_count += 1

            # 공격 페이로드: "admin' OR '1'='1"
            # attack_simulation.py에서는 성공했지만...
            #
            # 보안 서버의 방어:
            # 1. validate_username("admin' OR '1'='1") 호출
            # 2. 정규표현식 검증: ^[a-zA-Z0-9_]+$
            # 3. 작은따옴표(')는 패턴에 없음
            # 4. 검증 실패 → "잘못된 사용자 이름 형식" 반환
            # 5. SQL 실행 전에 차단!
            result = await session.call_tool("login", arguments={
                "username": "admin' OR '1'='1",
                "password": "anything"
            })
            response = result.content[0].text

            # 차단 여부 확인
            if "❌" in response or "잘못된" in response:
                print(f"✅ 차단 성공!\n{response}")
                blocked_count += 1
            else:
                print(f"❌ 차단 실패!\n{response}")

            # ===========================================
            # 방어 테스트 2: UNION SELECT 시도
            # ===========================================
            print("\n🎯 방어 테스트 2: UNION SELECT 데이터 추출 시도")
            print("-" * 70)
            print("📝 공격 시도: UNION SELECT")
            attack_count += 1

            # 공격: "' UNION SELECT id, username, password, credit_card FROM users--"
            # 방어: validate_username이 UNION, SELECT, 공백, -를 모두 차단
            result = await session.call_tool("search_user", arguments={
                "username": "' UNION SELECT id, username, password, credit_card FROM users--"
            })
            response = result.content[0].text

            if "❌" in response or "잘못된" in response:
                print(f"✅ 차단 성공!\n{response}")
                blocked_count += 1
            else:
                print(f"❌ 차단 실패!\n{response}")

            # ===========================================
            # 방어 테스트 3: 숫자 필드 SQL Injection
            # ===========================================
            print("\n🎯 방어 테스트 3: 숫자 필드 SQL Injection 시도")
            print("-" * 70)
            print("📝 공격 시도: UNION SELECT in numeric field")
            attack_count += 1

            # 공격: "1 UNION SELECT ..."
            # 방어: validate_user_id()에서 int() 변환 실패로 차단
            result = await session.call_tool("get_user_info", arguments={
                "user_id": "1 UNION SELECT id, username, password, credit_card FROM users"
            })
            response = result.content[0].text

            if "❌" in response or "잘못된" in response:
                print(f"✅ 차단 성공!\n{response}")
                blocked_count += 1
            else:
                print(f"❌ 차단 실패!\n{response}")

            # ===========================================
            # 방어 테스트 4: UPDATE Injection
            # ===========================================
            print("\n🎯 방어 테스트 4: UPDATE Injection 시도")
            print("-" * 70)
            print("📝 공격 시도: SQL Injection in UPDATE")
            attack_count += 1

            # 공격: "hacked@evil.com' WHERE '1'='1"
            # 방어: validate_email()이 ' 문자를 차단
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

            # ===========================================
            # 방어 테스트 5: SQL 주석 우회
            # ===========================================
            print("\n🎯 방어 테스트 5: SQL 주석(--) 우회 시도")
            print("-" * 70)
            print("📝 공격 시도: admin'--")
            attack_count += 1

            # 공격: "admin'--" (주석으로 뒤 조건 무효화)
            # 방어: ' 와 - 문자가 정규표현식에서 차단됨
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

            # ===========================================
            # 방어 테스트 6: Stacked Queries
            # ===========================================
            print("\n🎯 방어 테스트 6: Stacked Queries 시도")
            print("-" * 70)
            print("📝 공격 시도: '; DROP TABLE users--")
            attack_count += 1

            # 공격: "alice'; DROP TABLE users--"
            # 방어: ', ;, - 모두 차단됨
            result = await session.call_tool("search_user", arguments={
                "username": "alice'; DROP TABLE users--"
            })
            response = result.content[0].text

            if "❌" in response or "잘못된" in response:
                print(f"✅ 차단 성공!\n{response}")
                blocked_count += 1
            else:
                print(f"❌ 차단 실패!\n{response}")

            # ===========================================
            # 방어 테스트 7: 특수문자 삽입
            # ===========================================
            print("\n🎯 방어 테스트 7: 특수문자 삽입 시도")
            print("-" * 70)
            print("📝 공격 시도: <script>alert('XSS')</script>")
            attack_count += 1

            # 공격: XSS 시도 (SQL Injection과는 다른 공격)
            # 방어: <, >, ' 등 특수문자 차단
            result = await session.call_tool("search_user", arguments={
                "username": "<script>alert('XSS')</script>"
            })
            response = result.content[0].text

            if "❌" in response or "잘못된" in response:
                print(f"✅ 차단 성공!\n{response}")
                blocked_count += 1
            else:
                print(f"⚠️  입력 허용됨 (XSS 방어는 별도 필요)\n{response}")

            # ===========================================
            # 방어 테스트 8: Blind SQL Injection
            # ===========================================
            print("\n🎯 방어 테스트 8: Blind SQL Injection 시도")
            print("-" * 70)
            print("📝 공격 시도: Time-based blind injection")
            attack_count += 1

            # 공격: "' OR SLEEP(5)--" (시간 기반 정보 추출)
            # 방어: ', (, ) 모두 차단됨
            result = await session.call_tool("search_user", arguments={
                "username": "' OR SLEEP(5)--"
            })
            response = result.content[0].text

            if "❌" in response or "잘못된" in response:
                print(f"✅ 차단 성공!\n{response}")
                blocked_count += 1
            else:
                print(f"❌ 차단 실패!\n{response}")

            # ===========================================
            # 보너스: 정상 동작 확인
            # ===========================================
            print("\n🎯 보너스 테스트: 정상 사용자 접근")
            print("-" * 70)

            # 중요한 확인: 보안 기능이 정상 사용자를 방해하지 않는지
            # "alice", "alice123" 같은 정상 입력은 허용되어야 함
            result = await session.call_tool("login", arguments={
                "username": "alice",
                "password": "alice123"
            })
            response = result.content[0].text

            if "✅" in response or "성공" in response:
                print(f"✅ 정상 접근 허용\n{response}")
            else:
                print(f"⚠️  정상 접근 차단됨\n{response}")

            # ===========================================
            # 데이터베이스 무결성 확인
            # ===========================================
            print("\n🎯 데이터베이스 무결성 확인")
            print("-" * 70)

            # DROP TABLE 같은 공격이 실제로 차단되었는지 확인
            # 데이터베이스가 여전히 정상 동작하면 공격이 차단된 것
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

# ===========================================
# 프로그램 진입점
# ===========================================

if __name__ == "__main__":
    """
    스크립트가 직접 실행될 때만 방어 테스트 실행

    실행 방법:
    python3 secure_attack_simulation.py

    또는 Docker 환경:
    make shell python3 Part2_SQLInjection/WithSQLDefense/secure_attack_simulation.py

    기대 결과:
    - 모든 SQL Injection 공격이 차단됨
    - 차단 성공률 100% 달성
    - 정상 사용자는 접근 가능
    - 데이터베이스 무결성 유지
    """
    asyncio.run(run_defense_test())


# ===========================================
# 학습 정리
# ===========================================
"""
이 파일에서 배운 내용:

1. 방어 메커니즘의 효과
   - 입력 검증이 대부분의 공격을 1차 차단
   - Prepared Statement가 우회 시도를 2차 차단
   - 다층 방어 전략의 중요성

2. 공격과 방어의 비교
   attack_simulation.py          secure_attack_simulation.py
   ----------------------------------------
   모든 공격 성공       →       모든 공격 차단
   데이터 유출         →       입력 검증에서 차단
   권한 상승          →       Prepared Statement로 차단
   테이블 삭제         →       특수문자 차단

3. 방어 계층별 역할
   1단계: 입력 검증
   - validate_username(): ', ", -, %, (, ), ; 등 차단
   - validate_email(): 이메일 형식만 허용
   - validate_user_id(): 정수로 변환 가능한 값만 허용

   2단계: Prepared Statement
   - 쿼리 구조와 데이터 분리
   - SQL 구문 해석 차단
   - 자동 이스케이프 처리

   3단계: 에러 최소화
   - 상세 정보 숨김
   - 공격자의 정보 수집 차단

4. 보안과 사용성의 균형
   - 공격은 차단하지만 정상 사용은 허용
   - "alice", "bob" 같은 정상 입력은 통과
   - "admin' OR '1'='1" 같은 공격은 차단

5. 실전 적용 지침
   - NEVER: f-string으로 SQL 쿼리 생성
   - ALWAYS: Parameterized Query 사용
   - MUST: 모든 입력 검증
   - SHOULD: 화이트리스트 방식 사용

핵심 교훈:
SQL Injection은 완전히 방어 가능한 취약점입니다.
Prepared Statement + 입력 검증만 제대로 적용하면
거의 모든 SQL Injection 공격을 차단할 수 있습니다!

비교 분석:
- vulnerable_server.py vs secure_server.py
- attack_simulation.py vs secure_attack_simulation.py
이 4개 파일을 함께 비교 학습하세요!
"""
