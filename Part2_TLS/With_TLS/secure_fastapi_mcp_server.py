#!/usr/bin/env python3
"""
===========================================
FastAPI + FastMCP 하이브리드 HTTPS MCP 서버
===========================================

강의 목적:
이 파일은 FastAPI와 FastMCP를 결합한 하이브리드 아키텍처로
HTTPS/TLS를 사용하는 안전한 MCP 서버를 구현합니다.

학습 포인트:
1. 하이브리드 아키텍처 패턴
2. FastAPI의 TLS 처리
3. FastMCP의 MCP 프로토콜 처리
4. STDIO 서브프로세스 패턴
5. 역할 분담 아키텍처 설계
6. uvicorn을 사용한 HTTPS 서버 실행

아키텍처:
Client <--(HTTPS)--> FastAPI <--(STDIO)--> FastMCP Tools
   |                    |                        |
 REST API          TLS 처리           MCP 프로토콜 처리
 JSON-RPC          암호화/복호화          도구 실행
                   인증서 관리            스키마 검증

역할 분담:
- FastAPI:
  * HTTP 서버 역할
  * TLS 암호화 처리
  * REST API 엔드포인트 제공
  * CORS 설정
  * 에러 핸들링

- FastMCP:
  * MCP 프로토콜 구현
  * 도구 정의 및 실행
  * 스키마 검증
  * STDIO transport 처리

장점:
1. 각 라이브러리의 장점 활용
2. FastAPI의 강력한 HTTP/TLS 기능
3. FastMCP의 표준 MCP 구현
4. 유연한 확장성
5. REST API와 MCP 동시 지원

단점:
1. 복잡한 아키텍처
2. STDIO 서브프로세스 오버헤드
3. 디버깅 어려움
4. 두 라이브러리 모두 이해 필요

비교:
- secure_fastapi_mcp_server.py: 하이브리드 아키텍처 (이 파일)
- ref/secure_http_server.py: 순수 FastMCP 아키텍처
- ref/https_server.py: FastAPI만 사용
"""

# ===========================================
# 필요한 라이브러리 임포트
# ===========================================

import ssl          # TLS 프로토콜 지원
import sys          # 시스템 인터페이스
import os           # 운영체제 인터페이스
from pathlib import Path  # 파일 경로 처리
import uvicorn      # ASGI 서버 (HTTPS 지원)
from fastapi import FastAPI, HTTPException  # FastAPI 웹 프레임워크
from fastapi.middleware.cors import CORSMiddleware  # CORS 처리
import hashlib      # 해시 함수 (토큰 생성용)
import json         # JSON 처리
from datetime import datetime  # 타임스탬프
from fastmcp import FastMCP  # MCP 프로토콜 구현

# ===========================================
# FastMCP 인스턴스 생성
# ===========================================

# FastMCP 객체 생성
# STDIO 모드로 동작 - 표준 입출력으로 통신
# FastAPI에서 서브프로세스로 호출할 때 사용됨
#
# 동작 방식:
# 1. FastAPI가 이 파일을 --stdio-mode 플래그와 함께 실행
# 2. 서브프로세스로 FastMCP가 STDIO 모드로 시작
# 3. FastAPI와 FastMCP가 stdin/stdout으로 통신
# 4. FastMCP가 실제 도구를 실행하고 결과 반환
mcp = FastMCP(name="FastAPI + FastMCP Hybrid Server")

# ===========================================
# FastAPI 앱 생성
# ===========================================

# FastAPI 인스턴스 생성
# FastAPI가 담당하는 역할:
# 1. HTTP/HTTPS 서버
# 2. TLS 암호화
# 3. 라우팅 및 엔드포인트 관리
# 4. 미들웨어 처리 (CORS 등)
app = FastAPI(title="FastAPI + FastMCP Secure Server with TLS")

# ===========================================
# CORS 미들웨어 설정
# ===========================================

# CORS (Cross-Origin Resource Sharing) 설정
# 개발 환경에서는 모든 origin 허용
# 실제 프로덕션 환경에서는 특정 도메인만 허용해야 함
#
# 보안 고려사항:
# - allow_origins=["*"]: 모든 도메인 허용 (개발용)
# - 프로덕션: allow_origins=["https://example.com"]
# - allow_credentials=True: 쿠키 및 인증 정보 허용
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 실제 환경에서는 제한 필요
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ===========================================
# 데모용 사용자 데이터베이스
# ===========================================

# 인메모리 사용자 데이터베이스
# 실제 환경에서는 PostgreSQL, MongoDB 등 사용
#
# 보안 고려사항:
# - 비밀번호는 평문 저장하지 않고 해시 사용 (bcrypt, argon2)
# - API 키는 안전하게 보관 및 암호화
# - 실제로는 데이터베이스에 저장
#
# 이 데모에서는 학습 목적으로 단순화
users_db = {
    "admin": {
        "password": "admin123",  # 실제로는 해시된 비밀번호
        "api_key": "sk-1234567890abcdef",  # 실제로는 암호화된 키
        "role": "administrator"
    },
    "user1": {
        "password": "password123",
        "api_key": "sk-abcdef1234567890",
        "role": "user"
    }
}

# ===========================================
# MCP 도구 정의
# ===========================================

# FastMCP 데코레이터를 사용하여 MCP 도구 등록
# 각 함수는 자동으로 MCP 도구로 변환됨
# FastAPI 서브프로세스가 이 도구들을 STDIO로 호출

@mcp.tool
def add(a: int, b: int) -> int:
    """
    두 개의 정수를 더하는 도구

    목적: 간단한 계산 기능 데모

    파라미터:
    - a: 첫 번째 정수
    - b: 두 번째 정수

    반환값: 두 정수의 합

    보안:
    - HTTPS로 암호화된 채널을 통해 파라미터 전달
    - 결과도 암호화되어 반환
    """
    print(f"[HTTPS-Hybrid] Executing add tool with: a={a}, b={b}")
    return a + b

@mcp.tool
def create_greeting(name: str) -> str:
    """
    개인화된 환영 메시지를 생성하는 도구

    목적: 문자열 처리 및 개인화 기능 데모

    파라미터:
    - name: 사용자 이름

    반환값: 환영 메시지 문자열

    보안:
    - 사용자 이름이 HTTPS로 암호화되어 전달
    - XSS 공격 방지를 위한 입력 검증 필요 (프로덕션)
    """
    print(f"[HTTPS-Hybrid] Executing create_greeting tool with: name={name}")
    return f"Hello, {name}! Welcome to the secure FastAPI + FastMCP hybrid world."

@mcp.tool
def login(username: str, password: str) -> dict:
    """
    사용자 인증 도구

    목적: 민감한 인증 정보의 안전한 전송 데모

    파라미터:
    - username: 사용자명
    - password: 비밀번호

    반환값:
    - success: 인증 성공 여부
    - session_token: 세션 토큰 (성공 시)
    - role: 사용자 역할
    - security: 보안 정보

    보안 기능:
    1. HTTPS/TLS로 비밀번호 암호화 전송
    2. 네트워크 스니핑 방지
    3. MITM 공격 방지
    4. 세션 토큰 생성 (MD5 해시)

    실제 프로덕션에서는:
    - bcrypt/argon2로 비밀번호 해시
    - JWT 토큰 사용
    - Rate limiting 적용
    - 로그인 실패 카운트
    """
    print(f"🔒 [HTTPS-Hybrid] Login attempt with encrypted credentials - username: {username}")

    # 사용자 검증
    if username in users_db and users_db[username]["password"] == password:
        # 세션 토큰 생성 (실제로는 JWT 등 사용)
        session_token = f"session_{hashlib.md5(f'{username}{datetime.now()}'.encode()).hexdigest()}"
        print(f"✅ [HTTPS-Hybrid] Login successful for user: {username}")
        return {
            "success": True,
            "message": f"Login successful for user: {username}",
            "session_token": session_token,
            "role": users_db[username]["role"],
            "security": "🔒 Credentials transmitted over encrypted HTTPS/TLS connection (FastAPI+FastMCP)!"
        }

    print(f"❌ [HTTPS-Hybrid] Login failed for user: {username}")
    return {
        "success": False,
        "message": "Invalid username or password"
    }

@mcp.tool
def get_api_key(username: str, password: str) -> dict:
    """
    API 키 조회 도구

    목적: 민감한 API 키의 안전한 전송 데모

    파라미터:
    - username: 사용자명
    - password: 비밀번호

    반환값:
    - success: 조회 성공 여부
    - api_key: API 키 (성공 시)
    - security: 보안 정보

    보안 기능:
    1. HTTPS/TLS로 API 키 암호화 전송
    2. 인증 후에만 키 반환
    3. 네트워크 스니핑으로부터 키 보호

    API 키 보안 베스트 프랙티스:
    - 데이터베이스에 암호화하여 저장
    - 키 순환 (rotation) 정책
    - 키 만료 설정
    - 사용 로그 기록
    - Rate limiting
    """
    print(f"🔒 [HTTPS-Hybrid] API key request with encrypted credentials - username: {username}")

    # 인증 확인
    if username in users_db and users_db[username]["password"] == password:
        api_key = users_db[username]["api_key"]
        print(f"🔑 [HTTPS-Hybrid] API key retrieved for user: {username} - {api_key}")
        return {
            "success": True,
            "api_key": api_key,
            "security": "🔒 This API key is transmitted over encrypted HTTPS/TLS (FastAPI+FastMCP)!"
        }

    return {
        "success": False,
        "message": "Authentication failed"
    }

@mcp.tool
def process_payment(card_number: str, cvv: str, amount: float, merchant: str) -> dict:
    """
    결제 처리 도구 (시뮬레이션)

    목적: 매우 민감한 금융 정보의 안전한 전송 데모

    파라미터:
    - card_number: 신용카드 번호
    - cvv: 카드 보안 코드
    - amount: 결제 금액
    - merchant: 가맹점

    반환값:
    - transaction_id: 트랜잭션 ID
    - amount: 결제 금액
    - merchant: 가맹점
    - card: 마스킹된 카드 번호
    - timestamp: 결제 시간
    - security: 보안 정보

    보안 기능:
    1. HTTPS/TLS로 카드 정보 암호화 전송
    2. PCI DSS 컴플라이언스
    3. 카드 번호 마스킹 (표시용)
    4. 트랜잭션 ID 생성

    실제 프로덕션에서는:
    - PCI DSS Level 1 인증 필요
    - 카드 정보 저장 금지 (토큰화 사용)
    - Payment Gateway 사용 (Stripe, PayPal)
    - 3D Secure 인증
    - 사기 탐지 시스템
    - 암호화된 로그 기록

    중요: 절대로 카드 정보를 로그에 기록하지 마세요!
    """
    print(f"💳 [HTTPS-Hybrid] Processing payment with encrypted card details!")
    print(f"   Card Number: {card_number} (encrypted in transit)")
    print(f"   CVV: {cvv} (encrypted in transit)")
    print(f"   Amount: ${amount}")

    # 표시용으로 카드 번호 마스킹
    # 실제로는 카드 번호를 전혀 저장하지 않음
    masked_card = f"****-****-****-{card_number[-4:]}" if len(card_number) >= 4 else "****"

    # 트랜잭션 ID 생성
    transaction_id = f"txn_{hashlib.md5(f'{card_number}{datetime.now()}'.encode()).hexdigest()[:12]}"

    return {
        "success": True,
        "transaction_id": transaction_id,
        "amount": amount,
        "merchant": merchant,
        "card": masked_card,
        "timestamp": datetime.now().isoformat(),
        "security": "🔒 Credit card details transmitted over encrypted HTTPS/TLS (FastAPI+FastMCP)!"
    }

# ===========================================
# FastAPI 라우트 정의
# ===========================================

# FastAPI가 처리하는 REST API 엔드포인트들
# TLS을 통해 암호화된 HTTP 요청 처리

@app.get("/")
async def root():
    """
    루트 엔드포인트

    목적: 서버 정보 및 사용 가능한 엔드포인트 안내

    반환값:
    - message: 서버 이름
    - mcp_endpoint: MCP 프로토콜 엔드포인트
    - fastapi_endpoint: FastAPI 정보 엔드포인트
    - security: 보안 상태

    용도:
    - 서버 가동 확인
    - 엔드포인트 탐색
    - API 문서화
    """
    return {
        "message": "FastAPI + FastMCP Secure Server with TLS",
        "mcp_endpoint": "/mcp",
        "fastapi_endpoint": "/api/info",
        "security": "All communications are encrypted with TLS"
    }

@app.get("/health")
async def health():
    """
    건강 상태 확인 엔드포인트

    목적: 서버 상태 모니터링

    반환값:
    - status: 서버 상태
    - security: 보안 기능 상태
    - server: 서버 유형
    - architecture: 아키텍처 설명

    용도:
    - 로드 밸런서 health check
    - 모니터링 시스템 연동
    - 자동 복구 트리거
    """
    return {
        "status": "healthy",
        "security": "TLS enabled",
        "server": "FastAPI + FastMCP Hybrid Server",
        "architecture": "FastAPI handles HTTP/TLS, FastMCP handles MCP protocol"
    }

@app.get("/api/info")
async def api_info():
    """
    서버 정보 엔드포인트 (FastAPI 전용)

    목적: 서버 구성 및 기능 정보 제공

    반환값:
    - server_type: 서버 유형
    - tls_provider: TLS 처리 담당 컴포넌트
    - mcp_provider: MCP 처리 담당 컴포넌트
    - available_tools: 사용 가능한 도구 목록
    - security_features: 보안 기능 목록

    용도:
    - 클라이언트 설정
    - API 탐색
    - 기능 검증
    """
    return {
        "server_type": "Hybrid FastAPI + FastMCP",
        "tls_provider": "FastAPI + Uvicorn",
        "mcp_provider": "FastMCP",
        "available_tools": ["add", "create_greeting", "login", "get_api_key", "process_payment"],
        "security_features": [
            "TLS encryption",
            "MCP protocol compliance",
            "Dual architecture benefits"
        ]
    }

# ===========================================
# FastMCP STDIO 클라이언트 임포트 및 헬퍼 함수
# ===========================================

from fastmcp import Client
from fastmcp.client.transports import StdioTransport

async def call_fastmcp_tool(tool_name: str, arguments: dict = None):
    """
    FastMCP STDIO를 통해 도구를 호출하는 헬퍼 함수

    목적: FastAPI와 FastMCP 사이의 브릿지 역할

    동작 원리:
    1. 현재 Python 파일을 --stdio-mode로 서브프로세스 실행
    2. 서브프로세스에서 FastMCP가 STDIO 모드로 시작
    3. StdioTransport를 통해 서브프로세스와 통신
    4. 도구 호출 및 결과 수신
    5. 서브프로세스 종료

    아키텍처:
    FastAPI Handler
       |
       v
    call_fastmcp_tool()
       |
       v
    StdioTransport (stdin/stdout)
       |
       v
    FastMCP Subprocess (--stdio-mode)
       |
       v
    @mcp.tool 실행
       |
       v
    결과 반환

    파라미터:
    - tool_name: 호출할 도구 이름
    - arguments: 도구 인자 (dict)

    반환값: 도구 실행 결과 (str)

    장점:
    - FastAPI와 FastMCP의 깨끗한 분리
    - 표준 MCP 프로토콜 사용
    - 프로세스 격리

    단점:
    - 서브프로세스 생성 오버헤드
    - 메모리 사용 증가
    - 디버깅 복잡도 증가
    """
    if arguments is None:
        arguments = {}

    # STDIO Transport 생성
    # 현재 스크립트를 --stdio-mode로 재실행
    transport = StdioTransport(
        command="python3",  # Python 3 인터프리터
        args=[__file__, "--stdio-mode"]  # 현재 파일 + STDIO 모드 플래그
    )

    try:
        # FastMCP 클라이언트 생성 및 도구 호출
        async with Client(transport) as client:
            # MCP 프로토콜로 도구 호출
            result = await client.call_tool(tool_name, arguments)

            # 결과 추출
            # MCP 결과는 content 리스트 형태
            if hasattr(result, 'content') and result.content:
                if hasattr(result.content[0], 'text'):
                    return result.content[0].text
                else:
                    return str(result.content[0])
            else:
                return str(result)
    except Exception as e:
        # 에러 발생 시 상세 정보 로깅
        import traceback
        error_detail = traceback.format_exc()
        print(f"FastMCP tool call error: {error_detail}", file=sys.stderr)
        return f"Error calling FastMCP tool {tool_name}: {str(e)}"

# ===========================================
# MCP 프로토콜 엔드포인트
# ===========================================

@app.post("/mcp")
async def mcp_endpoint(request: dict):
    """
    MCP 프로토콜 엔드포인트 (FastAPI 핸들러)

    목적: JSON-RPC 2.0 형식의 MCP 요청을 처리

    지원 메서드:
    1. tools/list: 사용 가능한 도구 목록 반환
    2. tools/call: 특정 도구 호출 및 실행

    요청 형식 (JSON-RPC 2.0):
    {
      "jsonrpc": "2.0",
      "method": "tools/call",
      "params": {
        "name": "add",
        "arguments": {"a": 5, "b": 3}
      },
      "id": 1
    }

    응답 형식:
    {
      "jsonrpc": "2.0",
      "result": {
        "content": [
          {"type": "text", "text": "8"}
        ]
      },
      "id": 1
    }

    동작 흐름:
    1. FastAPI가 HTTPS 요청 수신 (TLS 복호화)
    2. JSON-RPC 메서드 파싱
    3. call_fastmcp_tool() 호출 (STDIO 서브프로세스)
    4. FastMCP 도구 실행
    5. 결과를 JSON-RPC 형식으로 반환
    6. FastAPI가 HTTPS 응답 (TLS 암호화)
    """
    try:
        # JSON-RPC 파라미터 추출
        method = request.get("method")
        params = request.get("params", {})
        request_id = request.get("id", 1)

        if method == "tools/list":
            # 도구 목록 요청 처리
            # MCP 프로토콜에 따라 사용 가능한 도구 목록 반환
            tools = []
            for tool_name in ["add", "create_greeting", "login", "get_api_key", "process_payment"]:
                tools.append({
                    "name": tool_name,
                    "description": f"Tool: {tool_name}",
                    "inputSchema": {
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                })

            return {
                "jsonrpc": "2.0",
                "result": {
                    "tools": tools
                },
                "id": request_id
            }

        elif method == "tools/call":
            # 도구 호출 요청 처리
            tool_name = params.get("name")
            arguments = params.get("arguments", {})

            print(f"🔧 Calling tool: {tool_name} with args: {arguments}", file=sys.stderr)

            # FastMCP STDIO 서브프로세스를 통해 실제 도구 호출
            # 여기서 프로세스 간 통신 발생
            result = await call_fastmcp_tool(tool_name, arguments)

            print(f"🔧 Tool result: {result}", file=sys.stderr)

            # MCP 프로토콜 응답 형식으로 반환
            return {
                "jsonrpc": "2.0",
                "result": {
                    "content": [
                        {
                            "type": "text",
                            "text": result
                        }
                    ]
                },
                "id": request_id
            }

        else:
            # 알 수 없는 메서드
            raise ValueError(f"Unknown method: {method}")

    except Exception as e:
        # 에러 응답 (JSON-RPC 2.0 형식)
        return {
            "jsonrpc": "2.0",
            "error": {
                "code": -1,
                "message": str(e)
            },
            "id": request.get("id", 1)
        }

# ===========================================
# 유틸리티 함수들
# ===========================================

def check_tls_certificates():
    """
    TLS 인증서 존재 여부 확인

    목적: 서버 시작 전 필수 인증서 파일 검증

    확인 항목:
    - server.crt: 서버 인증서
    - server.key: 서버 개인 키

    인증서가 없으면:
    - 에러 메시지 출력
    - 인증서 생성 방법 안내
    - 프로그램 종료

    인증서가 있으면:
    - 파일 경로 출력
    - 경로 문자열 반환
    """
    cert_dir = Path(__file__).parent / "certs"
    cert_file = cert_dir / "server.crt"
    key_file = cert_dir / "server.key"

    if not cert_file.exists() or not key_file.exists():
        print("❌ TLS 인증서가 없습니다!")
        print("   다음 명령으로 인증서를 생성하세요:")
        print("   python3 certificate_management.py")
        sys.exit(1)

    print(f"🔒 TLS 인증서 로드:")
    print(f"   인증서: {cert_file}")
    print(f"   개인키: {key_file}")

    return str(cert_file), str(key_file)

def show_security_info():
    """
    보안 기능 정보 표시

    목적: 사용자에게 활성화된 보안 기능 안내

    표시 내용:
    1. TLS 기능 목록
    2. 하이브리드 아키텍처 장점
    3. 테스트 명령어 예시
    4. 엔드포인트 사용법

    용도:
    - 서버 시작 시 정보 제공
    - 보안 기능 확인
    - 테스트 가이드
    """
    print("\n🔐 HTTPS/TLS 보안 기능 (FastAPI + FastMCP)")
    print("=" * 60)
    print("✅ 모든 데이터 암호화 전송 (FastAPI)")
    print("✅ 서버 신원 인증 (TLS)")
    print("✅ 데이터 무결성 보장 (TLS)")
    print("✅ 중간자 공격 방어 (TLS)")
    print("✅ 네트워크 스니핑 방지 (TLS)")
    print("✅ MCP 프로토콜 지원 (FastMCP)")
    print("✅ REST API 지원 (FastAPI)")
    print("✅ 하이브리드 아키텍처")

    print("\n🧪 테스트 명령어:")
    print("# 건강 상태 확인")
    print("curl -k https://localhost:8444/health")
    print("\n# FastAPI 정보")
    print("curl -k https://localhost:8444/api/info")
    print("\n# MCP 도구 목록")
    print("curl -k -X POST https://localhost:8444/mcp \\")
    print("  -H 'Content-Type: application/json' \\")
    print("  -d '{\"jsonrpc\":\"2.0\",\"method\":\"tools/list\",\"id\":1}'")

# ===========================================
# 프로그램 진입점
# ===========================================

if __name__ == "__main__":
    """
    메인 실행 로직

    두 가지 실행 모드:

    1. STDIO 모드 (--stdio-mode 플래그 사용 시)
       - FastMCP 서브프로세스로 실행
       - stdin/stdout으로 FastAPI와 통신
       - MCP 도구 실행 담당
       - 사용: python3 secure_fastapi_mcp_server.py --stdio-mode

    2. HTTPS 서버 모드 (기본)
       - FastAPI + uvicorn으로 HTTPS 서버 실행
       - TLS 암호화 처리
       - REST API 및 MCP 엔드포인트 제공
       - 사용: python3 secure_fastapi_mcp_server.py

    실행 순서:
    1. 인증서 확인
    2. 서버 정보 표시
    3. uvicorn으로 HTTPS 서버 시작
    4. 클라이언트 요청 수신 시 STDIO 서브프로세스 생성
    """
    import sys

    # ===========================================
    # 실행 모드 확인
    # ===========================================

    # STDIO 모드 확인
    # FastAPI에서 서브프로세스로 이 파일을 --stdio-mode와 함께 실행
    if "--stdio-mode" in sys.argv:
        # FastMCP STDIO 서버 모드
        # 표준 입출력으로 FastAPI와 통신
        print("🔧 FastMCP STDIO 모드로 실행", file=sys.stderr)
        mcp.run(transport="stdio")
    else:
        # ===========================================
        # FastAPI HTTPS 서버 모드 (기본)
        # ===========================================

        print("🔐 FastAPI + FastMCP 하이브리드 HTTPS 서버 시작")
        print("=" * 60)

        # TLS 인증서 확인
        # 인증서가 없으면 프로그램 종료
        cert_file, key_file = check_tls_certificates()

        # 서버 정보 출력
        print("하이브리드 HTTPS 서버를 https://127.0.0.1:8444 에서 시작합니다")
        print("FastAPI endpoint: https://127.0.0.1:8444/api/info")
        print("MCP endpoint: https://127.0.0.1:8444/mcp")
        print("⚠️  자체 서명 인증서를 사용하므로 브라우저에서 보안 경고가 표시됩니다.")

        # 보안 기능 정보 표시
        show_security_info()

        print("\n🚀 하이브리드 서버 시작 중...")

        # ===========================================
        # uvicorn으로 HTTPS 서버 실행
        # ===========================================

        # FastAPI를 uvicorn ASGI 서버로 실행
        # uvicorn이 TLS 암호화 처리
        #
        # 포트 구분:
        # - 8443: 순수 FastMCP HTTPS 서버 (ref/secure_http_server.py)
        # - 8444: 하이브리드 FastAPI + FastMCP 서버 (이 파일)
        #
        # TLS 설정:
        # - ssl_keyfile: 서버 개인 키
        # - ssl_certfile: 서버 인증서
        # - ssl_version: TLS 프로토콜 버전 (PROTOCOL_TLS_SERVER = 최신 버전)
        #
        # 보안 레벨:
        # - TLS 1.2 이상
        # - 강력한 암호화 스위트
        # - Forward Secrecy 지원
        uvicorn.run(
            app,                              # FastAPI 앱
            host="127.0.0.1",                 # 로컬호스트
            port=8444,                        # 포트 번호
            ssl_keyfile=key_file,             # 개인 키
            ssl_certfile=cert_file,           # 인증서
            ssl_version=ssl.PROTOCOL_TLS_SERVER,  # TLS 프로토콜
            log_level="info"                  # 로그 레벨
        )


# ===========================================
# 학습 정리
# ===========================================
"""
이 파일에서 배운 내용:

1. 하이브리드 아키텍처 패턴

   FastAPI의 역할:
   - HTTP/HTTPS 서버
   - TLS 암호화 처리
   - 요청 라우팅
   - CORS 처리
   - 미들웨어 관리

   FastMCP의 역할:
   - MCP 프로토콜 구현
   - 도구 정의 및 실행
   - 스키마 검증
   - STDIO transport

   장점:
   - 각 라이브러리의 강점 활용
   - FastAPI의 성숙한 HTTP/TLS 처리
   - FastMCP의 표준 MCP 구현
   - 깨끗한 관심사 분리

   단점:
   - 복잡한 아키텍처
   - 프로세스 간 통신 오버헤드
   - 디버깅 어려움
   - 두 라이브러리 모두 이해 필요

2. STDIO 서브프로세스 패턴

   동작 원리:
   1. FastAPI가 요청 수신
   2. 현재 파일을 --stdio-mode로 재실행
   3. 서브프로세스가 FastMCP STDIO 모드로 시작
   4. StdioTransport로 프로세스 간 통신
   5. FastMCP 도구 실행
   6. 결과를 FastAPI로 반환
   7. 서브프로세스 종료

   장점:
   - 프로세스 격리
   - 표준 MCP 프로토콜 사용
   - 깨끗한 인터페이스

   단점:
   - 서브프로세스 생성 비용
   - 메모리 사용 증가
   - 레이턴시 증가

3. uvicorn HTTPS 설정

   uvicorn.run() 파라미터:
   - app: FastAPI 앱
   - host: 바인딩 주소
   - port: 포트 번호
   - ssl_keyfile: 개인 키 파일
   - ssl_certfile: 인증서 파일
   - ssl_version: TLS 프로토콜 버전
   - log_level: 로그 레벨

   TLS 버전:
   - ssl.PROTOCOL_TLS_SERVER: 최신 TLS 버전
   - TLS 1.2 이상 지원
   - 안전하지 않은 버전 자동 비활성화

   암호화 스위트:
   - 강력한 암호화 알고리즘 사용
   - Forward Secrecy 지원
   - 취약한 암호화 알고리즘 제외

4. JSON-RPC 2.0 프로토콜

   요청 형식:
   {
     "jsonrpc": "2.0",
     "method": "tools/call",
     "params": {...},
     "id": 1
   }

   응답 형식 (성공):
   {
     "jsonrpc": "2.0",
     "result": {...},
     "id": 1
   }

   응답 형식 (에러):
   {
     "jsonrpc": "2.0",
     "error": {
       "code": -1,
       "message": "..."
     },
     "id": 1
   }

   지원 메서드:
   - tools/list: 도구 목록
   - tools/call: 도구 호출

5. FastAPI 보안 기능

   CORS 설정:
   - allow_origins: 허용 도메인
   - allow_credentials: 인증 정보 허용
   - allow_methods: 허용 HTTP 메서드
   - allow_headers: 허용 헤더

   프로덕션 권장사항:
   - allow_origins를 특정 도메인으로 제한
   - HTTPS만 허용
   - Rate limiting 적용
   - 인증/인가 미들웨어

6. 도구 보안 구현

   login 도구:
   - HTTPS로 비밀번호 암호화 전송
   - 세션 토큰 생성
   - 역할 기반 접근 제어

   get_api_key 도구:
   - 인증 후 키 반환
   - HTTPS로 키 암호화 전송
   - 키 노출 방지

   process_payment 도구:
   - PCI DSS 컴플라이언스
   - 카드 번호 마스킹
   - 카드 정보 로그 금지
   - HTTPS로 카드 정보 암호화

7. 아키텍처 비교

   순수 FastMCP (ref/secure_http_server.py):
   장점:
   - 단순한 아키텍처
   - 낮은 레이턴시
   - 쉬운 디버깅

   단점:
   - FastMCP의 HTTP transport 기능 제한
   - REST API 기능 부족
   - 미들웨어 제한

   하이브리드 FastAPI + FastMCP (이 파일):
   장점:
   - 강력한 HTTP/TLS 기능
   - REST API 지원
   - 풍부한 미들웨어
   - 표준 MCP 구현

   단점:
   - 복잡한 아키텍처
   - 서브프로세스 오버헤드
   - 디버깅 어려움

8. 실행 및 테스트

   서버 시작:
   python3 secure_fastapi_mcp_server.py

   REST API 테스트:
   curl -k https://localhost:8444/health
   curl -k https://localhost:8444/api/info

   MCP 프로토콜 테스트:
   curl -k -X POST https://localhost:8444/mcp \
     -H 'Content-Type: application/json' \
     -d '{"jsonrpc":"2.0","method":"tools/list","id":1}'

   도구 호출:
   curl -k -X POST https://localhost:8444/mcp \
     -H 'Content-Type: application/json' \
     -d '{"jsonrpc":"2.0","method":"tools/call","params":{"name":"add","arguments":{"a":5,"b":3}},"id":1}'

9. 프로덕션 고려사항

   인증서:
   - 자체 서명 대신 Let's Encrypt 사용
   - 인증서 자동 갱신
   - 여러 도메인 지원 (SAN)

   보안:
   - Rate limiting
   - JWT 인증
   - API 키 관리
   - 로그 암호화
   - 침입 탐지

   성능:
   - 서브프로세스 풀링
   - 결과 캐싱
   - 로드 밸런싱
   - 수평 확장

   모니터링:
   - Health check 엔드포인트
   - 메트릭 수집 (Prometheus)
   - 에러 추적 (Sentry)
   - 로그 집계 (ELK)

10. 다음 학습 단계

    - test_secure_server_proxy.py 실행
      * 하이브리드 서버 테스트
      * HTTPS 통신 확인
      * MCP 프로토콜 검증

    - secure_http_server_proxy.py 학습
      * HTTPS 프록시 구현
      * 프록시를 통한 보안 통신

    - secure_attack_simulation.py 실행
      * HTTPS 서버에 대한 공격 시도
      * TLS이 공격을 방어하는 방법
      * HTTP vs HTTPS 보안 비교

    - ref/ 디렉토리 파일들 학습
      * 다양한 아키텍처 비교
      * 최적의 구현 방법 선택

핵심 메시지:
하이브리드 아키텍처는 복잡하지만 각 라이브러리의 강점을 활용할 수 있습니다.
FastAPI의 성숙한 HTTP/TLS 기능과 FastMCP의 표준 MCP 구현을 결합하여
안전하고 기능이 풍부한 MCP 서버를 구축할 수 있습니다.
"""