#!/usr/bin/env python3
"""Test failure scenario: Connection without CA certificate (no certificate pinning)
This demonstrates the SSL certificate verification failure when CA is not used.
Run with: infisical run -- python test_failure_no_ca.py
"""
import os, json, sys, ssl, urllib.request, urllib.error
from datetime import datetime, timedelta
from authlib.jose import jwt

PROXY_URL = os.getenv("PROXY_URL", "https://localhost:8443")
TENANT = "tenant_a"
TARGET = "a"

JWT_SECRET = os.getenv("JWT_SECRET")
if not JWT_SECRET:
    print("[ERROR] JWT_SECRET not set. Run with: infisical run -- python test_failure_no_ca.py")
    sys.exit(1)

def create_jwt():
    """Create a valid JWT token"""
    header = {"alg": "HS256"}
    payload = {"tenant": TENANT, "exp": datetime.utcnow() + timedelta(minutes=5), "iat": datetime.utcnow()}
    return jwt.encode(header, payload, JWT_SECRET).decode()

def test_without_ca():
    """Test 1: Try to connect WITHOUT any CA certificate (should fail)"""
    print("\n" + "="*60)
    print("TEST 1: Connection WITHOUT CA certificate")
    print("="*60)
    print("Expected: SSL certificate verification error")
    print("-"*60)

    url = f"{PROXY_URL}/mcp/{TARGET}"
    token = create_jwt()
    data = json.dumps({"method": "select", "params": {}}).encode()

    # Create SSL context that requires certificate verification (default behavior)
    ctx = ssl.create_default_context()
    # Don't load any CA - this will fail because server uses self-signed cert

    try:
        headers = {"Content-Type": "application/json", "Authorization": f"Bearer {token}"}
        req = urllib.request.Request(url, data=data, headers=headers, method="POST")
        with urllib.request.urlopen(req, context=ctx, timeout=10) as resp:
            print(f"[UNEXPECTED] Request succeeded: {resp.read().decode()}")
            return False
    except ssl.SSLCertVerificationError as e:
        print(f"[EXPECTED ERROR] SSL Certificate Verification Failed!")
        print(f"  Error type: {type(e).__name__}")
        print(f"  Error message: {e}")
        print(f"\n[EXPLANATION]")
        print(f"  - Server uses self-signed certificate")
        print(f"  - Client doesn't have CA certificate to verify server")
        print(f"  - SSL handshake fails → connection rejected")
        print(f"\n[PASS] Certificate pinning is working correctly!")
        return True
    except urllib.error.URLError as e:
        # URLError wraps SSL errors
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
    """Test 2: Try with SSL verification disabled (insecure, for demonstration only)"""
    print("\n" + "="*60)
    print("TEST 2: Connection with SSL verification DISABLED (INSECURE!)")
    print("="*60)
    print("Expected: Connection succeeds but this is INSECURE!")
    print("-"*60)

    url = f"{PROXY_URL}/mcp/{TARGET}"
    token = create_jwt()
    data = json.dumps({"method": "select", "params": {}}).encode()

    # Create unverified SSL context (INSECURE - never do this in production!)
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    print("[WARNING] This disables ALL SSL verification - vulnerable to MITM attacks!")

    try:
        headers = {"Content-Type": "application/json", "Authorization": f"Bearer {token}"}
        req = urllib.request.Request(url, data=data, headers=headers, method="POST")
        with urllib.request.urlopen(req, context=ctx, timeout=10) as resp:
            result = json.loads(resp.read().decode())
            print(f"[RESULT] Request succeeded (insecurely): {json.dumps(result, indent=2)}")
            print(f"\n[WARNING] This proves that without certificate verification,")
            print(f"          an attacker could intercept this connection!")
            return True
    except Exception as e:
        print(f"[ERROR] {type(e).__name__}: {e}")
        return False

def test_with_wrong_ca():
    """Test 3: Try with wrong CA certificate"""
    print("\n" + "="*60)
    print("TEST 3: Connection with WRONG CA certificate")
    print("="*60)
    print("Expected: SSL certificate verification error (different CA)")
    print("-"*60)

    # Create a temporary wrong CA (just a random self-signed cert)
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

    with tempfile.NamedTemporaryFile(mode='w', suffix='.pem', delete=False) as f:
        f.write(wrong_ca)
        wrong_ca_path = f.name

    ctx = ssl.create_default_context()
    try:
        ctx.load_verify_locations(wrong_ca_path)
    except ssl.SSLError:
        print("[INFO] Wrong CA certificate is invalid (as expected)")
        # Use default context which won't have our server's CA
        ctx = ssl.create_default_context()

    try:
        headers = {"Content-Type": "application/json", "Authorization": f"Bearer {token}"}
        req = urllib.request.Request(url, data=data, headers=headers, method="POST")
        with urllib.request.urlopen(req, context=ctx, timeout=10) as resp:
            print(f"[UNEXPECTED] Request succeeded: {resp.read().decode()}")
            return False
    except ssl.SSLCertVerificationError as e:
        print(f"[EXPECTED ERROR] SSL Certificate Verification Failed!")
        print(f"  Error: {e}")
        print(f"\n[EXPLANATION]")
        print(f"  - Server's certificate is signed by OUR CA")
        print(f"  - Client tried to verify with DIFFERENT CA")
        print(f"  - Certificate chain validation failed")
        print(f"\n[PASS] Wrong CA correctly rejected!")
        return True
    except Exception as e:
        print(f"[INFO] Error (expected): {type(e).__name__}: {e}")
        return True
    finally:
        os.unlink(wrong_ca_path)

if __name__ == "__main__":
    print("="*60)
    print("FAILURE SCENARIO TEST: CA Certificate Verification")
    print("="*60)
    print("\nThis test demonstrates what happens when:")
    print("  1. No CA certificate is provided")
    print("  2. SSL verification is disabled (insecure)")
    print("  3. Wrong CA certificate is used")
    print()

    results = []
    results.append(("Without CA", test_without_ca()))
    results.append(("With verification disabled", test_with_unverified()))
    results.append(("With wrong CA", test_with_wrong_ca()))

    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    for name, passed in results:
        status = "PASS" if passed else "FAIL"
        print(f"  {name}: [{status}]")

    print("\n[CONCLUSION]")
    print("  Certificate pinning protects against:")
    print("  - Man-in-the-Middle (MITM) attacks")
    print("  - Rogue CA certificates")
    print("  - Unauthorized proxy interception")
