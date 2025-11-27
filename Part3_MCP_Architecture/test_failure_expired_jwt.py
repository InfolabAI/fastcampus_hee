#!/usr/bin/env python3
"""Test failure scenario: Expired JWT token
This demonstrates what happens when JWT token expires.
Run with: infisical run -- python test_failure_expired_jwt.py
"""
import os, json, sys, ssl, urllib.request, urllib.error
from pathlib import Path
from datetime import datetime, timedelta
from authlib.jose import jwt

PROXY_URL = os.getenv("PROXY_URL", "https://localhost:8443")
TENANT = "tenant_a"
TARGET = "a"
CA_PATH = Path(__file__).parent / "proxy_server" / "certs" / "ca.pem"

JWT_SECRET = os.getenv("JWT_SECRET")
if not JWT_SECRET:
    print("[ERROR] JWT_SECRET not set. Run with: infisical run -- python test_failure_expired_jwt.py")
    sys.exit(1)

def create_ssl_context():
    """Create SSL context with certificate pinning"""
    ctx = ssl.create_default_context()
    if CA_PATH.exists():
        ctx.load_verify_locations(str(CA_PATH))
    return ctx

def create_expired_jwt():
    """Create an EXPIRED JWT token (expired 1 minute ago)"""
    now = datetime.utcnow()
    expired_time = now - timedelta(minutes=1)  # Expired 1 minute ago
    issued_time = now - timedelta(minutes=6)   # Issued 6 minutes ago

    header = {"alg": "HS256"}
    payload = {
        "tenant": TENANT,
        "exp": expired_time,  # Already expired!
        "iat": issued_time
    }
    return jwt.encode(header, payload, JWT_SECRET).decode(), issued_time, expired_time

def create_about_to_expire_jwt(seconds_until_expire=2):
    """Create a JWT that will expire very soon"""
    now = datetime.utcnow()
    exp_time = now + timedelta(seconds=seconds_until_expire)

    header = {"alg": "HS256"}
    payload = {
        "tenant": TENANT,
        "exp": exp_time,
        "iat": now
    }
    return jwt.encode(header, payload, JWT_SECRET).decode(), now, exp_time

def create_valid_jwt():
    """Create a valid JWT token"""
    now = datetime.utcnow()
    exp_time = now + timedelta(minutes=5)

    header = {"alg": "HS256"}
    payload = {"tenant": TENANT, "exp": exp_time, "iat": now}
    return jwt.encode(header, payload, JWT_SECRET).decode(), now, exp_time

def make_request(token, test_name):
    """Make a request and handle the response"""
    url = f"{PROXY_URL}/mcp/{TARGET}"
    data = json.dumps({"method": "select", "params": {}}).encode()

    try:
        headers = {"Content-Type": "application/json", "Authorization": f"Bearer {token}"}
        req = urllib.request.Request(url, data=data, headers=headers, method="POST")
        with urllib.request.urlopen(req, context=create_ssl_context(), timeout=10) as resp:
            result = json.loads(resp.read().decode())
            return True, 200, result
    except urllib.error.HTTPError as e:
        body = e.read().decode() if e.fp else ""
        return False, e.code, {"error": e.reason, "detail": body}
    except Exception as e:
        return False, 0, {"error": str(e)}

def test_expired_token():
    """Test 1: Use an already expired token"""
    print("\n" + "="*60)
    print("TEST 1: Using EXPIRED JWT Token")
    print("="*60)
    print("Expected: 401 Unauthorized - Token has expired")
    print("-"*60)

    token, iat, exp = create_expired_jwt()
    now = datetime.utcnow()

    print(f"[JWT Details]")
    print(f"  Issued At (iat):  {iat.isoformat()}")
    print(f"  Expires At (exp): {exp.isoformat()}")
    print(f"  Current Time:     {now.isoformat()}")
    print(f"  Expired:          {(now - exp).total_seconds():.0f} seconds ago")
    print()

    success, status_code, result = make_request(token, "expired_token")

    if status_code == 401:
        print(f"[EXPECTED ERROR] HTTP 401 Unauthorized")
        print(f"  Response: {json.dumps(result, indent=2)}")
        print(f"\n[EXPLANATION]")
        print(f"  - JWT token's 'exp' claim is in the past")
        print(f"  - Server validates token expiration on each request")
        print(f"  - Expired tokens are rejected with 401")
        print(f"\n[PASS] Expired token correctly rejected!")
        return True
    else:
        print(f"[UNEXPECTED] Status: {status_code}, Result: {result}")
        return False

def test_token_expires_during_use():
    """Test 2: Token expires while waiting"""
    print("\n" + "="*60)
    print("TEST 2: Token EXPIRES DURING USE")
    print("="*60)
    print("Expected: First request succeeds, second fails after expiry")
    print("-"*60)

    # Create token that expires in 3 seconds
    token, iat, exp = create_about_to_expire_jwt(seconds_until_expire=3)
    now = datetime.utcnow()

    print(f"[JWT Details]")
    print(f"  Issued At (iat):  {iat.isoformat()}")
    print(f"  Expires At (exp): {exp.isoformat()}")
    print(f"  Time until expiry: {(exp - now).total_seconds():.1f} seconds")
    print()

    # First request - should succeed
    print("[Request 1] Immediate request (token still valid)...")
    success1, status1, result1 = make_request(token, "before_expiry")

    if success1:
        print(f"  Status: {status1} OK")
        print(f"  [PASS] Request succeeded while token was valid")
    else:
        print(f"  [WARN] Request failed: {result1}")

    # Wait for token to expire
    import time
    wait_time = 4  # Wait 4 seconds (token expires in 3)
    print(f"\n[Waiting {wait_time} seconds for token to expire...]")
    time.sleep(wait_time)

    # Second request - should fail
    now_after = datetime.utcnow()
    print(f"\n[Request 2] After waiting (token now expired)...")
    print(f"  Current Time: {now_after.isoformat()}")
    print(f"  Token expired: {(now_after - exp).total_seconds():.1f} seconds ago")

    success2, status2, result2 = make_request(token, "after_expiry")

    if status2 == 401:
        print(f"  Status: {status2} Unauthorized")
        print(f"  [PASS] Expired token correctly rejected!")
        return True
    else:
        print(f"  [UNEXPECTED] Status: {status2}, Result: {result2}")
        return False

def test_wrong_secret():
    """Test 3: Token signed with wrong secret"""
    print("\n" + "="*60)
    print("TEST 3: Token signed with WRONG SECRET")
    print("="*60)
    print("Expected: 401 Unauthorized - Invalid signature")
    print("-"*60)

    now = datetime.utcnow()
    exp = now + timedelta(minutes=5)

    # Sign with wrong secret
    wrong_secret = "this-is-a-wrong-secret-key-12345"
    header = {"alg": "HS256"}
    payload = {"tenant": TENANT, "exp": exp, "iat": now}
    token = jwt.encode(header, payload, wrong_secret).decode()

    print(f"[JWT Details]")
    print(f"  Correct Secret: {JWT_SECRET[:8]}...")
    print(f"  Used Secret:    {wrong_secret[:8]}...")
    print(f"  Token valid structurally but signature won't match")
    print()

    success, status_code, result = make_request(token, "wrong_secret")

    if status_code == 401:
        print(f"[EXPECTED ERROR] HTTP 401 Unauthorized")
        print(f"  Response: {json.dumps(result, indent=2)}")
        print(f"\n[EXPLANATION]")
        print(f"  - JWT signature is verified using JWT_SECRET")
        print(f"  - Token was signed with different secret")
        print(f"  - Signature verification failed")
        print(f"\n[PASS] Invalid signature correctly rejected!")
        return True
    else:
        print(f"[UNEXPECTED] Status: {status_code}, Result: {result}")
        return False

def test_tampered_payload():
    """Test 4: Token with tampered payload"""
    print("\n" + "="*60)
    print("TEST 4: Token with TAMPERED PAYLOAD")
    print("="*60)
    print("Expected: 401 Unauthorized - Signature mismatch")
    print("-"*60)

    # Create valid token
    now = datetime.utcnow()
    exp = now + timedelta(minutes=5)
    header = {"alg": "HS256"}
    payload = {"tenant": "tenant_a", "exp": exp, "iat": now}
    valid_token = jwt.encode(header, payload, JWT_SECRET).decode()

    # Tamper with the token - change tenant in payload
    import base64
    parts = valid_token.split('.')

    # Decode payload, modify, re-encode (without re-signing)
    payload_json = base64.urlsafe_b64decode(parts[1] + "==")
    payload_data = json.loads(payload_json)
    payload_data["tenant"] = "admin"  # Try to escalate to admin!

    tampered_payload = base64.urlsafe_b64encode(
        json.dumps(payload_data).encode()
    ).decode().rstrip("=")

    tampered_token = f"{parts[0]}.{tampered_payload}.{parts[2]}"

    print(f"[Tampering Details]")
    print(f"  Original tenant: tenant_a")
    print(f"  Tampered tenant: admin")
    print(f"  Signature unchanged (will fail verification)")
    print()

    success, status_code, result = make_request(tampered_token, "tampered")

    if status_code == 401:
        print(f"[EXPECTED ERROR] HTTP 401 Unauthorized")
        print(f"  Response: {json.dumps(result, indent=2)}")
        print(f"\n[EXPLANATION]")
        print(f"  - Payload was modified after signing")
        print(f"  - Signature no longer matches payload")
        print(f"  - Tampering detected and rejected")
        print(f"\n[PASS] Tampered token correctly rejected!")
        return True
    else:
        print(f"[UNEXPECTED] Status: {status_code}, Result: {result}")
        return False

def test_valid_token():
    """Test 5: Valid token (baseline)"""
    print("\n" + "="*60)
    print("TEST 5: Using VALID JWT Token (Baseline)")
    print("="*60)
    print("Expected: 200 OK - Request succeeds")
    print("-"*60)

    token, iat, exp = create_valid_jwt()
    now = datetime.utcnow()

    print(f"[JWT Details]")
    print(f"  Issued At (iat):  {iat.isoformat()}")
    print(f"  Expires At (exp): {exp.isoformat()}")
    print(f"  Time until expiry: {(exp - now).total_seconds():.0f} seconds")
    print()

    success, status_code, result = make_request(token, "valid_token")

    if success:
        print(f"[SUCCESS] HTTP 200 OK")
        print(f"  Response: {json.dumps(result, indent=2)[:200]}...")
        print(f"\n[PASS] Valid token accepted!")
        return True
    else:
        print(f"[UNEXPECTED] Status: {status_code}, Result: {result}")
        return False

if __name__ == "__main__":
    print("="*60)
    print("FAILURE SCENARIO TEST: JWT Token Validation")
    print("="*60)
    print("\nThis test demonstrates what happens when:")
    print("  1. JWT token is expired")
    print("  2. Token expires during use")
    print("  3. Token is signed with wrong secret")
    print("  4. Token payload is tampered")
    print("  5. Valid token (baseline for comparison)")
    print()

    results = []
    results.append(("Expired token", test_expired_token()))
    results.append(("Token expires during use", test_token_expires_during_use()))
    results.append(("Wrong secret", test_wrong_secret()))
    results.append(("Tampered payload", test_tampered_payload()))
    results.append(("Valid token (baseline)", test_valid_token()))

    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    for name, passed in results:
        status = "PASS" if passed else "FAIL"
        print(f"  {name}: [{status}]")

    print("\n[CONCLUSION]")
    print("  JWT validation protects against:")
    print("  - Expired tokens (time-based security)")
    print("  - Forged tokens (wrong secret)")
    print("  - Tampered tokens (payload modification)")
    print("  - Replay attacks (short expiration time)")
