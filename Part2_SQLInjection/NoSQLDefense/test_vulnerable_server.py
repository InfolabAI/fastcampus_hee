#!/usr/bin/env python3
"""
===========================================
취약한 서버 테스트 클라이언트
===========================================

강의 목적:
이 파일은 취약한 SQL 서버의 '정상적인' 기능을 테스트합니다.
공격이 아닌, 일반 사용자가 의도한 대로 서버를 사용하는 시나리오를 검증합니다.

학습 포인트:
1. MCP 클라이언트 작성 방법
2. 서버와의 통신 방식 이해
3. 정상 동작 vs 공격의 차이점 파악
"""

# ===========================================
# 필요한 라이브러리 임포트
# ===========================================

import asyncio  # 비동기 프로그래밍을 위한 표준 라이브러리
import json     # JSON 데이터 처리
# MCP (Model Context Protocol) 클라이언트 라이브러리
# ClientSession: MCP 서버와의 세션 관리
# StdioServerParameters: stdio를 통한 서버 연결 설정
# stdio_client: stdio 기반 MCP 클라이언트
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


# ===========================================
# 메인 테스트 함수
# ===========================================

async def test_vulnerable_server():
    """
    취약한 서버의 정상 동작을 테스트하는 함수

    테스트 시나리오:
    1. 정상 로그인 - 올바른 사용자명과 비밀번호로 로그인
    2. 사용자 검색 - 특정 사용자 이름으로 검색
    3. 사용자 정보 조회 - ID로 사용자 정보 가져오기
    4. 이메일 업데이트 - 사용자 이메일 주소 변경
    5. 업데이트 확인 - 변경사항이 제대로 저장되었는지 확인

    모든 테스트는 '정상적인' 입력만 사용합니다.
    공격 시도는 attack_simulation.py에서 수행됩니다.
    """

    # 테스트 시작 헤더 출력
    print("=" * 70)
    print("취약한 SQL 서버 - 정상 동작 테스트")
    print("=" * 70)

    # ===========================================
    # 서버 실행 파일 경로 설정
    # ===========================================
    # 현재 스크립트와 같은 디렉토리에서 서버 파일 찾기
    import os
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # ===========================================
    # MCP 서버 파라미터 설정
    # ===========================================
    # stdio(표준 입출력)를 통해 서버와 통신
    # command: 실행할 명령어 (Python 3)
    # args: 명령어 인자 (서버 스크립트 경로)
    # env: 환경 변수 (None = 현재 환경 사용)
    server_params = StdioServerParameters(
        command="python3",
        args=[os.path.join(script_dir, "vulnerable_server.py")],
        env=None
    )

    # ===========================================
    # MCP 클라이언트 세션 시작
    # ===========================================
    # async with 구문을 사용하여 리소스를 자동으로 정리합니다
    # stdio_client(): 서버 프로세스를 시작하고 stdio 스트림 반환
    # read: 서버로부터 데이터를 읽는 스트림
    # write: 서버에 데이터를 쓰는 스트림
    async with stdio_client(server_params) as (read, write):
        # ClientSession: MCP 프로토콜 레벨의 통신 관리
        async with ClientSession(read, write) as session:
            # ===========================================
            # 세션 초기화
            # ===========================================
            # MCP 프로토콜 핸드셰이크 수행
            # 서버와 클라이언트 간 capabilities 교환
            await session.initialize()

            # ===========================================
            # 테스트 1: 정상 로그인
            # ===========================================
            print("\n테스트 1: 정상 로그인")
            print("-" * 70)

            # call_tool(): 서버의 도구(tool) 실행 요청
            # 도구 이름: "login"
            # 인자: username과 password
            #
            # 정상 입력 예시:
            # username = "alice" (존재하는 사용자)
            # password = "alice123" (올바른 비밀번호)
            result = await session.call_tool("login", arguments={
                "username": "alice",
                "password": "alice123"
            })

            # result.content: 서버 응답 내용
            # result.content[0]: 첫 번째 콘텐츠 항목
            # result.content[0].text: 텍스트 형식의 응답
            print(f"결과: {result.content[0].text}")

            # ===========================================
            # 테스트 2: 사용자 검색
            # ===========================================
            print("\n테스트 2: 사용자 검색")
            print("-" * 70)

            # search_user 도구 호출
            # LIKE 쿼리를 사용하여 부분 일치 검색
            #
            # 정상 입력 예시:
            # username = "bob" (검색할 사용자 이름)
            # 서버는 "bob"을 포함하는 모든 사용자를 반환
            result = await session.call_tool("search_user", arguments={
                "username": "bob"
            })
            print(f"결과: {result.content[0].text}")

            # ===========================================
            # 테스트 3: 사용자 정보 조회
            # ===========================================
            print("\n테스트 3: 사용자 ID로 조회")
            print("-" * 70)

            # get_user_info 도구 호출
            # ID를 사용하여 특정 사용자 정보 가져오기
            #
            # 정상 입력 예시:
            # user_id = "2" (alice의 ID)
            # 참고: ID는 숫자지만 문자열로 전달됨
            result = await session.call_tool("get_user_info", arguments={
                "user_id": "2"
            })
            print(f"결과: {result.content[0].text}")

            # ===========================================
            # 테스트 4: 이메일 업데이트
            # ===========================================
            print("\n테스트 4: 이메일 업데이트")
            print("-" * 70)

            # update_email 도구 호출
            # 사용자의 이메일 주소를 새로운 값으로 변경
            #
            # 정상 입력 예시:
            # username = "alice" (대상 사용자)
            # new_email = "alice.new@example.com" (새 이메일)
            result = await session.call_tool("update_email", arguments={
                "username": "alice",
                "new_email": "alice.new@example.com"
            })
            print(f"결과: {result.content[0].text}")

            # ===========================================
            # 테스트 5: 업데이트 확인
            # ===========================================
            print("\n테스트 5: 업데이트 확인")
            print("-" * 70)

            # 이메일이 제대로 변경되었는지 확인
            # search_user로 alice를 다시 검색하여 새 이메일 확인
            result = await session.call_tool("search_user", arguments={
                "username": "alice"
            })
            print(f"결과: {result.content[0].text}")

    # ===========================================
    # 테스트 완료
    # ===========================================
    print("\n" + "=" * 70)
    print("모든 정상 테스트 완료")
    print("=" * 70)
    print("\n다음 단계:")
    print("- attack_simulation.py를 실행하여 SQL Injection 공격 시뮬레이션")
    print("- 정상 동작과 공격의 차이점을 비교 분석")


# ===========================================
# 프로그램 진입점
# ===========================================

if __name__ == "__main__":
    """
    스크립트가 직접 실행될 때만 테스트를 실행

    실행 방법:
    python3 test_vulnerable_server.py

    또는 Docker 환경:
    make shell python3 Part2_SQLInjection/NoSQLDefense/test_vulnerable_server.py
    """
    asyncio.run(test_vulnerable_server())


# ===========================================
# 학습 정리
# ===========================================
"""
이 파일에서 배운 내용:

1. MCP 클라이언트 구조
   - StdioServerParameters: 서버 실행 설정
   - stdio_client: 서버 프로세스 시작
   - ClientSession: 세션 관리
   - call_tool(): 도구 호출

2. 정상적인 사용 패턴
   - 유효한 사용자 이름과 비밀번호
   - 일반적인 검색어
   - 올바른 형식의 데이터

3. 테스트 시나리오 설계
   - 단계별 기능 테스트
   - 데이터 변경 후 확인
   - 명확한 입력과 기대 결과

4. 다음 학습 단계
   - attack_simulation.py에서 같은 도구를 악의적으로 사용
   - 정상 입력 vs 공격 입력의 차이 이해
   - SQL Injection 공격이 성공하는 원리 파악
"""
