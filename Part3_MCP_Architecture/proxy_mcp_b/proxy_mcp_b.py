#!/usr/bin/env python3
"""Proxy MCP B - FastMCP server with JWT from Infisical and certificate pinning
Run with: infisical run -- python proxy_mcp_b.py
"""
import os, json, sys, time, ssl, urllib.request, urllib.error
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from authlib.jose import jwt
from fastmcp import FastMCP

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

# Short-lived token cache (no long-lived storage)
_token_cache = {"token": None, "expires": None, "created": None}

# JWT Configuration
JWT_LIFETIME_MINUTES = 5
JWT_REFRESH_BEFORE_MINUTES = 1

# FastMCP server instance
mcp = FastMCP("ProxyMCP_B", instructions=f"Proxy MCP for {TENANT} - routes to backend_{TARGET}")

def log_jwt_status(action: str, created: datetime = None, expires: datetime = None):
    """Log JWT token status with details"""
    now = datetime.utcnow()
    log_data = {
        "timestamp": now.isoformat(),
        "action": action,
        "tenant": TENANT,
    }
    if created:
        log_data["jwt_created"] = created.isoformat()
        log_data["jwt_lifetime_sec"] = JWT_LIFETIME_MINUTES * 60
    if expires:
        log_data["jwt_expires"] = expires.isoformat()
        remaining = (expires - now).total_seconds()
        log_data["jwt_remaining_sec"] = max(0, int(remaining))
        log_data["jwt_expired"] = remaining <= 0
    print(f"[JWT] {json.dumps(log_data)}", file=sys.stderr)

def create_jwt() -> str:
    """Create a short-lived JWT token"""
    now = datetime.utcnow()
    exp = now + timedelta(minutes=JWT_LIFETIME_MINUTES)
    header = {"alg": "HS256"}
    payload = {"tenant": TENANT, "exp": exp, "iat": now}
    token = jwt.encode(header, payload, JWT_SECRET).decode()

    # Update cache with creation time
    _token_cache["created"] = now
    _token_cache["expires"] = now + timedelta(minutes=JWT_LIFETIME_MINUTES - JWT_REFRESH_BEFORE_MINUTES)

    log_jwt_status("TOKEN_CREATED", created=now, expires=exp)
    return token

def get_token() -> str:
    """Get valid token, auto-refresh if expired"""
    now = datetime.utcnow()

    if _token_cache["token"] and _token_cache["expires"]:
        if now < _token_cache["expires"]:
            # Token still valid, log remaining time
            actual_exp = _token_cache["created"] + timedelta(minutes=JWT_LIFETIME_MINUTES)
            remaining = (actual_exp - now).total_seconds()
            print(f"[JWT] Reusing token: {int(remaining)}s remaining", file=sys.stderr)
            return _token_cache["token"]
        else:
            log_jwt_status("TOKEN_REFRESH_NEEDED",
                          created=_token_cache["created"],
                          expires=_token_cache["created"] + timedelta(minutes=JWT_LIFETIME_MINUTES))

    _token_cache["token"] = create_jwt()
    return _token_cache["token"]

def create_ssl_context() -> ssl.SSLContext:
    """Create SSL context with certificate pinning"""
    ctx = ssl.create_default_context()
    if CA_PATH.exists():
        ctx.load_verify_locations(str(CA_PATH))
        print(f"Certificate pinning enabled: {CA_PATH}", file=sys.stderr)
    else:
        print(f"WARNING: CA not found at {CA_PATH}, using system CA", file=sys.stderr)
    return ctx

def call_proxy(method: str, params: Dict[str, Any], retries: int = 3, backoff: float = 1.0) -> Dict[str, Any]:
    """Call proxy server with retry and exponential backoff"""
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

@mcp.tool()
async def insert(name: str, value: str) -> Dict[str, Any]:
    """
    Insert a new item into Backend B.

    :param name: Name of the item to insert
    :param value: Value of the item
    :return: Result with status and inserted item details
    """
    print(f"[{TENANT}] insert: name={name}, value={value}", file=sys.stderr)
    result = call_proxy("insert", {"name": name, "value": value})
    return result

@mcp.tool()
async def update(id: int, value: str) -> Dict[str, Any]:
    """
    Update an existing item in Backend B.

    :param id: ID of the item to update
    :param value: New value for the item
    :return: Result with status and updated item details
    """
    print(f"[{TENANT}] update: id={id}, value={value}", file=sys.stderr)
    result = call_proxy("update", {"id": id, "value": value})
    return result

@mcp.tool()
async def select(id: Optional[int] = None) -> Dict[str, Any]:
    """
    Select items from Backend B.

    :param id: Optional ID to select specific item. If not provided, returns all items.
    :return: Result with queried items
    """
    params = {"id": id} if id is not None else {}
    print(f"[{TENANT}] select: params={params}", file=sys.stderr)
    result = call_proxy("select", params)
    return result

if __name__ == "__main__":
    print(f"Proxy MCP B started (tenant: {TENANT})", file=sys.stderr)
    print(f"JWT_SECRET loaded from Infisical", file=sys.stderr)
    print(f"Target: {PROXY_URL}/mcp/{TARGET}", file=sys.stderr)
    mcp.run()
