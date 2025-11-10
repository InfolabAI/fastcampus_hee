#!/usr/bin/env python3
"""
===========================================
HTTP 보안 취약점 공격 시뮬레이션 (통합 버전)
===========================================

강의 목적:
이 파일은 암호화되지 않은 HTTP 통신의 3가지 주요 보안 위험을
실제로 시연하는 교육용 공격 시뮬레이션입니다.

중요:
이 코드는 오직 교육 목적으로만 사용되어야 합니다.
실제 시스템에 대한 무단 공격은 불법이며,
컴퓨터범죄처벌법 위반으로 처벌받을 수 있습니다!

학습 포인트:
1. 네트워크 스니핑 공격
   - HTTP 트래픽에서 민감한 데이터 노출 시연
   - 평문 전송의 위험성 이해
   - 패킷 캡처 도구 사용법

2. 중간자 공격 (MITM - Man In The Middle)
   - 트래픽 가로채기 및 분석
   - 데이터 변조 및 주입
   - 통신 제어권 탈취

3. 무단 접근 공격
   - 인증 없는 HTTP MCP 서버 공격
   - 악의적 입력 및 리소스 남용
   - 서비스 거부 공격 가능성

시연할 공격들:
1. 네트워크 스니핑
   - login() 호출에서 비밀번호 탈취
   - get_api_key() 호출에서 API 키 탈취
   - process_payment() 호출에서 신용카드 정보 탈취

2. MITM 공격
   - 프록시 서버로 트래픽 중계
   - 결제 금액 변조 (10배 증가)
   - 요청/응답 실시간 분석

3. 무단 접근
   - 도구 목록 획득
   - 대용량 계산으로 CPU 남용
   - XSS/SQLi 공격 시도

실행 전 준비:
1. http_server.py가 실행 중이어야 함:
   python3 http_server.py

2. 선택사항: tcpdump로 실제 트래픽 캡처
   sudo tcpdump -i lo -A -s 0 'tcp port 8000'

비교:
- test_http_server_proxy.py: 정상 사용자 동작
- attack_simulation.py: 악의적 공격자 동작 (이 파일)
- 둘 다 같은 HTTP 트래픽을 생성하지만 의도가 다름!
"""

# ===========================================
# 필요한 라이브러리 임포트
# ===========================================

import asyncio     # 비동기 프로그래밍
import json         # JSON 데이터 처리
from datetime import datetime  # 타임스탬프
import socket       # 소켓 프로그래밍 (서버 상태 확인용)
from fastmcp import Client  # FastMCP 클라이언트

# ===========================================
# NetworkSniffer 클래스: 네트워크 스니핑 시뮬레이터
# ===========================================

class NetworkSniffer:
    """
    네트워크 트래픽을 캡처하고 분석하는 시뮬레이터

    실제 공격 도구:
    - Wireshark: GUI 기반 패킷 분석
    - tcpdump: CLI 기반 패킷 캡처
    - tshark: Wireshark의 CLI 버전
    - Ettercap: MITM 공격 및 스니핑

    이 클래스가 시뮬레이션하는 것:
    - 네트워크 인터페이스에서 패킷 캡처
    - HTTP 요청/응답 분석
    - 민감한 데이터 추출
    - 실시간 모니터링

    실제 공격 시나리오:
    1. 공격자가 공개 WiFi에서 tcpdump 실행
    2. 피해자가 HTTP 사이트에 로그인
    3. 비밀번호가 평문으로 전송됨
    4. 공격자가 패킷을 캡처하여 비밀번호 획득

    방어 방법:
    - HTTPS/TLS 사용으로 모든 데이터 암호화
    - VPN 사용으로 전체 트래픽 터널링
    - 공개 WiFi 사용 시 주의
    """

    def __init__(self):
        """
        스니퍼 초기화

        실제 도구에서는:
        - 네트워크 인터페이스 선택 (eth0, wlan0 등)
        - 프로미스큐어스 모드 활성화
        - 패킷 필터 설정 (BPF - Berkeley Packet Filter)
        """
        self.captured_data = []  # 캡처된 패킷 저장
        self.sniffing = False     # 스니핑 활성화 여부

    def start_sniffing(self):
        """
        네트워크 스니핑 시작

        실제 공격에서는:
        tcpdump -i wlan0 -A -s 0 'tcp port 80 or tcp port 8000'

        -i wlan0: 무선 인터페이스 선택
        -A: ASCII로 패킷 내용 출력
        -s 0: 전체 패킷 캡처 (잘리지 않음)
        'tcp port 80': HTTP 트래픽만 필터링
        """
        self.sniffing = True
        print("\n🔍 네트워크 스니핑 시작...")

    def stop_sniffing(self):
        """
        네트워크 스니핑 중지

        실제 도구에서는:
        - Ctrl+C로 캡처 중지
        - 캡처된 패킷을 파일로 저장
        - 통계 정보 출력
        """
        self.sniffing = False
        print("\n🛑 네트워크 스니핑 중지")

    def intercept_http_request(self, method, url, headers, data):
        """
        HTTP 요청 가로채기 시뮬레이션

        실제 공격에서는:
        1. 네트워크 인터페이스를 프로미스큐어스 모드로 설정
           (모든 패킷을 캡처, 자신에게 온 것만이 아닌)
        2. TCP 패킷을 캡처
        3. HTTP 프로토콜 파싱
        4. 요청 본문(body) 추출

        공격 가능한 환경:
        - 공개 WiFi (카페, 공항, 호텔)
        - 같은 네트워크의 다른 컴퓨터
        - 라우터/스위치에 접근 가능한 경우
        - ARP 스푸핑으로 트래픽 리다이렉트

        파라미터:
        - method: HTTP 메서드 (GET, POST 등)
        - url: 요청 URL
        - headers: HTTP 헤더들
        - data: 요청 본문 (민감한 데이터 포함)
        """
        if not self.sniffing:
            return

        # 타임스탬프 기록 (포렌식 분석용)
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # 캡처된 데이터 구조화
        # 실제 패킷 캡처에서는 훨씬 더 많은 정보 포함:
        # - IP 주소 (출발지/목적지)
        # - MAC 주소
        # - TCP 시퀀스 번호
        # - 전체 HTTP 헤더
        intercepted = {
            "timestamp": timestamp,
            "method": method,
            "url": url,
            "headers": headers,
            "data": data
        }

        self.captured_data.append(intercepted)

        # 실시간 모니터링 출력
        print(f"\n📡 [INTERCEPTED] {timestamp}")
        print(f"   Method: {method}")
        print(f"   URL: {url}")

        # ===========================================
        # 민감한 데이터 하이라이트
        # ===========================================
        # 공격자는 특정 키워드를 검색하여 민감한 정보 추출
        # grep 패턴: password|api|key|card|cvv|ssn|token

        if data:
            print("   🚨 평문 데이터 캡처:")
            if isinstance(data, dict):
                for key, value in data.items():
                    # 민감한 키워드 탐지
                    # 실제 공격에서는 정규표현식 사용:
                    # - 신용카드: \d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}
                    # - 이메일: [a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}
                    # - API 키: sk-[a-zA-Z0-9]{48}
                    if any(sensitive in str(key).lower() for sensitive in ['password', 'card', 'cvv', 'api']):
                        print(f"      ⚠️  {key}: {value}")
                    else:
                        print(f"      {key}: {value}")
            else:
                print(f"      {data}")
                
    def analyze_captured_data(self):
        """
        캡처된 데이터 분석 및 민감한 정보 추출

        실제 공격에서의 분석 과정:
        1. 패킷 필터링: HTTP 트래픽만 선택
        2. 프로토콜 파싱: HTTP 헤더와 본문 분리
        3. 패턴 매칭: 정규표현식으로 민감한 데이터 탐지
        4. 데이터 추출: 구조화된 형태로 저장
        5. 보고서 생성: 공격자가 활용 가능한 형태로 정리

        분석 도구:
        - Wireshark의 분석 기능
        - Python 스크립트 (scapy, dpkt)
        - grep, awk, sed (텍스트 처리)
        """
        print("\n\n📊 캡처된 민감한 데이터 분석")
        print("=" * 60)

        # 민감한 데이터 분류
        # 실제 공격에서는 데이터베이스에 저장하여 나중에 활용
        passwords = []      # 로그인 정보
        api_keys = []       # API 키 (현재 미사용, 확장 가능)
        card_numbers = []   # 신용카드 정보

        # 캡처된 모든 패킷 순회
        for packet in self.captured_data:
            data = packet.get("data", {})
            if isinstance(data, dict):
                # MCP JSON-RPC 요청에서 파라미터 추출
                # 구조: {"jsonrpc": "2.0", "method": "tools/call",
                #        "params": {"name": "tool_name", "arguments": {...}}}
                params = data.get("params", {})
                if isinstance(params, dict):
                    tool_name = params.get("name", "")
                    arguments = params.get("arguments", {})

                    # ===========================================
                    # 로그인 정보 추출
                    # ===========================================
                    if tool_name == "login" and isinstance(arguments, dict):
                        # login() 도구 호출에서 비밀번호 추출
                        # 실제 서비스: 은행, 이메일, SNS 등
                        passwords.append({
                            "time": packet["timestamp"],
                            "username": arguments.get("username", "unknown"),
                            "password": arguments.get("password", "unknown")
                        })

                    # ===========================================
                    # API 키 요청 추출
                    # ===========================================
                    elif tool_name == "get_api_key" and isinstance(arguments, dict):
                        # get_api_key() 도구 호출에서 인증 정보 추출
                        # API 키는 응답에 있지만, 인증 정보도 민감함
                        passwords.append({
                            "time": packet["timestamp"],
                            "username": arguments.get("username", "unknown"),
                            "password": arguments.get("password", "unknown")
                        })

                    # ===========================================
                    # 신용카드 정보 추출
                    # ===========================================
                    elif tool_name == "process_payment" and isinstance(arguments, dict):
                        # process_payment() 도구 호출에서 카드 정보 추출
                        # 실제: 온라인 쇼핑, 결제 API 등
                        card_numbers.append({
                            "time": packet["timestamp"],
                            "card": arguments.get("card_number", "unknown"),
                            "cvv": arguments.get("cvv", "unknown"),
                            "amount": arguments.get("amount", "unknown")
                        })

        # ===========================================
        # 추출된 민감한 데이터 출력
        # ===========================================

        if passwords:
            print("\n🔓 노출된 로그인 정보:")
            for p in passwords:
                print(f"   시간: {p['time']}")
                print(f"   사용자: {p['username']}")
                print(f"   비밀번호: {p['password']}")
                print()
                # 실제 공격에서는:
                # - 데이터베이스에 저장
                # - 다른 서비스에서 같은 비밀번호 재사용 시도
                # - 피싱 공격에 활용

        if card_numbers:
            print("\n💳 노출된 신용카드 정보:")
            for c in card_numbers:
                print(f"   시간: {c['time']}")
                print(f"   카드번호: {c['card']}")
                print(f"   CVV: {c['cvv']}")
                print(f"   금액: ${c['amount']}")
                print()
                # 실제 공격에서는:
                # - 다크웹에 판매
                # - 직접 사용하여 물품 구매
                # - 피싱 사이트 제작에 활용

        # 통계 정보
        print(f"\n📈 총 캡처된 패킷: {len(self.captured_data)}")
        print(f"   - 로그인 시도: {len(passwords)}")
        print(f"   - 결제 정보: {len(card_numbers)}")

# ===========================================
# 글로벌 스니퍼 인스턴스
# ===========================================
sniffer = NetworkSniffer()

# ===========================================
# 사용자 트래픽 시뮬레이션
# ===========================================

async def simulate_user_traffic(base_url="http://127.0.0.1:8000/mcp"):
    """사용자 트래픽 시뮬레이션 - FastMCP Client 사용"""
    print("\n👤 사용자 활동 시뮬레이션...")

    client = Client(base_url)

    try:
        async with client:
            # 1. 로그인 시도
            print("\n1️⃣ 사용자 로그인...")
            sniffer.intercept_http_request(
                "POST", base_url,
                {"Content-Type": "application/json"},
                {
                    "params": {
                        "name": "login",
                        "arguments": {"username": "admin", "password": "admin123"}
                    }
                }
            )

            try:
                result = await client.call_tool("login", {
                    "username": "admin",
                    "password": "admin123"
                })
                print(f"   📡 요청 전송됨 (성공)")
                print("   ✅ 로그인 성공!")
                print(f"   응답: {str(result)[:100]}...")
                print("   ⚠️  민감한 로그인 정보가 평문으로 네트워크에 노출되었습니다!")
            except Exception as e:
                print(f"   📡 요청 시도됨 (오류: {type(e).__name__})")
                print("   ⚠️  민감한 로그인 정보가 평문으로 네트워크에 노출되었습니다!")

            await asyncio.sleep(1)

            # 2. API 키 조회
            print("\n2️⃣ API 키 조회...")
            sniffer.intercept_http_request(
                "POST", base_url,
                {"Content-Type": "application/json"},
                {
                    "params": {
                        "name": "get_api_key",
                        "arguments": {"username": "user1", "password": "password123"}
                    }
                }
            )

            try:
                result = await client.call_tool("get_api_key", {
                    "username": "user1",
                    "password": "password123"
                })
                print(f"   📡 요청 전송됨 (성공)")
                print("   ✅ API 키 조회 성공!")
                print(f"   응답: {str(result)[:100]}...")
                print("   ⚠️  사용자 크리덴셜이 평문으로 네트워크에 노출되었습니다!")
            except Exception as e:
                print(f"   📡 요청 시도됨 (오류: {type(e).__name__})")
                print("   ⚠️  사용자 크리덴셜이 평문으로 네트워크에 노출되었습니다!")

            await asyncio.sleep(1)

            # 3. 결제 처리
            print("\n3️⃣ 결제 처리...")
            sniffer.intercept_http_request(
                "POST", base_url,
                {"Content-Type": "application/json"},
                {
                    "params": {
                        "name": "process_payment",
                        "arguments": {
                            "card_number": "4532-1234-5678-9012",
                            "cvv": "123",
                            "amount": 99.99,
                            "merchant": "Online Store"
                        }
                    }
                }
            )

            try:
                result = await client.call_tool("process_payment", {
                    "card_number": "4532-1234-5678-9012",
                    "cvv": "123",
                    "amount": 99.99,
                    "merchant": "Online Store"
                })
                print(f"   📡 요청 전송됨 (성공)")
                print("   ✅ 결제 처리 성공!")
                print(f"   응답: {str(result)[:100]}...")
                print("   ⚠️  신용카드 정보가 평문으로 네트워크에 노출되었습니다!")
            except Exception as e:
                print(f"   📡 요청 시도됨 (오류: {type(e).__name__})")
                print("   ⚠️  신용카드 정보가 평문으로 네트워크에 노출되었습니다!")

    except Exception as e:
        print(f"❌ 클라이언트 연결 실패: {e}")

async def simulate_unauthorized_access():
    """무단 접근 공격 시뮬레이션 - FastMCP Client 사용"""
    print("\n\n🚨 3단계: 무단 접근 공격 시뮬레이션")
    print("=" * 60)
    print("공격자가 인증 없이 HTTP MCP 서버에 직접 접근을 시도합니다.")

    base_url = "http://127.0.0.1:8000/mcp"
    client = Client(base_url)

    try:
        async with client:
            # 서버 탐지 및 연결
            print("\n🔍 서버 탐지 중...")
            await client.ping()
            print("✅ 타겟 서버 발견! (인증 없이 접근 가능)")

            # 도구 목록 획득 시도
            print("\n📋 사용 가능한 도구 탐색...")
            tools = await client.list_tools()
            print(f"✅ {len(tools)}개 도구 발견:")
            for tool in tools:
                print(f"   - {tool.name}: {tool.description}")
            print("⚠️  공격자가 모든 도구에 무제한 접근 가능!")

            # 악의적 기능 남용
            print("\n💀 악의적 기능 남용 시도...")
            malicious_requests = [
                {
                    "name": "add",
                    "arguments": {"a": 999999999, "b": 999999999},
                    "description": "대용량 계산으로 CPU 자원 남용"
                },
                {
                    "name": "create_greeting",
                    "arguments": {"name": "<script>alert('XSS')</script>"},
                    "description": "XSS 공격 시도"
                },
                {
                    "name": "create_greeting",
                    "arguments": {"name": "'; DROP TABLE users; --"},
                    "description": "SQL 인젝션 시도"
                }
            ]

            attack_success_count = 0
            for req in malicious_requests:
                try:
                    result = await client.call_tool(req["name"], req["arguments"])
                    attack_success_count += 1
                    print(f"   {req['description']}: 성공")
                    print(f"     ⚠️  공격 성공 - 서버가 악의적 요청을 처리함!")
                    print(f"     결과: {str(result)[:100]}...")
                except Exception as e:
                    print(f"   {req['description']}: 실패 ({type(e).__name__})")

            print("\n🎯 무단 접근 공격 결과:")
            print("   ✅ 인증 없이 서버 접근 성공")
            print(f"   ✅ 모든 기능에 무제한 접근 가능")
            if attack_success_count > 0:
                print(f"   ⚠️  악의적 요청 {attack_success_count}개 성공 - 서버가 입력 검증 없이 처리!")
            else:
                print(f"   ℹ️  악의적 요청은 타입 검증으로 차단됨 (하지만 인증은 여전히 없음!)")
            print("   ⚠️  심각한 보안 취약점 확인!")

    except Exception as e:
        print(f"❌ 서버 접근 실패: {e}")
        print("   MCP 서버가 실행되지 않음 (실제로는 보안상 좋은 상황)")

def check_server_running(host="127.0.0.1", port=8000):
    """서버가 실행 중인지 확인"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)
        result = sock.connect_ex((host, port))
        sock.close()
        return result == 0
    except:
        return False

def show_tcpdump_guide():
    """tcpdump 사용 가이드 표시"""
    print("\n📖 실제 네트워크 트래픽 캡처 가이드")
    print("=" * 60)
    print("다른 터미널에서 다음 명령어를 실행하여 실제 트래픽을 캡처할 수 있습니다:")
    print()
    print("1. 직접 서버 트래픽 캡처:")
    print("   sudo tcpdump -i lo -A -s 0 'tcp port 8000' -w http_traffic.pcap")
    print()
    print("2. MITM 프록시 트래픽 캡처:")
    print("   sudo tcpdump -i lo -A -s 0 'tcp port 8888' -w mitm_traffic.pcap")
    print()
    print("3. 캡처된 트래픽 분석:")
    print("   tcpdump -r http_traffic.pcap -A | grep -E 'password|api_key|card_number'")
    print()
    print("💡 팁: HTTP 트래픽은 평문이므로 모든 데이터가 그대로 노출됩니다!")
    print("=" * 60)

async def run_sniffing_demo():
    """네트워크 스니핑 데모"""
    print("\n🔍 1단계: 네트워크 스니핑 데모")
    print("=" * 60)
    print("HTTP 통신에서 민감한 데이터가 평문으로 노출되는 것을 시연합니다.")
    
    # 스니핑 시작
    sniffer.start_sniffing()
    
    # 정상 트래픽 시뮬레이션
    await simulate_user_traffic()
    
    # 스니핑 중지
    sniffer.stop_sniffing()
    
    # 캡처된 데이터 분석
    sniffer.analyze_captured_data()
    
    print("\n✅ 스니핑 데모 완료 - 모든 HTTP 데이터가 평문으로 노출됨을 확인했습니다!")

async def run_mitm_demo():
    """MITM 공격 데모 - 개념 설명"""
    print("\n\n🕵️ 2단계: 중간자 공격(MITM) 개념 데모")
    print("=" * 60)
    print("HTTP 통신에서 MITM 공격이 가능한 이유를 설명합니다.")

    print("\n💡 MITM 공격 작동 원리:")
    print("   1. 공격자가 네트워크 경로에 프록시 서버를 설치")
    print("   2. ARP 스푸핑/DNS 스푸핑으로 트래픽을 프록시로 유도")
    print("   3. 프록시가 모든 요청/응답을 가로채고 분석")
    print("   4. 데이터 변조 후 전달 (피해자는 인지 불가)")

    print("\n🎯 HTTP에서 가능한 MITM 공격:")
    print("   ✅ 비밀번호 탈취 - 평문으로 전송되므로 즉시 노출")
    print("   ✅ 세션 토큰 탈취 - 로그인 상태 하이재킹")
    print("   ✅ 결제 금액 변조 - $100 → $1000으로 변경 가능")
    print("   ✅ 응답 변조 - 악성 스크립트/멀웨어 주입")
    print("   ✅ 데이터 수집 - 모든 API 키, 개인정보 저장")

    print("\n🔍 실제 공격 예시:")
    print("   피해자: login(username='admin', password='admin123')")
    print("   → 프록시 가로챔: {'username': 'admin', 'password': 'admin123'}")
    print("   → 공격자 저장: admin:admin123")
    print("   → 서버로 전달: (정상 처리됨)")
    print("   → 피해자: (공격당한 사실을 모름)")

    print("\n💳 결제 변조 예시:")
    print("   피해자: process_payment(amount=99.99)")
    print("   → 프록시 변조: amount=999.99 (10배 증가!)")
    print("   → 서버 처리: $999.99 결제 완료")
    print("   → 피해자: $99.99 결제했다고 착각")

    print("\n⚠️  HTTP의 근본적 문제:")
    print("   - 암호화 없음 → 모든 데이터 평문 노출")
    print("   - 인증 없음 → 중간자 존재 탐지 불가")
    print("   - 무결성 보장 없음 → 변조 탐지 불가")

    print("\n✅ HTTPS/TLS 방어 메커니즘:")
    print("   - 종단간 암호화 → 프록시가 내용 해독 불가")
    print("   - 인증서 검증 → 중간자 탐지 가능")
    print("   - 무결성 검증 → 변조 즉시 감지")

    print("\n✅ MITM 개념 데모 완료!")

async def main():
    """메인 실행 함수"""
    print("🔓 HTTP 보안 취약점 공격 시뮬레이션")
    print("=" * 60)
    print("이 데모는 암호화되지 않은 HTTP 통신의 위험성을 보여줍니다.")
    print("1. 네트워크 스니핑: 평문 데이터 노출")
    print("2. MITM 공격: 트래픽 가로채기 및 변조")
    print("3. 무단 접근: 인증 없는 서버 공격")
    
    # MCP 서버 상태 확인
    print("\n🔍 MCP 서버 연결 확인 중...")
    if check_server_running():
        print("✅ MCP 서버가 실행 중입니다.")
    else:
        print("⚠️  MCP 서버가 실행되지 않습니다.")
        print("   일부 기능은 시뮬레이션으로만 동작합니다.")
        print("   실제 서버 테스트를 원하시면 다음 명령을 실행하세요:")
        print("   python3 http_server.py")
    
    # tcpdump 가이드 표시
    show_tcpdump_guide()
    
    print("\n⏳ 3초 후 공격 시뮬레이션을 시작합니다...")
    await asyncio.sleep(3)
    
    try:
        # 1단계: 네트워크 스니핑 데모
        await run_sniffing_demo()
        
        # 2단계: MITM 공격 데모
        await run_mitm_demo()
        
        # 3단계: 무단 접근 공격
        await simulate_unauthorized_access()
        
        # 전체 요약
        print("\n\n🚨 HTTP 통신 보안 위험 요약")
        print("=" * 60)
        print("1. 네트워크 스니핑")
        print("   - 모든 HTTP 트래픽을 실시간으로 모니터링 가능")
        print("   - 민감한 데이터(비밀번호, 카드정보 등) 탈취 가능")
        print("   - 피해자는 공격을 인지하지 못함")
        print()
        print("2. 중간자 공격(MITM)")
        print("   - 요청/응답 데이터를 임의로 변조 가능")
        print("   - 결제 금액 변조, 악성 응답 주입 등")
        print("   - 완전한 통신 제어권 획득")
        print()
        print("3. 무단 접근")
        print("   - 인증 없이 모든 서버 기능에 접근")
        print("   - 악의적 입력 및 리소스 남용")
        print("   - 서비스 거부 공격(DoS) 가능")
        print()
        print("✅ 해결책: HTTPS/TLS + 인증 시스템")
        print("   - 모든 데이터 암호화 전송 (TLS)")
        print("   - 서버 인증으로 MITM 방어 (TLS)")
        print("   - 사용자 인증으로 무단 접근 방지 (JWT/OAuth)")
        print("   - 데이터 무결성 보장 (TLS)")
        
    except KeyboardInterrupt:
        print("\n🛑 시뮬레이션이 사용자에 의해 중단되었습니다.")
    except Exception as e:
        print(f"\n❌ 시뮬레이션 중 오류 발생: {e}")

if __name__ == "__main__":
    """
    공격 시뮬레이션 실행

    실행 방법:
    1. 먼저 HTTP 서버 시작:
       Terminal 1: python3 http_server.py

    2. 공격 시뮬레이션 실행:
       Terminal 2: python3 attack_simulation.py

    3. 선택사항: 실제 트래픽 캡처
       Terminal 3: sudo tcpdump -i lo -A -s 0 'tcp port 8000'

    또는 Docker 환경:
    make shell python3 Part2_SSL/No_TLS/attack_simulation.py

    기대 결과:
    - 1단계: 네트워크 스니핑으로 평문 데이터 노출 확인
    - 2단계: MITM 공격으로 데이터 변조 시연
    - 3단계: 무단 접근으로 인증 없는 서버 공격 확인
    """
    asyncio.run(main())


# ===========================================
# 종합 학습 정리
# ===========================================
"""
이 파일에서 배운 내용:

1. 네트워크 스니핑 공격

   공격 메커니즘:
   - 네트워크 인터페이스를 프로미스큐어스 모드로 설정
   - 모든 네트워크 패킷 캡처
   - HTTP 트래픽 필터링 및 분석
   - 민감한 데이터 추출

   실제 도구:
   - tcpdump: sudo tcpdump -i eth0 -A -s 0 'tcp port 80'
   - Wireshark: GUI로 패킷 분석
   - tshark: Wireshark의 CLI 버전
   - Ettercap: MITM + 스니핑

   추출 가능한 데이터:
   - HTTP 요청/응답 전체
   - 로그인 정보 (username, password)
   - API 키 (Authorization 헤더)
   - 신용카드 정보
   - 세션 쿠키/토큰
   - 개인정보 (이름, 주소, 전화번호)

   공격 가능 환경:
   - 공개 WiFi (카페, 공항, 호텔)
   - 같은 LAN의 다른 컴퓨터
   - ISP 레벨 (정부/통신사)
   - 라우터/스위치 해킹

2. 중간자 공격 (MITM)

   공격 메커니즘:
   - 클라이언트와 서버 사이에 프록시 서버 설치
   - 양쪽 트래픽을 모두 중계하며 감청/변조
   - 피해자는 정상 통신이라고 착각

   MITM 구축 방법:
   - ARP 스푸핑: 같은 네트워크에서 MAC 주소 속이기
   - DNS 스푸핑: DNS 응답 조작으로 잘못된 서버 연결
   - DHCP 스푸핑: DHCP 서버 역할 수행
   - 악성 WiFi AP: 공격자가 운영하는 WiFi
   - BGP 하이재킹: 라우팅 프로토콜 조작

   변조 가능한 항목:
   - 요청 데이터 (파라미터 변경)
   - 응답 데이터 (악성 스크립트 주입)
   - 결제 금액 (이 예제에서 시연)
   - 다운로드 파일 (멀웨어 주입)

   실제 도구:
   - Bettercap: bettercap -iface eth0
   - mitmproxy: mitmproxy --mode transparent
   - Burp Suite: 웹 프록시 + 인터셉터

3. 무단 접근 공격

   공격 단계:
   1. 서버 탐지 (포트 스캐닝)
   2. 인증 우회 확인
   3. 도구 목록 획득
   4. 악의적 기능 남용

   공격 유형:
   - 리소스 남용 (CPU, 메모리, 디스크)
   - 서비스 거부 공격 (DoS)
   - 데이터 탈취
   - 악의적 입력 (XSS, SQLi)

   인증이 없을 때의 위험:
   - 누구나 모든 기능 접근 가능
   - Rate Limiting 없음
   - 감사 로깅 없음
   - 공격 추적 불가능

4. HTTP vs HTTPS 보안 비교

   HTTP (이 예제):
   - 모든 데이터 평문 전송
   - 스니핑 가능
   - MITM 가능
   - 데이터 무결성 보장 없음

   HTTPS:
   - TLS로 모든 데이터 암호화
   - 스니핑해도 해독 불가
   - MITM 시도 시 인증서 오류 발생
   - 데이터 무결성 보장 (해시)

   암호화 효과:
   - 평문: "password: admin123" → 그대로 노출
   - 암호화: "Hs7$k2@mP..." → 해독 불가능

5. 실제 공격 사례

   Target 카드 정보 유출 (2013):
   - 4천만 개 카드 정보 유출
   - 네트워크 트래픽 모니터링으로 수집
   - 암호화되지 않은 내부 통신 악용

   WiFi 스니핑 사건 (지속적):
   - 공개 WiFi에서 HTTP 트래픽 캡처
   - 이메일, 비밀번호, 쿠키 수집
   - 계정 탈취 및 신원 도용

   MITM 공격 사례:
   - 국가 레벨: 중국 Great Firewall
   - ISP 레벨: 광고 주입
   - 공항 WiFi: 피싱 페이지 주입

6. 법적 책임

   이런 공격은 불법입니다:
   - 컴퓨터범죄처벌법 위반
   - 통신비밀보호법 위반
   - 개인정보보호법 위반

   처벌:
   - 징역 3년 이상
   - 벌금 수억 원
   - 민사 손해배상

   합법적 사용:
   - 자신의 시스템 테스트
   - 명시적 허가 받은 모의해킹
   - 교육 목적 시뮬레이션 (이 예제)

7. 방어 메커니즘

   기본 방어:
   - HTTPS/TLS 사용 (필수!)
   - 인증 시스템 (JWT, OAuth)
   - Rate Limiting
   - 입력 검증

   고급 방어:
   - Certificate Pinning: 특정 인증서만 신뢰
   - HSTS: Strict-Transport-Security 헤더
   - HPKP: Public Key Pinning
   - 네트워크 격리 (VLAN)

   모니터링:
   - IDS/IPS: 침입 탐지/방지 시스템
   - 트래픽 분석
   - 이상 탐지
   - 로그 감사

8. 다음 학습 단계

   - secure_fastapi_mcp_server.py 학습
     * HTTPS 사용으로 암호화
     * 인증서 설정 (certificate_management.py)
     * 동일한 공격 시도 시 실패 확인

   - secure_attack_simulation.py 실행
     * HTTPS 트래픽 스니핑 시도
     * 암호화된 데이터 확인
     * MITM 공격 실패 확인

   - TLS 프로토콜 이해
     * 핸드셰이크 과정
     * 인증서 검증
     * 암호화 알고리즘

핵심 메시지:
HTTP는 기본적으로 안전하지 않습니다!
모든 민감한 데이터 전송에는 HTTPS/TLS를 사용해야 합니다!
"나는 공격받지 않을 것"이라는 생각은 위험합니다!
"""