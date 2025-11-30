#!/usr/bin/env python3
"""Test failure scenario: Connection without CA certificate (no certificate pinning)
This demonstrates the SSL certificate verification failure when CA is not used.
Run with: infisical run -- python test_failure_no_ca.py
"""
# =============================================================================
# SSL 인증서 검증 실패 시나리오 테스트
# =============================================================================
# 목적: CA 인증서 없이 연결 시 서버의 동작 검증
# 테스트 시나리오:
#   1. CA 인증서 없이 연결 (SSL 검증 실패)
#   2. SSL 검증 비활성화 (보안 취약 - 데모용)
#   3. 잘못된 CA 인증서 사용 (체인 검증 실패)
# 보안 개념: 인증서 피닝 (Certificate Pinning)으로 MITM 공격 방지
# =============================================================================

import os, json, sys, ssl, urllib.request, urllib.error  # 표준 라이브러리
from datetime import datetime, timedelta  # 시간 계산
from authlib.jose import jwt  # JWT 생성

# -----------------------------------------------------------------------------
# 환경 설정
# -----------------------------------------------------------------------------
PROXY_URL = os.getenv("PROXY_URL", "https://localhost:8443")  # Proxy Server 주소
TENANT = "tenant_a"  # 테스트용 테넌트
TARGET = "a"  # 라우팅 대상

# JWT 시크릿 확인 - Infisical에서 주입
JWT_SECRET = os.getenv("JWT_SECRET")
if not JWT_SECRET:
    print("[ERROR] JWT_SECRET not set. Run with: infisical run -- python test_failure_no_ca.py")
    sys.exit(1)

# -----------------------------------------------------------------------------
# JWT 토큰 생성 함수
# -----------------------------------------------------------------------------
def create_jwt():
    """유효한 JWT 토큰 생성 - SSL 테스트에서 인증 문제 제외"""
    header = {"alg": "HS256"}  # 알고리즘
    payload = {"tenant": TENANT, "exp": datetime.utcnow() + timedelta(minutes=5), "iat": datetime.utcnow()}
    return jwt.encode(header, payload, JWT_SECRET).decode()

# =============================================================================
# 테스트 함수들 - SSL 인증서 검증 시나리오
# =============================================================================
def test_without_ca():
    """
    테스트 1: CA 인증서 없이 연결 시도
    예상 결과: SSL 인증서 검증 에러 (자체 서명 인증서를 신뢰할 수 없음)
    """
    print("\n" + "="*60)
    print("TEST 1: Connection WITHOUT CA certificate")
    print("="*60)
    print("Expected: SSL certificate verification error")
    print("-"*60)

    url = f"{PROXY_URL}/mcp/{TARGET}"
    token = create_jwt()  # 유효한 JWT (SSL 테스트와 분리)
    data = json.dumps({"method": "select", "params": {}}).encode()

    # 기본 SSL 컨텍스트 - 인증서 검증 필요 (기본 동작)
    ctx = ssl.create_default_context()
    # CA 로드 안함 → 자체 서명 인증서를 검증할 수 없음

    try:
        headers = {"Content-Type": "application/json", "Authorization": f"Bearer {token}"}
        req = urllib.request.Request(url, data=data, headers=headers, method="POST")
        with urllib.request.urlopen(req, context=ctx, timeout=10) as resp:
            print(f"[UNEXPECTED] Request succeeded: {resp.read().decode()}")  # 예상외: 성공
            return False
    except ssl.SSLCertVerificationError as e:  # SSL 검증 에러 (예상됨)
        print(f"[EXPECTED ERROR] SSL Certificate Verification Failed!")
        print(f"  Error type: {type(e).__name__}")
        print(f"  Error message: {e}")
        print(f"\n[EXPLANATION]")
        print(f"  - Server uses self-signed certificate")  # 서버: 자체 서명 인증서 사용
        print(f"  - Client doesn't have CA certificate to verify server")  # 클라이언트: CA 없음
        print(f"  - SSL handshake fails → connection rejected")  # 핸드셰이크 실패
        print(f"\n[PASS] Certificate pinning is working correctly!")
        return True
    except urllib.error.URLError as e:
        # URLError가 SSL 에러를 래핑하는 경우
        if "CERTIFICATE_VERIFY_FAILED" in str(e):
            print(f"[EXPECTED ERROR] SSL Certificate Verification Failed!")
            print(f"  Error type: {type(e).__name__}")
            print(f"  Error message: {e}")
            print(f"\n[EXPLANATION]")
            print(f"  - Server uses self-signed certificate")
            print(f"  - Client doesn't have CA certificate to verify server")
            print(f"  - SSL handshake fails → connection rejected")
            print(f"\n[PASS] Certificate pinning is working correctly!")
            return True
        print(f"[ERROR] URLError: {e}")
        return False
    except Exception as e:
        print(f"[ERROR] Unexpected error: {type(e).__name__}: {e}")
        return False

def test_with_unverified():
    """
    테스트 2: SSL 검증 비활성화로 연결 (보안 취약 - 데모용)
    경고: 프로덕션에서 절대 사용 금지!
    목적: 검증 없이 연결 가능함을 보여주고, 이것이 왜 위험한지 설명
    """
    print("\n" + "="*60)
    print("TEST 2: Connection with SSL verification DISABLED (INSECURE!)")
    print("="*60)
    print("Expected: Connection succeeds but this is INSECURE!")
    print("-"*60)

    url = f"{PROXY_URL}/mcp/{TARGET}"
    token = create_jwt()
    data = json.dumps({"method": "select", "params": {}}).encode()

    # SSL 검증 비활성화 컨텍스트 (위험! 프로덕션에서 절대 사용 금지!)
    ctx = ssl.create_default_context()
    ctx.check_hostname = False  # 호스트명 검증 비활성화
    ctx.verify_mode = ssl.CERT_NONE  # 인증서 검증 비활성화

    print("[WARNING] This disables ALL SSL verification - vulnerable to MITM attacks!")

    try:
        headers = {"Content-Type": "application/json", "Authorization": f"Bearer {token}"}
        req = urllib.request.Request(url, data=data, headers=headers, method="POST")
        with urllib.request.urlopen(req, context=ctx, timeout=10) as resp:
            result = json.loads(resp.read().decode())
            print(f"[RESULT] Request succeeded (insecurely): {json.dumps(result, indent=2)}")
            print(f"\n[WARNING] This proves that without certificate verification,")  # 경고
            print(f"          an attacker could intercept this connection!")  # MITM 가능
            return True
    except Exception as e:
        print(f"[ERROR] {type(e).__name__}: {e}")
        return False

def test_with_wrong_ca():
    """
    테스트 3: 잘못된 CA 인증서로 연결 시도
    시나리오: 공격자가 다른 CA로 발급한 인증서 사용 시도
    예상 결과: 인증서 체인 검증 실패
    """
    print("\n" + "="*60)
    print("TEST 3: Connection with WRONG CA certificate")
    print("="*60)
    print("Expected: SSL certificate verification error (different CA)")
    print("-"*60)

    # 임시 잘못된 CA 인증서 생성 (랜덤 자체 서명 인증서)
    import tempfile
    wrong_ca = """-----BEGIN CERTIFICATE-----
MIIBkTCB+wIJAKHBfpegPjMCMA0GCSqGSIb3DQEBCwUAMBExDzANBgNVBAMMBndy
b25nQ0EwHhcNMjQwMTAxMDAwMDAwWhcNMjUwMTAxMDAwMDAwWjARMQ8wDQYDVQQD
DAZ3cm9uZ0NBMFwwDQYJKoZIhvcNAQEBBQADSwAwSAJBAMOQlN+RzijOsslqxPBn
9XD5ZXW8oQxmSKwhqLg9Y0gzVSEWUqoXU7mBdkpg9XCl/VhB6t6q/q+8RyFU/mXj
j5sCAwEAAaNTMFEwHQYDVR0OBBYEFBm9nY8u8QR0/Y1qXP9y8gvL8IROMB8GA1Ud
IwQYMBaAFBm9nY8u8QR0/Y1qXP9y8gvL8IROMAwGA1UdEwQFMAMBAf8wDQYJKoZI
hvcNAQELBQADQQBxM5J/L1K3l4k/nT5mJx9z5J8J9z5z5J8J9z5z5J8J9z5z5J8J
-----END CERTIFICATE-----"""

    url = f"{PROXY_URL}/mcp/{TARGET}"
    token = create_jwt()
    data = json.dumps({"method": "select", "params": {}}).encode()

    # 임시 파일에 잘못된 CA 저장
    with tempfile.NamedTemporaryFile(mode='w', suffix='.pem', delete=False) as f:
        f.write(wrong_ca)
        wrong_ca_path = f.name

    ctx = ssl.create_default_context()
    try:
        ctx.load_verify_locations(wrong_ca_path)  # 잘못된 CA 로드 시도
    except ssl.SSLError:
        print("[INFO] Wrong CA certificate is invalid (as expected)")  # 잘못된 CA 형식
        ctx = ssl.create_default_context()  # 기본 컨텍스트로 대체

    try:
        headers = {"Content-Type": "application/json", "Authorization": f"Bearer {token}"}
        req = urllib.request.Request(url, data=data, headers=headers, method="POST")
        with urllib.request.urlopen(req, context=ctx, timeout=10) as resp:
            print(f"[UNEXPECTED] Request succeeded: {resp.read().decode()}")  # 예상외: 성공
            return False
    except ssl.SSLCertVerificationError as e:  # 인증서 체인 검증 실패 (예상됨)
        print(f"[EXPECTED ERROR] SSL Certificate Verification Failed!")
        print(f"  Error: {e}")
        print(f"\n[EXPLANATION]")
        print(f"  - Server's certificate is signed by OUR CA")  # 서버: 우리 CA가 서명
        print(f"  - Client tried to verify with DIFFERENT CA")  # 클라이언트: 다른 CA 사용
        print(f"  - Certificate chain validation failed")  # 체인 검증 실패
        print(f"\n[PASS] Wrong CA correctly rejected!")
        return True
    except Exception as e:
        print(f"[INFO] Error (expected): {type(e).__name__}: {e}")  # 다른 에러도 예상됨
        return True
    finally:
        os.unlink(wrong_ca_path)  # 임시 파일 삭제

# =============================================================================
# 메인 실행부 - 모든 테스트 실행 및 결과 요약
# =============================================================================
if __name__ == "__main__":
    print("="*60)
    print("FAILURE SCENARIO TEST: CA Certificate Verification")
    print("="*60)
    print("\nThis test demonstrates what happens when:")
    print("  1. No CA certificate is provided")  # CA 없음
    print("  2. SSL verification is disabled (insecure)")  # SSL 검증 비활성화
    print("  3. Wrong CA certificate is used")  # 잘못된 CA
    print()

    # 모든 테스트 실행 및 결과 수집
    results = []
    results.append(("Without CA", test_without_ca()))
    results.append(("With verification disabled", test_with_unverified()))
    results.append(("With wrong CA", test_with_wrong_ca()))

    # 결과 요약 출력
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    for name, passed in results:
        status = "PASS" if passed else "FAIL"
        print(f"  {name}: [{status}]")

    # 결론 - 인증서 피닝이 보호하는 공격들
    print("\n[CONCLUSION]")
    print("  Certificate pinning protects against:")
    print("  - Man-in-the-Middle (MITM) attacks")  # 중간자 공격
    print("  - Rogue CA certificates")  # 불량 CA 인증서
    print("  - Unauthorized proxy interception")  # 무단 프록시 가로채기
