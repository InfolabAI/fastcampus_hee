#!/usr/bin/env python3
"""
===========================================
Secure HTTPS MCP 프록시 서버
===========================================

강의 목적:
이 파일은 STDIO 인터페이스를 통해 HTTPS MCP 서버에 안전하게 접속하는
프록시 서버를 구현합니다.

학습 포인트:
1. HTTPS 프록시 구현
2. STDIO 인터페이스 처리
3. TLS 컨텍스트 설정
4. 자체 서명 인증서 처리
5. 비동기 HTTP 클라이언트 (aiohttp)
6. MCP 요청 전달 메커니즘

아키텍처:
Client <--(STDIO)--> Secure Proxy <--(HTTPS)--> HTTPS Server
   |                      |                           |
 MCP 클라이언트      프록시 레이어              실제 MCP 서버
 JSON-RPC           STDIO<->HTTPS              TLS 암호화
                    변환 및 중계              도구 실행

프록시의 역할:
1. Transport 변환: STDIO <-> HTTPS
2. TLS 암호화 통신
3. 요청 전달 및 응답 중계
4. 에러 처리 및 복구
5. Health check 및 모니터링

HTTP vs HTTPS 프록시 비교:
- http_server_proxy.py (No_TLS):
  * HTTP로 통신
  * 데이터 평문 전송
  * 스니핑 가능
  * MITM 공격 취약

- secure_http_server_proxy.py (이 파일):
  * HTTPS로 통신
  * 데이터 암호화
  * 스니핑 불가
  * MITM 공격 방어

보안 주의사항:
- 자체 서명 인증서를 위해 verify=False 사용
- 프로덕션에서는 공인 인증서 사용
- TLS 컨텍스트 설정 중요

비교:
- http_server_proxy.py: HTTP 프록시
- secure_http_server_proxy.py: HTTPS 프록시 (이 파일)
"""

# ===========================================
# 필요한 라이브러리 임포트
# ===========================================

import asyncio       # 비동기 I/O
import json          # JSON 처리
import sys           # 시스템 인터페이스
import aiohttp       # 비동기 HTTP 클라이언트
import ssl           # TLS 지원
from pathlib import Path  # 파일 경로 처리

# ===========================================
# Secure HTTPS 프록시 클래스
# ===========================================

class SecureHttpServerProxy:
    """
    HTTPS MCP 프록시 서버

    목적: STDIO 인터페이스를 HTTPS MCP 서버에 연결

    동작 원리:
    1. 클라이언트로부터 STDIO로 MCP 요청 수신
    2. 요청을 JSON으로 파싱
    3. HTTPS로 실제 MCP 서버에 전달
    4. 서버 응답을 STDIO로 반환

    보안 특징:
    - HTTPS 통신으로 데이터 암호화
    - TLS 컨텍스트 설정
    - 자체 서명 인증서 지원
    - Health check 기능
    """

    def __init__(self, target_url="https://127.0.0.1:8443"):
        """
        프록시 초기화

        파라미터:
        - target_url: 대상 HTTPS 서버 URL

        URL 선택:
        - https://127.0.0.1:8443: 순수 FastMCP HTTPS 서버
        - https://127.0.0.1:8444: 하이브리드 FastAPI + FastMCP 서버

        초기화 항목:
        - target_url: 대상 서버 주소
        - session: aiohttp 세션 (None으로 시작)
        - mcp_session_id: MCP 세션 ID (향후 사용)
        - ssl_context: TLS 설정 (자체 서명 인증서용)
        """
        self.target_url = target_url
        self.session = None
        self.mcp_session_id = None

        # ===========================================
        # TLS 컨텍스트 설정
        # ===========================================

        # TLS 인증서 검증 비활성화 (자체 서명 인증서용)
        # 프로덕션 환경에서는 verify=True 사용!
        #
        # 설정 이유:
        # - 자체 서명 인증서는 CA가 서명하지 않음
        # - 브라우저/클라이언트가 기본적으로 거부
        # - 개발/테스트를 위해 검증 비활성화
        #
        # 보안 고려사항:
        # - 프로덕션: Let's Encrypt 등 공인 CA 사용
        # - verify=True로 설정
        # - MITM 공격 방어
        #
        # 설정 방법:
        # 1. create_default_context(): 기본 TLS 컨텍스트 생성
        # 2. check_hostname = False: 호스트명 검증 비활성화
        # 3. verify_mode = CERT_NONE: 인증서 검증 비활성화
        self.ssl_context = ssl.create_default_context()
        self.ssl_context.check_hostname = False  # 호스트명 검증 OFF
        self.ssl_context.verify_mode = ssl.CERT_NONE  # 인증서 검증 OFF
        
    async def start(self):
        """
        프록시 세션 시작

        목적: aiohttp 세션 초기화 및 TLS 설정

        동작:
        1. TCPConnector 생성 (TLS 컨텍스트 포함)
        2. ClientSession 생성 (connector 사용)
        3. 프록시 시작 메시지 출력

        TLS 설정:
        - connector에 ssl_context 전달
        - 모든 HTTPS 요청에 적용
        - 자체 서명 인증서 허용

        중요:
        - 세션은 재사용 가능
        - 연결 풀링으로 성능 향상
        - 비동기 작업 지원
        """
        # TLS 컨텍스트를 사용하는 TCP 커넥터 생성
        connector = aiohttp.TCPConnector(ssl=self.ssl_context)
        # 비동기 HTTP 클라이언트 세션 생성
        self.session = aiohttp.ClientSession(connector=connector)
        print("🔗 Secure HTTP Proxy started", file=sys.stderr)
        print(f"🎯 Target server: {self.target_url}", file=sys.stderr)

    async def stop(self):
        """
        프록시 세션 종료

        목적: 리소스 정리 및 연결 종료

        동작:
        1. 세션 존재 확인
        2. 세션 닫기 (연결 종료)
        3. 종료 메시지 출력

        중요:
        - 반드시 세션을 닫아야 함
        - 리소스 누수 방지
        - graceful shutdown
        """
        if self.session:
            await self.session.close()
            print("🔌 Secure HTTP Proxy stopped", file=sys.stderr)
    
    
    async def forward_request(self, mcp_request):
        """
        MCP 요청을 HTTPS 서버로 전달

        목적: 클라이언트 요청을 HTTPS로 암호화하여 서버에 전달

        동작 흐름:
        1. JSON 헤더 설정
        2. HTTPS POST 요청으로 /mcp 엔드포인트 호출
        3. 서버 응답 수신 및 파싱
        4. 에러 처리

        보안:
        - HTTPS로 요청 암호화
        - TLS 컨텍스트 사용
        - 민감한 데이터 보호

        파라미터:
        - mcp_request: MCP JSON-RPC 요청

        반환값:
        - 성공: 서버 응답 (JSON)
        - 실패: 에러 응답 (JSON-RPC 형식)
        """
        try:
            # 표준 JSON API 헤더
            headers = {
                "Content-Type": "application/json",
                "Accept": "application/json"
            }
            
            # MCP 엔드포인트로 POST 요청
            async with self.session.post(
                f"{self.target_url}/mcp",
                json=mcp_request,
                headers=headers
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    print(f"📤 Forwarded request to {self.target_url}", file=sys.stderr)
                    return result
                else:
                    error_text = await response.text()
                    print(f"❌ HTTP Error {response.status}: {error_text}", file=sys.stderr)
                    return {
                        "jsonrpc": "2.0",
                        "error": {
                            "code": response.status,
                            "message": f"HTTP {response.status}: {error_text}"
                        },
                        "id": mcp_request.get("id", 1)
                    }
                    
        except aiohttp.ClientError as e:
            print(f"❌ Connection error: {e}", file=sys.stderr)
            return {
                "jsonrpc": "2.0",
                "error": {
                    "code": -1,
                    "message": f"Connection error: {str(e)}"
                },
                "id": mcp_request.get("id", 1)
            }
        except Exception as e:
            print(f"❌ Unexpected error: {e}", file=sys.stderr)
            return {
                "jsonrpc": "2.0",
                "error": {
                    "code": -1,
                    "message": f"Proxy error: {str(e)}"
                },
                "id": mcp_request.get("id", 1)
            }
    
    async def health_check(self):
        """서버 상태 확인"""
        try:
            async with self.session.get(f"{self.target_url}/health") as response:
                if response.status == 200:
                    result = await response.json()
                    print(f"✅ Health check OK: {result.get('status', 'unknown')}", file=sys.stderr)
                    return True
                else:
                    print(f"⚠️ Health check failed: HTTP {response.status}", file=sys.stderr)
                    return False
        except Exception as e:
            print(f"❌ Health check error: {e}", file=sys.stderr)
            return False

async def handle_stdio(target_url="https://127.0.0.1:8443"):
    """stdio 인터페이스 처리"""
    proxy = SecureHttpServerProxy(target_url)
    await proxy.start()
    
    # 서버 상태 확인
    if not await proxy.health_check():
        print("❌ Target server is not responding", file=sys.stderr)
        await proxy.stop()
        sys.exit(1)
    
    try:
        while True:
            # stdin에서 JSON 요청 읽기
            line = await asyncio.get_event_loop().run_in_executor(
                None, sys.stdin.readline
            )
            
            if not line:
                break
                
            line = line.strip()
            if not line:
                continue
                
            try:
                # JSON 파싱
                request = json.loads(line)
                print(f"📥 Received request: {request.get('method', 'unknown')}", file=sys.stderr)
                
                # 요청 전달 및 응답 받기
                response = await proxy.forward_request(request)
                
                # stdout으로 응답 출력
                print(json.dumps(response))
                sys.stdout.flush()
                
            except json.JSONDecodeError as e:
                print(f"❌ JSON parse error: {e}", file=sys.stderr)
                error_response = {
                    "jsonrpc": "2.0",
                    "error": {
                        "code": -32700,
                        "message": f"Parse error: {str(e)}"
                    },
                    "id": None
                }
                print(json.dumps(error_response))
                sys.stdout.flush()
                
    except KeyboardInterrupt:
        print("🛑 Interrupted by user", file=sys.stderr)
    except Exception as e:
        print(f"❌ Stdio handler error: {e}", file=sys.stderr)
    finally:
        await proxy.stop()

def main():
    """메인 함수"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Secure HTTP Server Proxy")
    parser.add_argument(
        "--target", 
        default="https://127.0.0.1:8443",
        help="Target HTTPS server URL (default: https://127.0.0.1:8443)"
    )
    parser.add_argument(
        "--fastapi-server",
        action="store_true",
        help="Connect to FastAPI+FastMCP hybrid server on port 8444"
    )
    
    args = parser.parse_args()
    
    # 서버 선택
    if args.fastapi_server:
        target_url = "https://127.0.0.1:8444"
    else:
        target_url = args.target
    
    print(f"🚀 Starting Secure HTTP Proxy to {target_url}", file=sys.stderr)
    
    try:
        asyncio.run(handle_stdio(target_url))
    except KeyboardInterrupt:
        print("🛑 Proxy stopped by user", file=sys.stderr)
    except Exception as e:
        print(f"❌ Proxy failed: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()


# ===========================================
# 학습 정리
# ===========================================
"""
이 파일에서 배운 내용:

1. HTTPS 프록시 구현

   프록시 패턴:
   - STDIO 인터페이스 <-> HTTPS 변환
   - 클라이언트와 서버 사이의 중계자
   - Transport 레이어 브릿지
   - 보안 통신 제공

   장점:
   - 클라이언트는 STDIO만 사용
   - 서버는 HTTPS로 보안 제공
   - 프록시가 TLS 암호화 처리
   - 유연한 아키텍처

2. TLS 컨텍스트 설정

   자체 서명 인증서 처리:
   ssl_context = ssl.create_default_context()
   ssl_context.check_hostname = False
   ssl_context.verify_mode = ssl.CERT_NONE

   설정 의미:
   - check_hostname = False: 호스트명 검증 OFF
   - verify_mode = CERT_NONE: 인증서 검증 OFF
   - 자체 서명 인증서 허용

   프로덕션 설정:
   - check_hostname = True
   - verify_mode = CERT_REQUIRED
   - CA 서명 인증서 사용
   - MITM 공격 방어

3. aiohttp 비동기 HTTP 클라이언트

   세션 생성:
   connector = aiohttp.TCPConnector(ssl=ssl_context)
   session = aiohttp.ClientSession(connector=connector)

   장점:
   - 비동기 I/O로 높은 성능
   - 연결 풀링
   - 세션 재사용
   - TLS 지원

   요청 전송:
   async with session.post(url, json=data) as response:
       result = await response.json()

4. STDIO 인터페이스 처리

   입력 처리:
   - stdin에서 JSON 라인 읽기
   - 비동기 readline 처리
   - JSON 파싱

   출력 처리:
   - stdout으로 JSON 응답 출력
   - flush()로 즉시 전송
   - 버퍼링 방지

   에러 처리:
   - JSON 파싱 에러
   - 연결 에러
   - 타임아웃

5. HTTP vs HTTPS 프록시 비교

   HTTP 프록시 (http_server_proxy.py):
   - 평문 전송
   - 스니핑 가능
   - MITM 공격 취약
   - 빠른 성능

   HTTPS 프록시 (이 파일):
   - 암호화 전송
   - 스니핑 불가
   - MITM 공격 방어
   - TLS 오버헤드

6. Health Check 메커니즘

   목적:
   - 서버 가용성 확인
   - 시작 시 서버 확인
   - 연결 상태 모니터링

   구현:
   async with session.get(f"{url}/health") as response:
       if response.status == 200:
           return True

   활용:
   - 프록시 시작 전 서버 확인
   - 서버 다운 시 즉시 종료
   - 불필요한 대기 방지

7. 에러 처리

   연결 에러:
   - aiohttp.ClientError 처리
   - 서버 다운 감지
   - 재시도 로직 (구현 가능)

   JSON 파싱 에러:
   - JSONDecodeError 처리
   - 에러 응답 생성
   - 클라이언트에 통보

   JSON-RPC 에러 형식:
   {
     "jsonrpc": "2.0",
     "error": {
       "code": -1,
       "message": "error message"
     },
     "id": request_id
   }

8. 명령행 인자 처리

   argparse 사용:
   --target: 대상 서버 URL 지정
   --fastapi-server: FastAPI 서버 선택

   유연한 설정:
   - 다양한 서버 선택
   - 개발/프로덕션 환경 구분
   - 테스트 용이성

9. 비동기 프로그래밍

   asyncio 사용:
   - async/await 문법
   - 비동기 I/O
   - 이벤트 루프

   장점:
   - 높은 동시성
   - 낮은 리소스 사용
   - 스케일링 용이

   주의사항:
   - 블로킹 코드 피하기
   - run_in_executor 사용
   - 에러 전파 처리

10. 실행 및 테스트

    실행 방법:
    # 기본 (8443 포트)
    python3 secure_http_server_proxy.py

    # FastAPI 서버 (8444 포트)
    python3 secure_http_server_proxy.py --fastapi-server

    # 커스텀 URL
    python3 secure_http_server_proxy.py --target https://example.com:8443

    Docker 환경:
    make shell python3 Part2_SSL/With_TLS/secure_http_server_proxy.py

    테스트:
    - test_secure_server_proxy.py 실행
    - 프록시를 통한 MCP 도구 호출
    - HTTPS 통신 확인

핵심 메시지:
HTTPS 프록시는 HTTP 프록시의 모든 보안 문제를 해결합니다.
TLS 암호화로 데이터를 보호하고, 인증서 검증으로 MITM 공격을 방어합니다.
자체 서명 인증서는 개발/테스트용으로만 사용하고,
프로덕션 환경에서는 반드시 공인 CA 인증서를 사용해야 합니다!
"""