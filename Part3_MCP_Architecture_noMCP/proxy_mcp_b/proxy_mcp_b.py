#!/usr/bin/env python3
"""Proxy MCP B - HTTPS client with JWT from Infisical and certificate pinning
Run with: infisical run -- python proxy_mcp_b.py
"""
import os, json, sys, time, ssl, urllib.request, urllib.error
from pathlib import Path
from datetime import datetime, timedelta
from authlib.jose import jwt

PROXY_URL = os.getenv("PROXY_URL", "https://localhost:8443")
TENANT = "tenant_b"
TARGET = "b"

# JWT_SECRET must come from Infisical
JWT_SECRET = os.getenv("JWT_SECRET")
if not JWT_SECRET:
    print("ERROR: JWT_SECRET not set. Run with: infisical run -- python proxy_mcp_b.py", file=sys.stderr)
    sys.exit(1)

# CA certificate for pinning
CA_PATH = Path(__file__).parent.parent / "proxy_server" / "certs" / "ca.pem"

_token_cache = {"token": None, "expires": None}

def create_jwt():
    header = {"alg": "HS256"}
    payload = {"tenant": TENANT, "exp": datetime.utcnow() + timedelta(minutes=5), "iat": datetime.utcnow()}
    return jwt.encode(header, payload, JWT_SECRET).decode()

def get_token():
    if _token_cache["token"] and _token_cache["expires"] and datetime.utcnow() < _token_cache["expires"]:
        return _token_cache["token"]
    _token_cache["token"] = create_jwt()
    _token_cache["expires"] = datetime.utcnow() + timedelta(minutes=4)
    return _token_cache["token"]

def create_ssl_context():
    ctx = ssl.create_default_context()
    if CA_PATH.exists():
        ctx.load_verify_locations(str(CA_PATH))
        print(f"Certificate pinning enabled: {CA_PATH}", file=sys.stderr)
    else:
        print(f"WARNING: CA not found at {CA_PATH}, using system CA", file=sys.stderr)
    return ctx

def call_proxy(method, params, retries=3, backoff=1.0):
    url = f"{PROXY_URL}/mcp/{TARGET}"
    data = json.dumps({"method": method, "params": params}).encode()

    for attempt in range(retries):
        try:
            headers = {"Content-Type": "application/json", "Authorization": f"Bearer {get_token()}"}
            req = urllib.request.Request(url, data=data, headers=headers, method="POST")
            with urllib.request.urlopen(req, context=create_ssl_context(), timeout=30) as resp:
                return json.loads(resp.read().decode())
        except urllib.error.HTTPError as e:
            if e.code == 401:
                _token_cache["token"] = None
                continue
            if attempt == retries - 1:
                return {"error": f"HTTP {e.code}: {e.reason}"}
        except Exception as e:
            if attempt == retries - 1:
                return {"error": str(e)}
        time.sleep(backoff * (2 ** attempt))
    return {"error": "Max retries exceeded"}

def handle_request(req):
    method, params = req.get("method", ""), req.get("params", {})
    if method in ("insert", "update", "select"):
        return call_proxy(method, params)
    elif method == "tools/list":
        return {"result": {"tools": [
            {"name": "insert", "description": "Insert item"},
            {"name": "update", "description": "Update item"},
            {"name": "select", "description": "Select items"}
        ]}}
    return {"error": f"Unknown method: {method}"}

if __name__ == "__main__":
    print(f"Proxy MCP B started (tenant: {TENANT})", file=sys.stderr)
    print(f"JWT_SECRET loaded from Infisical", file=sys.stderr)
    for line in sys.stdin:
        try:
            req = json.loads(line.strip())
            resp = handle_request(req)
            resp.update({"jsonrpc": "2.0", "id": req.get("id", 1)})
            print(json.dumps(resp), flush=True)
        except Exception as e:
            print(json.dumps({"jsonrpc": "2.0", "error": str(e), "id": 1}), flush=True)
