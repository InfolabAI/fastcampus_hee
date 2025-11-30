#!/usr/bin/env python3
"""Test failure scenario: Expired JWT token
This demonstrates what happens when JWT token expires.
Run with: infisical run -- python test_failure_expired_jwt.py
"""
# =============================================================================
# JWT 토큰 만료 실패 시나리오 테스트
# =============================================================================
# 목적: JWT 토큰 만료 시 서버의 동작 검증
# 테스트 시나리오:
#   1. 이미 만료된 토큰
#   2. 사용 중 만료되는 토큰
#   3. 잘못된 시크릿으로 서명된 토큰
#   4. 페이로드가 변조된 토큰
#   5. 유효한 토큰 (기준 비교용)
# =============================================================================

import os, json, sys, ssl, urllib.request, urllib.error  # 표준 라이브러리
from pathlib import Path  # 파일 경로
from datetime import datetime, timedelta  # 시간 계산
from authlib.jose import jwt  # JWT 생성/검증

# -----------------------------------------------------------------------------
# 환경 설정
# -----------------------------------------------------------------------------
PROXY_URL = os.getenv("PROXY_URL", "https://localhost:8443")  # Proxy Server 주소
TENANT = "tenant_a"  # 테스트용 테넌트
TARGET = "a"  # 라우팅 대상
CA_PATH = Path(__file__).parent / "proxy_server" / "certs" / "ca.pem"  # CA 인증서 경로

# JWT 시크릿 확인 - Infisical에서 주입
JWT_SECRET = os.getenv("JWT_SECRET")
if not JWT_SECRET:
    print("[ERROR] JWT_SECRET not set. Run with: infisical run -- python test_failure_expired_jwt.py")
    sys.exit(1)

# -----------------------------------------------------------------------------
# SSL 컨텍스트 생성 - 인증서 피닝
# -----------------------------------------------------------------------------
def create_ssl_context():
    """SSL 컨텍스트 생성 - CA 인증서로 서버 검증"""
    ctx = ssl.create_default_context()  # 기본 SSL 컨텍스트
    if CA_PATH.exists():
        ctx.load_verify_locations(str(CA_PATH))  # CA 인증서 로드 (피닝)
    return ctx

# -----------------------------------------------------------------------------
# JWT 토큰 생성 함수들 - 다양한 테스트 시나리오용
# -----------------------------------------------------------------------------
def create_expired_jwt():
    """이미 만료된 JWT 토큰 생성 (1분 전 만료)"""
    now = datetime.utcnow()
    expired_time = now - timedelta(minutes=1)  # 만료 시간: 1분 전 (이미 만료!)
    issued_time = now - timedelta(minutes=6)   # 발급 시간: 6분 전

    header = {"alg": "HS256"}  # 알고리즘: HMAC-SHA256
    payload = {
        "tenant": TENANT,  # 테넌트 클레임
        "exp": expired_time,  # 만료 시간 (이미 지남!)
        "iat": issued_time  # 발급 시간
    }
    return jwt.encode(header, payload, JWT_SECRET).decode(), issued_time, expired_time

def create_about_to_expire_jwt(seconds_until_expire=2):
    """곧 만료될 JWT 토큰 생성 - 시간 경과 테스트용"""
    now = datetime.utcnow()
    exp_time = now + timedelta(seconds=seconds_until_expire)  # N초 후 만료

    header = {"alg": "HS256"}
    payload = {
        "tenant": TENANT,
        "exp": exp_time,  # 곧 만료
        "iat": now  # 지금 발급
    }
    return jwt.encode(header, payload, JWT_SECRET).decode(), now, exp_time

def create_valid_jwt():
    """유효한 JWT 토큰 생성 - 기준 비교용"""
    now = datetime.utcnow()
    exp_time = now + timedelta(minutes=5)  # 5분 후 만료

    header = {"alg": "HS256"}
    payload = {"tenant": TENANT, "exp": exp_time, "iat": now}
    return jwt.encode(header, payload, JWT_SECRET).decode(), now, exp_time

# -----------------------------------------------------------------------------
# HTTP 요청 함수 - Proxy Server에 요청
# -----------------------------------------------------------------------------
def make_request(token, test_name):
    """Proxy Server에 요청 전송 및 응답 처리"""
    url = f"{PROXY_URL}/mcp/{TARGET}"  # 요청 URL
    data = json.dumps({"method": "select", "params": {}}).encode()  # 요청 바디

    try:
        headers = {"Content-Type": "application/json", "Authorization": f"Bearer {token}"}  # JWT 토큰 헤더
        req = urllib.request.Request(url, data=data, headers=headers, method="POST")
        with urllib.request.urlopen(req, context=create_ssl_context(), timeout=10) as resp:
            result = json.loads(resp.read().decode())
            return True, 200, result  # 성공: (True, 상태코드, 응답)
    except urllib.error.HTTPError as e:
        body = e.read().decode() if e.fp else ""
        return False, e.code, {"error": e.reason, "detail": body}  # HTTP 에러
    except Exception as e:
        return False, 0, {"error": str(e)}  # 기타 예외

# =============================================================================
# 테스트 함수들 - 각 시나리오별 검증
# =============================================================================
def test_expired_token():
    """
    테스트 1: 이미 만료된 토큰 사용
    예상 결과: 401 Unauthorized
    """
    print("\n" + "="*60)
    print("TEST 1: Using EXPIRED JWT Token")
    print("="*60)
    print("Expected: 401 Unauthorized - Token has expired")
    print("-"*60)

    token, iat, exp = create_expired_jwt()  # 만료된 토큰 생성
    now = datetime.utcnow()

    # JWT 상세 정보 출력
    print(f"[JWT Details]")
    print(f"  Issued At (iat):  {iat.isoformat()}")  # 발급 시간
    print(f"  Expires At (exp): {exp.isoformat()}")  # 만료 시간
    print(f"  Current Time:     {now.isoformat()}")  # 현재 시간
    print(f"  Expired:          {(now - exp).total_seconds():.0f} seconds ago")  # 만료 경과 시간
    print()

    success, status_code, result = make_request(token, "expired_token")

    if status_code == 401:  # 401 = 예상대로 거부됨
        print(f"[EXPECTED ERROR] HTTP 401 Unauthorized")
        print(f"  Response: {json.dumps(result, indent=2)}")
        print(f"\n[EXPLANATION]")
        print(f"  - JWT token's 'exp' claim is in the past")  # exp가 과거
        print(f"  - Server validates token expiration on each request")  # 매 요청마다 검증
        print(f"  - Expired tokens are rejected with 401")  # 만료된 토큰 거부
        print(f"\n[PASS] Expired token correctly rejected!")
        return True
    else:
        print(f"[UNEXPECTED] Status: {status_code}, Result: {result}")  # 예상외 결과
        return False

def test_token_expires_during_use():
    """
    테스트 2: 사용 중 토큰 만료
    시나리오: 첫 요청 성공 → 대기 → 두 번째 요청 실패
    """
    print("\n" + "="*60)
    print("TEST 2: Token EXPIRES DURING USE")
    print("="*60)
    print("Expected: First request succeeds, second fails after expiry")
    print("-"*60)

    # 3초 후 만료되는 토큰 생성
    token, iat, exp = create_about_to_expire_jwt(seconds_until_expire=3)
    now = datetime.utcnow()

    print(f"[JWT Details]")
    print(f"  Issued At (iat):  {iat.isoformat()}")
    print(f"  Expires At (exp): {exp.isoformat()}")
    print(f"  Time until expiry: {(exp - now).total_seconds():.1f} seconds")  # 만료까지 남은 시간
    print()

    # 첫 번째 요청 - 아직 유효
    print("[Request 1] Immediate request (token still valid)...")
    success1, status1, result1 = make_request(token, "before_expiry")

    if success1:
        print(f"  Status: {status1} OK")
        print(f"  [PASS] Request succeeded while token was valid")  # 유효한 동안 성공
    else:
        print(f"  [WARN] Request failed: {result1}")

    # 토큰 만료까지 대기
    import time
    wait_time = 4  # 4초 대기 (토큰은 3초 후 만료)
    print(f"\n[Waiting {wait_time} seconds for token to expire...]")
    time.sleep(wait_time)  # 시간 경과 시뮬레이션

    # 두 번째 요청 - 이제 만료됨
    now_after = datetime.utcnow()
    print(f"\n[Request 2] After waiting (token now expired)...")
    print(f"  Current Time: {now_after.isoformat()}")
    print(f"  Token expired: {(now_after - exp).total_seconds():.1f} seconds ago")  # 만료 후 경과 시간

    success2, status2, result2 = make_request(token, "after_expiry")

    if status2 == 401:  # 만료 후 401 예상
        print(f"  Status: {status2} Unauthorized")
        print(f"  [PASS] Expired token correctly rejected!")
        return True
    else:
        print(f"  [UNEXPECTED] Status: {status2}, Result: {result2}")
        return False

def test_wrong_secret():
    """
    테스트 3: 잘못된 시크릿으로 서명된 토큰
    공격 시나리오: 공격자가 자체 시크릿으로 토큰 생성 시도
    """
    print("\n" + "="*60)
    print("TEST 3: Token signed with WRONG SECRET")
    print("="*60)
    print("Expected: 401 Unauthorized - Invalid signature")
    print("-"*60)

    now = datetime.utcnow()
    exp = now + timedelta(minutes=5)

    # 잘못된 시크릿으로 서명 - 공격자 시뮬레이션
    wrong_secret = "this-is-a-wrong-secret-key-12345"  # 공격자가 추측한 시크릿
    header = {"alg": "HS256"}
    payload = {"tenant": TENANT, "exp": exp, "iat": now}
    token = jwt.encode(header, payload, wrong_secret).decode()  # 잘못된 키로 서명

    print(f"[JWT Details]")
    print(f"  Correct Secret: {JWT_SECRET[:8]}...")  # 서버의 올바른 시크릿
    print(f"  Used Secret:    {wrong_secret[:8]}...")  # 공격자가 사용한 시크릿
    print(f"  Token valid structurally but signature won't match")  # 구조는 유효하지만 서명 불일치
    print()

    success, status_code, result = make_request(token, "wrong_secret")

    if status_code == 401:  # 서명 검증 실패 → 401
        print(f"[EXPECTED ERROR] HTTP 401 Unauthorized")
        print(f"  Response: {json.dumps(result, indent=2)}")
        print(f"\n[EXPLANATION]")
        print(f"  - JWT signature is verified using JWT_SECRET")  # 서버 시크릿으로 서명 검증
        print(f"  - Token was signed with different secret")  # 다른 시크릿으로 서명됨
        print(f"  - Signature verification failed")  # 서명 검증 실패
        print(f"\n[PASS] Invalid signature correctly rejected!")
        return True
    else:
        print(f"[UNEXPECTED] Status: {status_code}, Result: {result}")
        return False

def test_tampered_payload():
    """
    테스트 4: 페이로드가 변조된 토큰
    공격 시나리오: 토큰 탈취 후 권한 상승 시도 (tenant_a → admin)
    """
    print("\n" + "="*60)
    print("TEST 4: Token with TAMPERED PAYLOAD")
    print("="*60)
    print("Expected: 401 Unauthorized - Signature mismatch")
    print("-"*60)

    # 유효한 토큰 생성 (먼저 정상 토큰 필요)
    now = datetime.utcnow()
    exp = now + timedelta(minutes=5)
    header = {"alg": "HS256"}
    payload = {"tenant": "tenant_a", "exp": exp, "iat": now}
    valid_token = jwt.encode(header, payload, JWT_SECRET).decode()  # 정상 서명된 토큰

    # 토큰 변조 - 페이로드의 tenant를 admin으로 변경
    import base64
    parts = valid_token.split('.')  # JWT: header.payload.signature

    # 페이로드 디코드 → 수정 → 재인코딩 (서명은 그대로!)
    payload_json = base64.urlsafe_b64decode(parts[1] + "==")  # base64 디코드
    payload_data = json.loads(payload_json)  # JSON 파싱
    payload_data["tenant"] = "admin"  # 권한 상승 시도!

    tampered_payload = base64.urlsafe_b64encode(
        json.dumps(payload_data).encode()
    ).decode().rstrip("=")  # 변조된 페이로드

    tampered_token = f"{parts[0]}.{tampered_payload}.{parts[2]}"  # 변조된 토큰 조합

    print(f"[Tampering Details]")
    print(f"  Original tenant: tenant_a")  # 원래 테넌트
    print(f"  Tampered tenant: admin")  # 변조된 테넌트 (권한 상승 시도)
    print(f"  Signature unchanged (will fail verification)")  # 서명은 변경 안됨 → 불일치
    print()

    success, status_code, result = make_request(tampered_token, "tampered")

    if status_code == 401:  # 변조 감지 → 401
        print(f"[EXPECTED ERROR] HTTP 401 Unauthorized")
        print(f"  Response: {json.dumps(result, indent=2)}")
        print(f"\n[EXPLANATION]")
        print(f"  - Payload was modified after signing")  # 서명 후 페이로드 변경
        print(f"  - Signature no longer matches payload")  # 서명과 페이로드 불일치
        print(f"  - Tampering detected and rejected")  # 변조 감지 및 거부
        print(f"\n[PASS] Tampered token correctly rejected!")
        return True
    else:
        print(f"[UNEXPECTED] Status: {status_code}, Result: {result}")
        return False

def test_valid_token():
    """
    테스트 5: 유효한 토큰 (기준 비교용)
    목적: 다른 테스트들과 비교하기 위한 정상 동작 확인
    """
    print("\n" + "="*60)
    print("TEST 5: Using VALID JWT Token (Baseline)")
    print("="*60)
    print("Expected: 200 OK - Request succeeds")
    print("-"*60)

    token, iat, exp = create_valid_jwt()  # 유효한 토큰 생성
    now = datetime.utcnow()

    print(f"[JWT Details]")
    print(f"  Issued At (iat):  {iat.isoformat()}")  # 발급 시간
    print(f"  Expires At (exp): {exp.isoformat()}")  # 만료 시간
    print(f"  Time until expiry: {(exp - now).total_seconds():.0f} seconds")  # 만료까지 남은 시간
    print()

    success, status_code, result = make_request(token, "valid_token")

    if success:  # 200 OK 예상
        print(f"[SUCCESS] HTTP 200 OK")
        print(f"  Response: {json.dumps(result, indent=2)[:200]}...")  # 응답 일부 출력
        print(f"\n[PASS] Valid token accepted!")
        return True
    else:
        print(f"[UNEXPECTED] Status: {status_code}, Result: {result}")
        return False

# =============================================================================
# 메인 실행부 - 모든 테스트 실행 및 결과 요약
# =============================================================================
if __name__ == "__main__":
    print("="*60)
    print("FAILURE SCENARIO TEST: JWT Token Validation")
    print("="*60)
    print("\nThis test demonstrates what happens when:")
    print("  1. JWT token is expired")  # 만료된 토큰
    print("  2. Token expires during use")  # 사용 중 만료
    print("  3. Token is signed with wrong secret")  # 잘못된 시크릿
    print("  4. Token payload is tampered")  # 변조된 페이로드
    print("  5. Valid token (baseline for comparison)")  # 유효한 토큰 (기준)
    print()

    # 모든 테스트 실행 및 결과 수집
    results = []
    results.append(("Expired token", test_expired_token()))
    results.append(("Token expires during use", test_token_expires_during_use()))
    results.append(("Wrong secret", test_wrong_secret()))
    results.append(("Tampered payload", test_tampered_payload()))
    results.append(("Valid token (baseline)", test_valid_token()))

    # 결과 요약 출력
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    for name, passed in results:
        status = "PASS" if passed else "FAIL"
        print(f"  {name}: [{status}]")

    # 결론 - JWT 검증이 보호하는 공격들
    print("\n[CONCLUSION]")
    print("  JWT validation protects against:")
    print("  - Expired tokens (time-based security)")  # 시간 기반 보안
    print("  - Forged tokens (wrong secret)")  # 위조된 토큰
    print("  - Tampered tokens (payload modification)")  # 변조된 토큰
    print("  - Replay attacks (short expiration time)")  # 리플레이 공격 (짧은 만료 시간)
