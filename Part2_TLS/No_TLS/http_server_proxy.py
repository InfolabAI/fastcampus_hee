#!/usr/bin/env python3
"""
===========================================
HTTP MCP 프록시 서버
===========================================

강의 목적:
이 파일은 FastMCP의 프록시 기능을 사용하여 원격 HTTP MCP 서버에
연결하는 프록시 레이어를 구현합니다.

학습 포인트:
1. MCP 프록시 패턴의 이해
2. STDIO transport와 HTTP transport의 브릿지
3. 분산 MCP 아키텍처
4. 프록시를 사용하는 이유
5. 프록시의 보안 문제

아키텍처:
Claude Code <--(STDIO)--> http_server_proxy.py <--(HTTP)--> http_server.py
    |                           |                                 |
  클라이언트               프록시 레이어                     실제 서버

중요:
이 프록시도 HTTP를 사용하므로 http_server.py와 동일한 보안 문제가 있습니다!
프록시와 서버 간의 통신도 암호화되지 않습니다.

비교:
- http_server.py: FastAPI 기반 HTTP MCP 서버
- http_server_proxy.py: FastMCP 프록시 (이 파일)
- secure_http_server_proxy.py: HTTPS를 사용하는 안전한 프록시
"""

# ===========================================
# 필요한 라이브러리 임포트
# ===========================================

from fastmcp import FastMCP

# ===========================================
# MCP 프록시 생성
# ===========================================

# FastMCP.as_proxy() 메서드를 사용하여 원격 HTTP 서버에 대한 프록시 생성
#
# 프록시가 하는 일:
# 1. STDIO transport로 클라이언트(Claude Code)와 통신
# 2. HTTP transport로 실제 MCP 서버(http_server.py)와 통신
# 3. 양방향 메시지 중계
#
# 프록시를 사용하는 이유:
# 1. 클라이언트는 STDIO로만 통신하고 싶을 때
# 2. 실제 서버는 HTTP로 서비스를 제공할 때
# 3. 두 transport 간의 브릿지가 필요할 때
# 4. 여러 클라이언트가 하나의 HTTP 서버를 공유할 때
#
# 보안 문제:
# - 이 프록시는 HTTP를 사용합니다
# - 프록시 <-> 서버 간 통신이 암호화되지 않습니다
# - 네트워크 스니핑으로 데이터 도청 가능
# - http_server.py와 동일한 보안 취약점 존재
#
# 전제 조건:
# http_server.py가 http://127.0.0.1:8000/mcp 에서 이미 실행 중이어야 합니다.
proxy = FastMCP.as_proxy(
    "http://127.0.0.1:8000/mcp",  # 원격 HTTP MCP 서버의 URL
    name="HTTP Server Proxy"       # 프록시 이름 (디버깅/로깅용)
)

# ===========================================
# 프로그램 진입점
# ===========================================

if __name__ == "__main__":
    """
    프록시 서버 실행

    실행 방법:
    1. 먼저 http_server.py를 실행:
       python3 http_server.py

    2. 그 다음 이 프록시를 실행:
       python3 http_server_proxy.py

    또는 Docker 환경:
    make shell python3 Part2_SSL/No_TLS/http_server_proxy.py

    동작 방식:
    1. proxy.run()은 기본적으로 STDIO transport로 실행
    2. 클라이언트(Claude Code)가 STDIO로 이 프록시에 연결
    3. 프록시가 요청을 HTTP로 변환하여 http_server.py에 전달
    4. http_server.py의 응답을 다시 STDIO로 변환하여 클라이언트에 반환

    통신 흐름 예시:

    클라이언트 요청:
    Claude Code -> (STDIO) -> http_server_proxy.py

    프록시 중계:
    http_server_proxy.py -> (HTTP POST) -> http://127.0.0.1:8000/mcp/tool/login
    Body: {"username": "admin", "password": "admin123"}
    ↑ 이 데이터가 평문으로 전송됨!

    서버 응답:
    http_server.py -> (HTTP Response) -> http_server_proxy.py

    클라이언트 응답:
    http_server_proxy.py -> (STDIO) -> Claude Code

    보안 문제:
    - 프록시와 서버 간의 HTTP 통신이 암호화되지 않음
    - 로컬 네트워크(127.0.0.1)라도 위험할 수 있음
    - 특히 컨테이너/가상머신 환경에서는 더욱 위험
    """
    # STDIO transport로 실행
    # 클라이언트는 stdin/stdout으로 이 프록시와 통신
    # 프록시는 HTTP로 실제 서버와 통신
    proxy.run()


# ===========================================
# 학습 정리
# ===========================================
"""
이 파일에서 배운 내용:

1. MCP 프록시 패턴
   - FastMCP.as_proxy(): 원격 MCP 서버에 대한 프록시 생성
   - Transport 변환: STDIO <-> HTTP
   - 양방향 메시지 중계
   - 클라이언트와 서버 사이의 브릿지 역할

2. 프록시를 사용하는 이유
   - Transport 변환
     * 클라이언트: STDIO만 지원
     * 서버: HTTP로 서비스 제공
     * 프록시: 두 transport 간 브릿지

   - 분산 아키텍처
     * 여러 클라이언트가 하나의 HTTP 서버 공유
     * 서버를 별도 머신에서 실행 가능
     * 부하 분산 및 스케일링

   - 네트워크 레이어 추가
     * 로컬 STDIO -> 원격 HTTP
     * 서버를 다른 위치에 배치 가능

3. 통신 흐름 상세 분석

   클라이언트 -> 프록시 (STDIO):
   - 표준 입력(stdin)으로 JSON-RPC 메시지 전송
   - MCP 프로토콜 메시지
   - 예: {"jsonrpc": "2.0", "method": "tools/call", ...}

   프록시 -> 서버 (HTTP):
   - HTTP POST 요청으로 변환
   - URL: http://127.0.0.1:8000/mcp/tool/login
   - Body: {"username": "admin", "password": "admin123"}
   - 평문 전송! (암호화 없음)

   서버 -> 프록시 (HTTP Response):
   - HTTP 200 OK
   - Body: {"result": {"success": true, ...}}
   - 평문 응답!

   프록시 -> 클라이언트 (STDIO):
   - JSON-RPC 응답으로 변환
   - 표준 출력(stdout)으로 전송

4. 프록시의 보안 문제

   문제점:
   - 프록시와 서버 간 통신이 HTTP (평문)
   - 네트워크 스니핑으로 데이터 도청 가능
   - 로컬호스트(127.0.0.1)라도 완전히 안전하지 않음

   왜 로컬호스트도 위험한가:
   - 같은 머신의 다른 프로세스가 스니핑 가능
   - 컨테이너 환경: 다른 컨테이너가 네트워크 모니터링
   - 가상머신 환경: 하이퍼바이저나 다른 VM이 접근 가능
   - 악성 소프트웨어가 로컬 트래픽 캡처

   공격 시나리오:
   1. 공격자가 같은 머신에 악성 프로그램 설치
   2. 악성 프로그램이 localhost 트래픽 모니터링
   3. HTTP 요청에서 비밀번호/API 키 추출
   4. 신용카드 정보 등 민감한 데이터 탈취

5. FastMCP 프록시 기능

   FastMCP.as_proxy() 메서드:
   - 첫 번째 인자: 원격 서버 URL
   - name: 프록시 이름 (선택사항, 디버깅용)
   - 반환값: FastMCP 프록시 객체

   proxy.run():
   - 기본값: STDIO transport
   - 클라이언트와의 통신 시작
   - 원격 서버로 요청 중계

   자동으로 처리되는 것:
   - MCP 프로토콜 핸드셰이크
   - Transport 변환 (STDIO <-> HTTP)
   - 에러 처리 및 재전송
   - 연결 관리

6. 분산 MCP 아키텍처

   단일 서버 아키텍처:
   Claude Code <--(STDIO)--> mcp_server.py

   프록시 아키텍처:
   Claude Code <--(STDIO)--> proxy.py <--(HTTP)--> remote_server.py

   장점:
   - 서버를 원격 머신에서 실행 가능
   - 여러 클라이언트가 하나의 서버 공유
   - 서버 업데이트 시 클라이언트 영향 없음
   - 부하 분산 가능

   단점:
   - 네트워크 레이턴시 증가
   - 보안 위험 증가 (HTTP 사용 시)
   - 추가 장애 지점 (프록시)

7. 실행 순서

   1단계: HTTP 서버 시작
      Terminal 1: python3 http_server.py
      - FastAPI 서버가 8000번 포트에서 대기

   2단계: 프록시 시작
      Terminal 2: python3 http_server_proxy.py
      - STDIO transport로 대기
      - HTTP 서버에 연결 준비

   3단계: 클라이언트 연결
      Claude Code가 STDIO로 프록시에 연결

   4단계: 통신 시작
      Claude Code -> Proxy -> HTTP Server

8. 다음 학습 단계

   - test_http_server_proxy.py 실행
     * 프록시를 통한 정상 동작 테스트
     * http_server.py 직접 호출 vs 프록시 경유 비교

   - attack_simulation.py 실행
     * 프록시를 통한 공격 시뮬레이션
     * HTTP 트래픽 스니핑 실습
     * 평문 전송의 위험성 확인

   - secure_http_server_proxy.py 학습
     * HTTPS를 사용하는 안전한 프록시
     * TLS 암호화 적용
     * HTTP vs HTTPS 프록시 비교

   - 보안 개선 방법 이해
     * HTTP -> HTTPS 전환
     * 인증서 관리
     * 종단간 암호화 (End-to-End Encryption)

핵심 메시지:
프록시는 편리한 아키텍처 패턴이지만,
HTTP를 사용하면 프록시 레이어에서도 보안 문제가 발생합니다!
프록시와 서버 간의 통신도 반드시 암호화해야 합니다.
"""