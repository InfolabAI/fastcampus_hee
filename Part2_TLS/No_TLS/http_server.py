#!/usr/bin/env python3
"""
===========================================
취약한 HTTP MCP 서버 (암호화 없음)
===========================================

강의 목적:
이 파일은 암호화되지 않은 HTTP 프로토콜로 민감한 데이터를 전송하는
취약한 MCP 서버를 구현합니다.

학습 포인트:
1. HTTP의 근본적인 보안 문제
2. 평문 전송의 위험성
3. 중간자 공격 (MITM) 취약점
4. 민감한 데이터의 종류
5. 보안 경고 메시지의 중요성

보안 문제:
1. HTTP는 암호화되지 않음
   - 모든 데이터가 평문으로 전송
   - 네트워크 스니핑으로 쉽게 도청 가능

2. 전송되는 민감한 데이터:
   - 사용자 비밀번호 (평문)
   - API 키 (평문)
   - 신용카드 정보 (평문)
   - 세션 토큰 (평문)

3. 공격 시나리오:
   - WiFi 도청
   - 네트워크 스니핑 (Wireshark, tcpdump)
   - 중간자 공격 (MITM)
   - ARP Spoofing
   - DNS Hijacking

비교:
- http_server.py: HTTP로 민감 데이터 전송 (이 파일) - 위험!
- secure_fastapi_mcp_server.py: HTTPS로 암호화된 전송 - 안전

핵심 메시지:
민감한 데이터는 절대 HTTP로 전송하면 안 됩니다!
HTTPS/TLS를 사용해야 합니다.
"""

# ===========================================
# 필요한 라이브러리 임포트
# ===========================================

import asyncio      # 비동기 프로그래밍
from fastmcp import FastMCP  # FastMCP 프레임워크
import hashlib      # 해시 함수 (세션 토큰 생성용)
import json         # JSON 데이터 처리
from datetime import datetime  # 타임스탬프

# ===========================================
# FastMCP 서버 초기화
# ===========================================

# FastMCP 서버 인스턴스를 생성합니다
# 이름: "VulnerableDataServer"
#
# 주의:
# 이 서버는 교육 목적으로 의도적으로 취약하게 만들어졌습니다.
# 실제 운영 환경에서는 절대 사용하지 마세요!
mcp = FastMCP("VulnerableDataServer")

# ===========================================
# 데모용 사용자 데이터베이스
# ===========================================

# 인메모리 사용자 데이터베이스
# 실제 환경에서는 암호화된 데이터베이스를 사용해야 함
#
# 포함된 민감한 정보:
# 1. password: 사용자 비밀번호 (평문 저장 - 나쁜 관행!)
# 2. api_key: API 액세스 키
# 3. role: 사용자 권한 수준
#
# 보안 문제:
# - 비밀번호가 평문으로 저장됨 (해시화해야 함)
# - API 키가 노출됨
# - 데이터베이스가 메모리에만 있음 (영속성 없음)
users_db = {
    "admin": {
        "password": "admin123",  # 평문 비밀번호 - 절대 안 됨!
        "api_key": "sk-1234567890abcdef",  # 민감한 API 키
        "role": "administrator"  # 관리자 권한
    },
    "user1": {
        "password": "password123",  # 평문 비밀번호 - 절대 안 됨!
        "api_key": "sk-abcdef1234567890",  # 민감한 API 키
        "role": "user"  # 일반 사용자 권한
    }
}

# ===========================================
# MCP 도구 함수들
# ===========================================

@mcp.tool()
async def add(a: int, b: int) -> int:
    """
    두 개의 정수를 더합니다.

    :param a: 첫 번째 숫자
    :param b: 두 번째 숫자
    :return: 두 숫자의 합

    보안 관점:
    이 함수는 민감한 데이터를 다루지 않으므로
    HTTP로 전송해도 큰 문제 없음

    하지만 다른 도구들과 같은 서버에서 실행되므로
    전체 서버를 HTTPS로 보호하는 것이 좋음
    """
    print(f"Executing add tool with: a={a}, b={b}")
    return a + b

@mcp.tool()
async def create_greeting(name: str) -> str:
    """
    주어진 이름으로 환영 메시지를 생성합니다.

    :param name: 인사할 사람의 이름
    :return: "Hello, {name}!..." 형태의 환영 메시지

    보안 관점:
    이 함수도 민감한 데이터를 다루지 않음

    하지만 name 매개변수가 HTTP로 전송되므로
    사용자의 개인 정보 (이름)가 노출될 수 있음
    """
    print(f"Executing create_greeting tool with: name={name}")
    return f"Hello, {name}! Welcome to the world of MCP."

@mcp.tool()
async def login(username: str, password: str) -> dict:
    """
    사용자명과 비밀번호로 사용자를 인증합니다.

    :param username: 사용자명
    :param password: 비밀번호 (평문으로 전송됨!)
    :return: 인증 결과와 세션 토큰

    심각한 보안 문제:
    1. 비밀번호가 HTTP로 평문 전송됨
       - 네트워크 스니핑으로 즉시 도청 가능
       - WiFi 환경에서 특히 위험
       - Wireshark 같은 도구로 쉽게 캡처

    2. 전송 예시 (평문):
       POST http://127.0.0.1:8000/mcp/tool/login
       {"username": "admin", "password": "admin123"}
       ↑ 이 내용이 그대로 네트워크를 통해 전송됨!

    3. 공격 시나리오:
       - 공용 WiFi에서 사용
       → 같은 WiFi의 공격자가 Wireshark 실행
       → 비밀번호 즉시 노출

    4. 세션 토큰도 평문 전송:
       - 세션 하이재킹 가능
       - 토큰을 훔쳐 다른 곳에서 사용 가능

    해결책:
    - HTTPS/TLS를 사용해야 함
    - 전송 계층 암호화 필수
    """
    print(f"⚠️  WARNING: Login attempt with credentials in plain text - username: {username}")

    if username in users_db and users_db[username]["password"] == password:
        # MD5로 세션 토큰 생성
        # 주의: MD5는 암호학적으로 안전하지 않음 (교육용으로만 사용)
        session_token = f"session_{hashlib.md5(f'{username}{datetime.now()}'.encode()).hexdigest()}"
        print(f"✅ Login successful for user: {username}")
        return {
            "success": True,
            "message": f"Login successful for user: {username}",
            "session_token": session_token,  # 이것도 평문으로 전송됨!
            "role": users_db[username]["role"],
            "warning": "⚠️  Credentials were transmitted over unencrypted HTTP!"
        }

    print(f"❌ Login failed for user: {username}")
    return {
        "success": False,
        "message": "Invalid username or password"
    }

@mcp.tool()
async def get_api_key(username: str, password: str) -> dict:
    """
    인증된 사용자의 API 키를 조회합니다.

    :param username: 사용자명
    :param password: 비밀번호
    :return: API 키 또는 오류 메시지

    심각한 보안 문제:
    1. API 키가 HTTP로 평문 전송됨
       - API 키는 장기간 사용되는 인증 수단
       - 한 번 노출되면 계속 악용 가능
       - 비밀번호보다 더 위험할 수 있음

    2. 전송 예시 (평문):
       응답: {"api_key": "sk-1234567890abcdef"}
       ↑ 이 API 키가 그대로 네트워크를 통해 전송됨!

    3. 공격 영향:
       - API 키 도청
       - 무제한 API 사용 (사용자 명의로)
       - 데이터 유출
       - 금전적 손실 (유료 API의 경우)

    4. 실제 사례:
       - OpenAI API 키 노출 사고
       - AWS 액세스 키 노출 사고
       - 수백만 원의 과금 피해

    해결책:
    - HTTPS/TLS 필수
    - API 키 rotation 정책
    - IP 화이트리스트
    - 사용량 제한
    """
    print(f"⚠️  WARNING: API key request with plain text credentials - username: {username}")

    if username in users_db and users_db[username]["password"] == password:
        api_key = users_db[username]["api_key"]
        print(f"🔑 API key retrieved for user: {username} - {api_key}")
        return {
            "success": True,
            "api_key": api_key,  # 민감한 API 키가 평문으로 전송됨!
            "warning": "⚠️  This API key is transmitted over unencrypted HTTP!"
        }

    return {
        "success": False,
        "message": "Authentication failed"
    }

@mcp.tool()
async def process_payment(card_number: str, cvv: str, amount: float, merchant: str) -> dict:
    """
    결제 트랜잭션을 처리합니다 (시뮬레이션만).

    :param card_number: 신용카드 번호
    :param cvv: CVV 코드
    :param amount: 결제 금액
    :param merchant: 가맹점명
    :return: 트랜잭션 결과

    극도로 심각한 보안 문제:
    1. 신용카드 정보가 HTTP로 평문 전송됨
       - 카드 번호 (전체)
       - CVV 코드
       - 이 정보만 있으면 온라인 결제 가능!

    2. 전송 예시 (평문):
       POST http://127.0.0.1:8000/mcp/tool/process_payment
       {
         "card_number": "1234567890123456",
         "cvv": "123",
         "amount": 100.00
       }
       ↑ 카드 정보가 그대로 전송됨!

    3. 법적 문제:
       - PCI DSS 위반 (Payment Card Industry Data Security Standard)
       - 개인정보보호법 위반
       - 형사 처벌 가능
       - 거액의 과징금

    4. 공격 영향:
       - 신용카드 도용
       - 부정 사용
       - 금전적 손실
       - 개인 신용 피해

    5. 실제 사례:
       - Target 카드 정보 유출 (4천만 건)
       - Home Depot 유출 (5천6백만 건)
       - 수조 원의 피해

    절대 금지:
    - 신용카드 정보는 절대 HTTP로 전송하면 안 됨
    - HTTPS/TLS는 최소한의 요구사항
    - PCI DSS 준수 필수
    - 결제 게이트웨이 사용 권장 (Stripe, PayPal 등)
    """
    print(f"💳 WARNING: Processing payment with plain text card details!")
    print(f"   Card Number: {card_number}")
    print(f"   CVV: {cvv}")
    print(f"   Amount: ${amount}")

    # 표시용으로 카드 번호 마스킹
    # 주의: 이미 네트워크에서 노출되었으므로 소용없음!
    masked_card = f"****-****-****-{card_number[-4:]}" if len(card_number) >= 4 else "****"

    # 트랜잭션 ID 생성
    transaction_id = f"txn_{hashlib.md5(f'{card_number}{datetime.now()}'.encode()).hexdigest()[:12]}"

    return {
        "success": True,
        "transaction_id": transaction_id,
        "amount": amount,
        "merchant": merchant,
        "card": masked_card,  # 응답에서는 마스킹하지만 의미 없음
        "timestamp": datetime.now().isoformat(),
        "warning": "⚠️  Credit card details transmitted in plain text over HTTP!"
    }


# ===========================================
# 서버 실행
# ===========================================

if __name__ == "__main__":
    """
    HTTP 서버를 시작합니다 (암호화되지 않음).

    실행 방법:
    python3 http_server.py

    또는 Docker 환경:
    make shell python3 Part2_SSL/No_TLS/http_server.py

    주의:
    - 이 서버는 교육 목적으로만 사용
    - 실제 환경에서는 절대 사용 금지!
    - 민감한 데이터가 평문으로 전송됨

    서버 정보:
    - 주소: http://127.0.0.1:8000
    - MCP 엔드포인트: http://127.0.0.1:8000/mcp
    - 프로토콜: HTTP (암호화 없음)

    다음 학습 단계:
    1. test_http_server_proxy.py: 정상 기능 테스트
    2. attack_simulation.py: 스니핑 공격 시뮬레이션
    3. secure_fastapi_mcp_server.py: HTTPS 버전 비교
    4. secure_attack_simulation.py: 암호화된 통신 검증
    """
    print("=" * 70)
    print("⚠️  취약한 HTTP 서버 시작 (교육용)")
    print("=" * 70)
    print()
    print("Starting MCP server on http://127.0.0.1:8000")
    print("MCP endpoint is available at http://127.0.0.1:8000/mcp")
    print()
    print("경고: 이 서버는 암호화되지 않은 HTTP를 사용합니다!")
    print("민감한 데이터가 평문으로 전송됩니다.")
    print("교육 목적으로만 사용하세요.")
    print("=" * 70)
    print()

    # FastMCP가 내부적으로 uvicorn과 같은 ASGI 서버를 사용하여 실행
    # transport="http": HTTP 프로토콜 사용 (암호화 없음)
    # host="127.0.0.1": 로컬호스트에만 바인딩
    # port=8000: 포트 8000 사용
    mcp.run(transport="http", host="127.0.0.1", port=8000)


# ===========================================
# 학습 정리
# ===========================================
"""
이 파일에서 배운 내용:

1. HTTP의 근본적인 보안 문제
   - HTTP는 암호화되지 않은 프로토콜
   - 모든 데이터가 평문으로 전송
   - OSI 7계층 중 응용 계층 프로토콜
   - 전송 계층에서 암호화 없음

2. 민감한 데이터의 종류
   Level 1 (가장 위험):
   - 신용카드 정보 (카드 번호, CVV)
   - 비밀번호 (평문)
   - 주민등록번호, 여권번호

   Level 2 (매우 위험):
   - API 키, 액세스 토큰
   - 세션 토큰
   - OAuth 토큰

   Level 3 (위험):
   - 이메일 주소
   - 전화번호
   - 주소

   Level 4 (주의 필요):
   - 사용자명
   - 이름
   - 일반 개인 정보

3. HTTP 평문 전송의 위험성
   전송 흐름:
   클라이언트 → 네트워크 (WiFi/라우터/ISP) → 서버

   각 지점에서 도청 가능:
   1. 로컬 네트워크: WiFi 패킷 스니핑
   2. 라우터: 라우터 해킹, ARP Spoofing
   3. ISP: 네트워크 모니터링
   4. 중간 노드: 중간자 공격 (MITM)

4. 공격 도구 및 방법
   패킷 스니핑:
   - Wireshark: GUI 기반 패킷 분석 도구
   - tcpdump: CLI 기반 패킷 캡처
   - tshark: Wireshark의 CLI 버전

   중간자 공격 (MITM):
   - ARP Spoofing: arpspoof, ettercap
   - DNS Hijacking: DNS 응답 조작
   - TLS Stripping: HTTPS → HTTP 다운그레이드

5. 실제 공격 시나리오
   시나리오 1: 공용 WiFi 공격
   1. 공격자가 같은 WiFi 네트워크 접속
   2. Wireshark 실행, 패킷 캡처 시작
   3. 피해자가 HTTP 로그인
   4. 공격자가 비밀번호 즉시 확인
   5. 피해자 계정 탈취

   시나리오 2: 중간자 공격
   1. 공격자가 ARP Spoofing 실행
   2. 네트워크 트래픽이 공격자를 경유
   3. 모든 HTTP 통신 도청
   4. 비밀번호, API 키 수집
   5. 대규모 계정 탈취

6. 법적 및 규제 문제
   PCI DSS (Payment Card Industry Data Security Standard):
   - 신용카드 정보 처리 시 필수 준수
   - HTTP는 PCI DSS 위반
   - HTTPS/TLS 필수

   개인정보보호법:
   - 개인정보의 안전한 전송 의무
   - 평문 전송은 법 위반
   - 과징금 및 형사 처벌

   GDPR (유럽 일반 데이터 보호 규정):
   - 데이터 전송 시 암호화 필수
   - 위반 시 최대 전 세계 매출의 4% 과징금

7. 해결책: HTTPS/TLS
   HTTPS = HTTP + TLS
   - 전송 계층 암호화
   - 데이터 기밀성 보장
   - 서버 인증
   - 데이터 무결성 검증

   TLS 작동 원리:
   1. 클라이언트가 서버에 연결 요청
   2. 서버가 인증서 전송
   3. 클라이언트가 인증서 검증
   4. 대칭키 교환 (비대칭키 암호화 사용)
   5. 이후 모든 통신은 대칭키로 암호화

8. 비교 학습
   http_server.py (이 파일):
   - Protocol: HTTP
   - Port: 8000
   - Encryption: 없음
   - 보안 수준: 매우 낮음
   - 용도: 교육용만

   secure_fastapi_mcp_server.py:
   - Protocol: HTTPS
   - Port: 8443
   - Encryption: TLS 1.2 이상
   - 보안 수준: 높음
   - 용도: 실제 운영 가능

9. 다음 학습 단계
   - test_http_server_proxy.py: 정상 기능 확인
   - attack_simulation.py: 실제 스니핑 공격 시뮬레이션
   - secure_fastapi_mcp_server.py: HTTPS 구현
   - certificate_management.py: 인증서 관리
   - secure_attack_simulation.py: HTTPS 보안 검증

핵심 메시지:
민감한 데이터는 절대 HTTP로 전송하지 마세요!

HTTP: 평문 전송 → 도청 가능 → 매우 위험
HTTPS: 암호화 전송 → 도청 불가 → 안전

HTTPS/TLS는 선택이 아닌 필수입니다!
"""
