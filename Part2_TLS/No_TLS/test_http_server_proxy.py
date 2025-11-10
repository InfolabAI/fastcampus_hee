#!/usr/bin/env python3
"""
===========================================
HTTP 프록시 서버 테스트 클라이언트
===========================================

강의 목적:
이 파일은 http_server_proxy.py를 통해 원격 HTTP 서버의 도구들을
테스트하는 클라이언트입니다.

학습 포인트:
1. FastMCP Client 사용법
2. StdioTransport를 통한 프록시 연결
3. 프록시를 통한 간접 통신의 투명성
4. MCP 도구 호출 패턴
5. 정상 동작 vs 보안 문제 구분

통신 흐름:
test_http_server_proxy.py (Client)
    |
    v (STDIO)
http_server_proxy.py (Proxy)
    |
    v (HTTP - 평문!)
http_server.py (Server)

중요:
이 테스트는 정상 동작을 확인하지만,
HTTP를 사용하므로 모든 데이터가 평문으로 전송됩니다!

비교:
- 직접 연결: Client -> Server (단일 홉)
- 프록시 경유: Client -> Proxy -> Server (2홉)
- 결과는 동일하지만 보안 위험은 증가
"""

# ===========================================
# 필요한 라이브러리 임포트
# ===========================================

import asyncio  # 비동기 프로그래밍
# FastMCP 클라이언트 라이브러리
from fastmcp import Client
from fastmcp.client.transports import StdioTransport

# ===========================================
# 메인 테스트 함수
# ===========================================

async def test_http_server_proxy():
    """
    HTTP 프록시를 통한 서버 테스트

    테스트 시나리오:
    1. 프록시에 STDIO로 연결
    2. 사용 가능한 도구 목록 조회
    3. add 도구 테스트 (2회)
    4. create_greeting 도구 테스트 (2회)
    5. 프록시 동작 특성 확인

    주의:
    - http_server.py가 먼저 실행되어 있어야 함
    - http_server_proxy.py는 자동으로 시작됨
    - 모든 데이터가 HTTP로 평문 전송됨
    """

    # ===========================================
    # StdioTransport 설정
    # ===========================================

    # StdioTransport: 표준 입출력(stdin/stdout)으로 프로세스와 통신
    #
    # 동작 방식:
    # 1. command와 args로 프로세스 시작
    # 2. stdin으로 요청 전송
    # 3. stdout으로 응답 수신
    #
    # 여기서는 http_server_proxy.py를 subprocess로 실행
    # 이 프록시가 다시 HTTP로 http_server.py와 통신
    transport = StdioTransport(
        command="python",              # Python 인터프리터
        args=["http_server_proxy.py"]  # 실행할 프록시 스크립트
    )

    # ===========================================
    # FastMCP Client 생성
    # ===========================================

    # Client: MCP 프로토콜 클라이언트
    # - transport를 통해 서버(또는 프록시)와 통신
    # - MCP 프로토콜 메시지 직렬화/역직렬화
    # - 도구 호출, 리소스 조회 등 MCP 기능 제공
    client = Client(transport)

    # ===========================================
    # 테스트 실행
    # ===========================================

    try:
        # async with: 자동 리소스 정리
        # client가 연결을 열고 종료 시 자동으로 닫음
        async with client:
            print("=== HTTP Server Proxy 테스트 시작 ===\n")

            # ===========================================
            # 1. 도구 목록 조회
            # ===========================================

            # list_tools(): 서버에서 제공하는 모든 도구 목록 조회
            #
            # 통신 흐름:
            # 1. Client -> (STDIO) -> Proxy: list_tools 요청
            # 2. Proxy -> (HTTP) -> Server: GET /mcp/tools
            # 3. Server -> (HTTP) -> Proxy: 도구 목록 응답
            # 4. Proxy -> (STDIO) -> Client: 도구 목록 전달
            #
            # 보안 문제:
            # - 2-3 단계가 HTTP (평문)로 전송됨
            # - 도구 목록 자체는 민감하지 않지만, 구조 정보 노출
            tools = await client.list_tools()
            print("사용 가능한 도구:")
            for tool in tools:
                # 각 도구의 이름과 설명 출력
                # http_server.py에 정의된 @mcp.tool() 데코레이터가 붙은 함수들
                print(f"  - {tool.name}: {tool.description}")
            print()

            # ===========================================
            # 2. add 도구 테스트
            # ===========================================

            print("1. add 도구 테스트:")

            # 첫 번째 테스트: 작은 숫자
            print("   입력: a=5, b=3")

            # call_tool(): 특정 도구 호출
            # - 첫 번째 인자: 도구 이름
            # - 두 번째 인자: 도구 파라미터 (dict)
            #
            # 통신 흐름:
            # 1. Client -> Proxy (STDIO):
            #    {"jsonrpc": "2.0", "method": "tools/call",
            #     "params": {"name": "add", "arguments": {"a": 5, "b": 3}}}
            #
            # 2. Proxy -> Server (HTTP POST):
            #    POST http://127.0.0.1:8000/mcp/tool/add
            #    Body: {"a": 5, "b": 3}
            #    ↑ 평문 전송!
            #
            # 3. Server: 5 + 3 = 8 계산
            #
            # 4. Server -> Proxy (HTTP Response):
            #    {"result": 8}
            #    ↑ 평문 응답!
            #
            # 5. Proxy -> Client (STDIO):
            #    JSON-RPC 응답으로 변환하여 전달
            #
            # 보안 분석:
            # - 이 데이터는 민감하지 않음 (단순 계산)
            # - 하지만 HTTP 평문 전송으로 도청 가능
            # - 패턴 분석으로 사용자 행동 추적 가능
            result = await client.call_tool("add", {"a": 5, "b": 3})
            print(f"   결과: {result}")
            print()

            # 두 번째 테스트: 큰 숫자
            print("   입력: a=100, b=200")

            # 동일한 통신 흐름:
            # Client -> Proxy (STDIO) -> Server (HTTP) -> Proxy -> Client
            #
            # HTTP 요청:
            # POST http://127.0.0.1:8000/mcp/tool/add
            # Body: {"a": 100, "b": 200}
            #
            # 반복되는 패턴:
            # - 여러 요청을 관찰하면 사용 패턴 파악 가능
            # - 타이밍 분석으로 사용자 행동 추론 가능
            result = await client.call_tool("add", {"a": 100, "b": 200})
            print(f"   결과: {result}")
            print()

            # ===========================================
            # 3. create_greeting 도구 테스트
            # ===========================================

            print("2. create_greeting 도구 테스트:")

            # 첫 번째 테스트: 일반 이름
            print("   입력: name='Proxy User'")

            # 통신 흐름:
            # 1. Client -> Proxy (STDIO)
            # 2. Proxy -> Server (HTTP POST):
            #    POST http://127.0.0.1:8000/mcp/tool/create_greeting
            #    Body: {"name": "Proxy User"}
            #    ↑ 이름이 평문으로 전송!
            #
            # 3. Server: "Hello, Proxy User!" 생성
            # 4. Server -> Proxy: 응답 전송
            # 5. Proxy -> Client: 결과 전달
            #
            # 보안 문제:
            # - 사용자 이름이 평문으로 전송됨
            # - 개인정보보호법 위반 가능성
            # - 네트워크 스니핑으로 실명 파악 가능
            # - 반복되는 이름으로 사용자 식별 가능
            result = await client.call_tool("create_greeting", {"name": "Proxy User"})
            print(f"   결과: {result}")
            print()

            # 두 번째 테스트: 다른 이름
            print("   입력: name='MCP Developer'")

            # HTTP 요청:
            # POST http://127.0.0.1:8000/mcp/tool/create_greeting
            # Body: {"name": "MCP Developer"}
            #
            # 보안 분석:
            # - 직업/역할 정보 노출
            # - 여러 요청을 종합하면 사용자 프로파일링 가능
            # - "Developer"라는 키워드로 타겟팅 공격 가능
            result = await client.call_tool("create_greeting", {"name": "MCP Developer"})
            print(f"   결과: {result}")
            print()

            # ===========================================
            # 4. 프록시 특성 설명
            # ===========================================

            print("3. 프록시 특징:")
            print("   - stdio 프로토콜로 Claude Code와 연결")
            print("   - HTTP 프로토콜로 백엔드 서버와 통신")
            print("   - JWT 인증이 없는 서버로 누구나 접근 가능")
            print()

            print("=== 테스트 완료 ===")

    # ===========================================
    # 에러 처리
    # ===========================================

    except Exception as e:
        # 예외 발생 시 원인 출력
        print(f"오류 발생: {e}")

        # 일반적인 원인:
        # 1. http_server.py가 실행되지 않음
        # 2. 포트 8000이 이미 사용 중
        # 3. http_server_proxy.py 파일을 찾을 수 없음
        # 4. Python 버전 호환성 문제
        print("HTTP 서버가 실행 중인지 확인하세요.")
        print("실행 명령: python http_server.py")

# ===========================================
# 프로그램 진입점
# ===========================================

if __name__ == "__main__":
    """
    스크립트가 직접 실행될 때만 테스트 실행

    실행 방법:
    1. 먼저 HTTP 서버 시작:
       Terminal 1: python3 http_server.py

    2. 테스트 실행:
       Terminal 2: python3 test_http_server_proxy.py

    또는 Docker 환경:
    make shell python3 Part2_SSL/No_TLS/test_http_server_proxy.py

    기대 결과:
    - 모든 도구가 정상 동작
    - 프록시 레이어가 투명하게 작동
    - 결과는 직접 연결과 동일
    - 하지만 HTTP 트래픽이 평문으로 전송됨!

    확인 사항:
    - http_server.py가 실행 중이어야 함
    - 포트 8000이 사용 가능해야 함
    - Python 3.8 이상 필요
    """
    # 비동기 함수 실행
    asyncio.run(test_http_server_proxy())


# ===========================================
# 학습 정리
# ===========================================
"""
이 파일에서 배운 내용:

1. FastMCP Client 사용법

   Client 생성:
   - Client(transport): transport를 통해 서버 연결
   - async with 구문으로 자동 리소스 정리

   주요 메서드:
   - list_tools(): 사용 가능한 도구 목록 조회
   - call_tool(name, args): 특정 도구 호출
   - list_resources(): 리소스 목록 조회 (이 예제에서는 미사용)

   비동기 패턴:
   - async/await 사용
   - asyncio.run()으로 실행

2. StdioTransport 설정

   StdioTransport 생성:
   transport = StdioTransport(
       command="python",           # 실행할 명령어
       args=["script.py"]          # 명령어 인자
   )

   동작 원리:
   - subprocess로 프로세스 시작
   - stdin/stdout으로 통신
   - JSON-RPC 메시지 교환

   장점:
   - 간단한 설정
   - 프로세스 격리
   - 로컬 통신에 적합

   단점:
   - 원격 서버 직접 연결 불가
   - 프로세스 오버헤드

3. 프록시를 통한 간접 통신

   3단계 통신 구조:

   [Client] <--(STDIO)--> [Proxy] <--(HTTP)--> [Server]

   Client (test_http_server_proxy.py):
   - FastMCP Client 사용
   - StdioTransport로 프록시 연결
   - 프록시가 있는지 모름 (투명)

   Proxy (http_server_proxy.py):
   - STDIO로 클라이언트와 통신
   - HTTP로 서버와 통신
   - Transport 변환 수행

   Server (http_server.py):
   - FastAPI로 HTTP 서비스 제공
   - MCP 도구 구현
   - 클라이언트/프록시 구분 안 함

4. 통신 흐름 상세 분석

   add(5, 3) 호출 시:

   1단계: Client -> Proxy (STDIO)
      메시지:
      {
        "jsonrpc": "2.0",
        "method": "tools/call",
        "params": {
          "name": "add",
          "arguments": {"a": 5, "b": 3}
        },
        "id": 1
      }

      - stdin으로 전송
      - JSON-RPC 2.0 형식
      - MCP 프로토콜 준수

   2단계: Proxy -> Server (HTTP)
      요청:
      POST http://127.0.0.1:8000/mcp/tool/add
      Content-Type: application/json

      Body:
      {"a": 5, "b": 3}

      - 평문 전송!
      - 네트워크 스니핑 가능

   3단계: Server 처리
      - add() 함수 실행
      - 결과: 5 + 3 = 8

   4단계: Server -> Proxy (HTTP Response)
      응답:
      HTTP/1.1 200 OK
      Content-Type: application/json

      Body:
      {"result": 8}

      - 평문 응답!

   5단계: Proxy -> Client (STDIO)
      메시지:
      {
        "jsonrpc": "2.0",
        "result": 8,
        "id": 1
      }

      - stdout으로 전송
      - Client가 결과 수신

5. 프록시의 투명성

   클라이언트 관점:
   - 프록시 존재를 모름
   - 직접 연결과 동일한 API 사용
   - 결과도 동일

   투명성의 장점:
   - 클라이언트 코드 변경 불필요
   - 서버 위치 변경 자유로움
   - 아키텍처 변경 용이

   투명성의 단점:
   - 보안 문제 인식 어려움
   - 성능 오버헤드 숨겨짐
   - 디버깅 복잡도 증가

6. MCP 도구 호출 패턴

   기본 패턴:
   result = await client.call_tool(tool_name, arguments)

   예시들:

   # 숫자 계산
   result = await client.call_tool("add", {"a": 5, "b": 3})

   # 문자열 처리
   result = await client.call_tool("create_greeting", {"name": "Alice"})

   # 복잡한 객체
   result = await client.call_tool("process_data", {
       "data": [1, 2, 3],
       "options": {"sort": True}
   })

   공통점:
   - 비동기 호출 (await)
   - 도구 이름은 문자열
   - 인자는 dict
   - 결과는 도구마다 다름

7. 보안 문제 분석

   HTTP 평문 전송:
   - 모든 요청/응답이 평문
   - 네트워크 스니핑으로 도청 가능
   - 데이터 변조 가능

   프록시 레이어의 위험:
   - 홉(hop)이 늘어날수록 위험 증가
   - 각 홉에서 도청 가능
   - 프록시 서버 자체가 공격 대상

   민감한 데이터:
   - 이 테스트: 이름, 숫자 (상대적으로 덜 민감)
   - http_server.py의 다른 도구:
     * login(): 비밀번호 평문 전송
     * get_api_key(): API 키 평문 전송
     * process_payment(): 신용카드 평문 전송!

8. 테스트 vs 실제 사용

   이 테스트 파일:
   - 정상 동작 확인
   - 기능 검증
   - 성능 측정

   실제 공격 (attack_simulation.py):
   - 네트워크 스니핑
   - 데이터 도청
   - 패킷 분석

   차이점:
   - 테스트: 기능 중심
   - 공격: 보안 취약점 중심
   - 둘 다 중요!

9. 에러 처리

   일반적인 에러:

   1. ConnectionError:
      - 원인: http_server.py 미실행
      - 해결: 서버 먼저 시작

   2. FileNotFoundError:
      - 원인: http_server_proxy.py 찾을 수 없음
      - 해결: 파일 경로 확인

   3. PermissionError:
      - 원인: 포트 사용 권한 없음
      - 해결: sudo 또는 다른 포트 사용

   4. TimeoutError:
      - 원인: 서버 응답 지연
      - 해결: 타임아웃 증가 또는 서버 확인

10. 다음 학습 단계

    - attack_simulation.py 실행
      * 프록시를 통한 HTTP 트래픽 스니핑
      * Wireshark로 패킷 캡처
      * 평문 데이터 추출 실습
      * add, create_greeting 호출 도청

    - 보안 서버와 비교
      * secure_http_server_proxy.py 학습
      * HTTPS 사용으로 암호화
      * 동일한 테스트 실행
      * 암호화된 트래픽 확인

    - 프록시 패턴의 장단점 이해
      * 언제 프록시를 사용해야 하는가
      * 보안을 위한 프록시 설정
      * 성능과 보안의 트레이드오프

핵심 메시지:
프록시는 편리하지만 보안 레이어를 추가하지 않으면
오히려 공격 표면(attack surface)이 늘어납니다!
"""