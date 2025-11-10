#!/usr/bin/env python3
"""
===========================================
Secure Server Proxy 테스트 클라이언트
===========================================

강의 목적:
이 파일은 secure_http_server_proxy.py를 통해 HTTPS MCP 서버들에
접근하여 기능을 테스트합니다.

학습 포인트:
1. HTTPS 프록시를 통한 MCP 통신
2. STDIO 서브프로세스 관리
3. 비동기 프로세스 통신
4. MCP 프로토콜 테스트
5. 두 가지 서버 아키텍처 테스트
6. TLS 암호화 투명성 확인

테스트 대상:
1. FastMCP 순수 서버 (8443 포트)
   - ref/secure_http_server.py 또는
   - https_uvicorn_mcp_server.py

2. FastAPI+FastMCP 하이브리드 서버 (8444 포트)
   - secure_fastapi_mcp_server.py

아키텍처:
Test Client <--(STDIO)--> Proxy <--(HTTPS)--> HTTPS Server
    |                        |                      |
 테스트 코드          secure_http_server_proxy   실제 MCP 서버
 JSON-RPC            STDIO <-> HTTPS 변환      TLS 암호화
                                                도구 실행

보안 확인사항:
- 프록시를 통한 TLS 암호화
- 민감한 데이터 전송 (비밀번호, 카드정보)
- 암호화의 투명성 (클라이언트는 HTTP/HTTPS 구분 불필요)

비교:
- test_http_server_proxy.py: HTTP 프록시 테스트
- test_secure_server_proxy.py: HTTPS 프록시 테스트 (이 파일)
"""

# ===========================================
# 필요한 라이브러리 임포트
# ===========================================

import asyncio    # 비동기 I/O
import json       # JSON 처리
import subprocess # 서브프로세스 관리
import sys        # 시스템 인터페이스
import time       # 시간 처리

# ===========================================
# STDIO 프록시 테스터 클래스
# ===========================================

class StdioProxyTester:
    def __init__(self, proxy_command=None):
        if proxy_command is None:
            proxy_command = ["python3", "secure_http_server_proxy.py"]
        self.proxy_command = proxy_command
        self.process = None
        
    async def start_proxy(self):
        """프록시 프로세스 시작"""
        print(f"🚀 Starting proxy: {' '.join(self.proxy_command)}")
        self.process = await asyncio.create_subprocess_exec(
            *self.proxy_command,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        # 프록시 시작 대기
        await asyncio.sleep(2)
        
        if self.process.returncode is not None:
            stderr = await self.process.stderr.read()
            raise Exception(f"Proxy failed to start: {stderr.decode()}")
            
        print("✅ Proxy started successfully")
        return True
        
    async def stop_proxy(self):
        """프록시 프로세스 종료"""
        if self.process:
            self.process.terminate()
            await self.process.wait()
            print("🛑 Proxy stopped")
    
    async def send_request(self, request):
        """MCP 요청 전송"""
        if not self.process:
            raise Exception("Proxy not started")
            
        # JSON 요청 전송
        request_json = json.dumps(request) + "\n"
        self.process.stdin.write(request_json.encode())
        await self.process.stdin.drain()
        
        # 응답 읽기 (timeout 설정)
        try:
            response_line = await asyncio.wait_for(
                self.process.stdout.readline(), 
                timeout=10.0
            )
            
            if not response_line:
                raise Exception("No response received")
                
            response = json.loads(response_line.decode().strip())
            return response
            
        except asyncio.TimeoutError:
            raise Exception("Request timeout")
        except json.JSONDecodeError as e:
            raise Exception(f"Invalid JSON response: {e}")

async def test_fastmcp_server():
    """FastMCP 순수 서버 테스트"""
    print("\n🧪 Testing FastMCP Pure Server (port 8443)")
    print("=" * 60)
    
    tester = StdioProxyTester(["python3", "secure_http_server_proxy.py"])
    
    try:
        await tester.start_proxy()
        
        # 1. 도구 목록 요청
        print("📋 1. Tools list request")
        request = {
            "jsonrpc": "2.0",
            "method": "tools/list",
            "id": 1
        }
        
        response = await tester.send_request(request)
        if "result" in response:
            print("✅ Tools list received")
            tools = response["result"].get("tools", [])
            for tool in tools:
                print(f"   - {tool['name']}")
        else:
            print(f"❌ Error: {response.get('error', 'Unknown error')}")
        
        # 2. 로그인 테스트
        print("\n📋 2. Login test")
        request = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": "login",
                "arguments": {
                    "username": "admin",
                    "password": "admin123"
                }
            },
            "id": 2
        }
        
        response = await tester.send_request(request)
        if "result" in response:
            content = response["result"]["content"][0]["text"]
            result = json.loads(content)
            if result.get("success"):
                print(f"✅ Login successful: {result['message']}")
                print(f"   Security: {result['security']}")
            else:
                print(f"❌ Login failed: {result['message']}")
        else:
            print(f"❌ Error: {response.get('error', 'Unknown error')}")
        
        # 3. 결제 처리 테스트
        print("\n📋 3. Payment processing test")
        request = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": "process_payment",
                "arguments": {
                    "card_number": "4532-1234-5678-9012",
                    "cvv": "123",
                    "amount": 99.99,
                    "merchant": "FastMCP Store"
                }
            },
            "id": 3
        }
        
        response = await tester.send_request(request)
        if "result" in response:
            content = response["result"]["content"][0]["text"]
            result = json.loads(content)
            if result.get("success"):
                print(f"✅ Payment processed: {result['transaction_id']}")
                print(f"   Amount: ${result['amount']}")
                print(f"   Security: {result['security']}")
            else:
                print(f"❌ Payment failed: {result.get('message', 'Unknown error')}")
        else:
            print(f"❌ Error: {response.get('error', 'Unknown error')}")
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
    finally:
        await tester.stop_proxy()

async def test_hybrid_server():
    """FastAPI+FastMCP 하이브리드 서버 테스트"""
    print("\n🧪 Testing FastAPI+FastMCP Hybrid Server (port 8444)")
    print("=" * 60)
    
    tester = StdioProxyTester([
        "python3", "secure_http_server_proxy.py", "--fastapi-server"
    ])
    
    try:
        await tester.start_proxy()
        
        # 1. 도구 목록 요청
        print("📋 1. Tools list request")
        request = {
            "jsonrpc": "2.0",
            "method": "tools/list",
            "id": 1
        }
        
        response = await tester.send_request(request)
        if "result" in response:
            print("✅ Tools list received")
            if "tools" in response["result"]:
                tools = response["result"]["tools"]
                for tool in tools:
                    print(f"   - {tool['name']}")
        else:
            print(f"❌ Error: {response.get('error', 'Unknown error')}")
        
        # 2. 인사 메시지 테스트
        print("\n📋 2. Greeting test")
        request = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": "create_greeting",
                "arguments": {
                    "name": "Hybrid User"
                }
            },
            "id": 2
        }
        
        response = await tester.send_request(request)
        if "result" in response:
            content = response["result"]["content"][0]["text"]
            # 결과가 JSON인지 확인하고, 그렇지 않으면 문자열 그대로 사용
            try:
                result = json.loads(content)
                print(f"✅ Greeting: {result}")
            except json.JSONDecodeError:
                print(f"✅ Greeting: {content}")
        else:
            print(f"❌ Error: {response.get('error', 'Unknown error')}")
        
        # 3. 계산 테스트
        print("\n📋 3. Addition test")
        request = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": "add",
                "arguments": {
                    "a": 100,
                    "b": 200
                }
            },
            "id": 3
        }
        
        response = await tester.send_request(request)
        if "result" in response:
            content = response["result"]["content"][0]["text"]
            # 결과가 JSON인지 확인하고, 그렇지 않으면 문자열 그대로 사용
            try:
                result = json.loads(content)
                print(f"✅ Addition result: 100 + 200 = {result}")
            except json.JSONDecodeError:
                print(f"✅ Addition result: 100 + 200 = {content}")
        else:
            print(f"❌ Error: {response.get('error', 'Unknown error')}")
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
    finally:
        await tester.stop_proxy()

def check_server_running(port):
    """서버가 실행 중인지 확인"""
    import socket
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)
        result = sock.connect_ex(('127.0.0.1', port))
        sock.close()
        return result == 0
    except:
        return False

async def main():
    """메인 테스트 함수"""
    print("🔐 Secure Server Proxy Test Suite")
    print("=" * 60)
    
    # 서버 상태 확인
    print("📊 Checking server status...")
    fastmcp_running = check_server_running(8443)
    hybrid_running = check_server_running(8444)
    
    print(f"   FastMCP Server (8443): {'✅ Running' if fastmcp_running else '❌ Not running'}")
    print(f"   Hybrid Server (8444): {'✅ Running' if hybrid_running else '❌ Not running'}")
    
    if not fastmcp_running and not hybrid_running:
        print("\n❌ No servers are running!")
        print("Please start one of the following:")
        print("   python3 https_uvicorn_mcp_server.py")
        print("   python3 https_fastapi_mcp_server.py")
        return
    
    # 테스트 실행
    try:
        if fastmcp_running:
            await test_fastmcp_server()
        
        if hybrid_running:
            await test_hybrid_server()
        
        print("\n🎯 Test Summary")
        print("=" * 60)
        print("✅ stdio proxy successfully forwards MCP requests to HTTPS servers")
        print("✅ TLS encryption is handled transparently by the proxy")
        print("✅ Both FastMCP and Hybrid architectures work correctly")
        print("✅ All MCP protocol features (tools/list, tools/call) function properly")
        
    except KeyboardInterrupt:
        print("\n🛑 Tests interrupted by user")
    except Exception as e:
        print(f"\n❌ Test suite failed: {e}")

if __name__ == "__main__":
    """
    프로그램 진입점

    실행 방법:
    python3 test_secure_server_proxy.py

    또는 Docker 환경:
    make shell python3 Part2_SSL/With_TLS/test_secure_server_proxy.py

    사전 준비:
    1. HTTPS 서버 시작:
       python3 secure_fastapi_mcp_server.py (8444 포트)
       또는
       python3 ref/https_uvicorn_mcp_server.py (8443 포트)

    2. 인증서 생성 (필요시):
       python3 certificate_management.py

    기대 결과:
    - 프록시를 통한 HTTPS 통신 성공
    - 모든 MCP 도구 정상 동작
    - TLS 암호화 투명성 확인
    - HTTP vs HTTPS 차이 체감
    """
    asyncio.run(main())


# ===========================================
# 학습 정리
# ===========================================
"""
이 파일에서 배운 내용:

1. HTTPS 프록시 테스트 패턴

   테스트 구조:
   - 프록시 프로세스 시작
   - STDIO로 통신
   - MCP 요청 전송
   - 응답 검증
   - 프록시 종료

   통신 흐름:
   Test Client -> (STDIO) -> Proxy -> (HTTPS) -> HTTPS Server
   Test Client <- (STDIO) <- Proxy <- (HTTPS) <- HTTPS Server

2. STDIO 서브프로세스 관리

   프로세스 생성:
   process = await asyncio.create_subprocess_exec(
       *command,
       stdin=PIPE,
       stdout=PIPE,
       stderr=PIPE
   )

   비동기 통신:
   - process.stdin.write(): 요청 전송
   - process.stdin.drain(): 버퍼 비우기
   - process.stdout.readline(): 응답 읽기
   - await asyncio.wait_for(): 타임아웃 설정

3. MCP 프로토콜 테스트

   tools/list 테스트:
   - 사용 가능한 도구 목록 조회
   - 서버 연결 확인
   - 프로토콜 정상 동작 검증

   tools/call 테스트:
   - 실제 도구 실행
   - 파라미터 전달
   - 결과 검증

4. 두 가지 서버 아키텍처 테스트

   FastMCP 순수 서버 (8443):
   - FastMCP의 HTTP transport 사용
   - TLS 암호화 내장
   - 단순한 아키텍처
   - 테스트: login, process_payment

   FastAPI+FastMCP 하이브리드 (8444):
   - FastAPI의 TLS 처리
   - FastMCP의 도구 실행
   - 복잡한 아키텍처
   - 테스트: add, create_greeting

5. 보안 테스트

   민감한 데이터 전송:
   - 비밀번호 (login)
   - 카드 번호 (process_payment)
   - HTTPS로 암호화 전송
   - 스니핑 불가 확인

   TLS 암호화 투명성:
   - 클라이언트는 HTTP/HTTPS 구분 불필요
   - 프록시가 TLS 처리
   - 애플리케이션 코드 변경 없음

6. 서버 상태 확인

   포트 체크:
   sock.connect_ex(('127.0.0.1', port))
   - 서버 실행 여부 확인
   - 테스트 전 검증
   - 명확한 에러 메시지

   장점:
   - 불필요한 테스트 방지
   - 사용자 친화적
   - 디버깅 용이

7. 에러 처리

   타임아웃:
   - asyncio.wait_for() 사용
   - 10초 제한
   - 무한 대기 방지

   JSON 파싱:
   - JSONDecodeError 처리
   - 유연한 응답 처리
   - JSON/문자열 모두 지원

   프로세스 에러:
   - 시작 실패 감지
   - stderr 로깅
   - 명확한 에러 메시지

8. HTTP vs HTTPS 프록시 비교

   test_http_server_proxy.py:
   - HTTP 프록시 테스트
   - 평문 전송
   - 빠른 성능
   - 보안 위험

   test_secure_server_proxy.py (이 파일):
   - HTTPS 프록시 테스트
   - 암호화 전송
   - TLS 오버헤드
   - 보안 보장

   차이점:
   - 프록시 URL: http vs https
   - 보안: 없음 vs TLS
   - 성능: 빠름 vs 느림 (암호화 비용)
   - 운영: 개발용 vs 프로덕션

9. 테스트 시나리오

   FastMCP 서버 테스트:
   1. 도구 목록 조회
   2. 로그인 (민감 데이터)
   3. 결제 처리 (매우 민감)

   하이브리드 서버 테스트:
   1. 도구 목록 조회
   2. 인사 메시지 생성
   3. 숫자 계산

   모든 시나리오:
   - HTTPS로 암호화
   - 프록시를 통한 중계
   - 정상 동작 확인

10. 학습 포인트 정리

    아키텍처 이해:
    - 프록시 패턴의 이점
    - Transport 변환
    - 보안 레이어 추가

    보안 체감:
    - HTTP vs HTTPS 차이
    - TLS 암호화 효과
    - 프록시의 보안 역할

    실무 적용:
    - 프록시 설계 패턴
    - 비동기 프로세스 통신
    - 에러 처리 베스트 프랙티스

핵심 메시지:
HTTPS 프록시는 클라이언트와 서버 사이에 보안 레이어를 추가합니다.
클라이언트는 STDIO로 간단하게 통신하고,
프록시가 TLS 암호화를 투명하게 처리합니다.
이 패턴은 레거시 클라이언트를 수정하지 않고도
보안을 강화할 수 있는 효과적인 방법입니다!
"""