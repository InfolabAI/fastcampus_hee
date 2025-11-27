#!/usr/bin/env python3
"""FastAPI Proxy Server with JWT + Casbin + Multi-tenant routing
JWT_SECRET must be loaded from Infisical (no hardcoding)
"""
import os, json, subprocess, sys
from pathlib import Path
from datetime import datetime
from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from authlib.jose import jwt
from pydantic import BaseModel
import casbin

BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

# JWT_SECRET must come from Infisical - fail if not set
JWT_SECRET = os.getenv("JWT_SECRET")
if not JWT_SECRET:
    print("ERROR: JWT_SECRET not set. Run with: infisical run -- python server.py")
    sys.exit(1)

app = FastAPI()
security = HTTPBearer()
enforcer = casbin.Enforcer(str(Path(__file__).parent / "model.conf"), str(Path(__file__).parent / "policy.csv"))
BACKENDS = {}

class MCPRequest(BaseModel):
    method: str
    params: dict = {}

def log_debug(tenant: str, request: dict, response: dict, allowed: bool, backend: str):
    log_entry = {"timestamp": datetime.utcnow().isoformat(), "tenant": tenant, "request": request,
                 "response": response, "allowed": allowed, "backend": backend}
    with open(BASE_DIR / "proxy_server" / "debug.log", "a") as f:
        f.write(json.dumps(log_entry) + "\n")

def verify_jwt(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    try:
        claims = jwt.decode(credentials.credentials, JWT_SECRET)
        claims.validate()
        return dict(claims)
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {e}")

async def get_backend(tenant: str) -> subprocess.Popen:
    if tenant in BACKENDS and BACKENDS[tenant].poll() is None:
        return BACKENDS[tenant]
    script = BASE_DIR / f"backend_{tenant}" / f"backend_{tenant}.py"
    env = os.environ.copy()
    env["DB_PATH"] = str(DATA_DIR / f"tenant_{tenant}.db")
    proc = subprocess.Popen([sys.executable, str(script)], stdin=subprocess.PIPE,
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, env=env)
    BACKENDS[tenant] = proc
    return proc

async def call_backend(tenant: str, method: str, params: dict) -> dict:
    proc = await get_backend(tenant)
    request = {"jsonrpc": "2.0", "id": 1, "method": method, "params": params}
    try:
        proc.stdin.write(json.dumps(request) + "\n")
        proc.stdin.flush()
        line = proc.stdout.readline()
        return json.loads(line) if line else {"error": "No response"}
    except Exception as e:
        return {"error": str(e)}

@app.post("/mcp/{target_tenant}")
async def proxy_mcp(target_tenant: str, req: MCPRequest, claims: dict = Depends(verify_jwt)):
    tenant = claims.get("tenant", "unknown")
    allowed = enforcer.enforce(tenant, f"backend_{target_tenant}", "access")
    request_data = {"method": req.method, "params": req.params, "target": target_tenant}

    if not allowed:
        resp = {"error": f"Access denied: {tenant} cannot access backend_{target_tenant}"}
        log_debug(tenant, request_data, resp, False, f"backend_{target_tenant}")
        raise HTTPException(status_code=403, detail=resp["error"])

    resp = await call_backend(target_tenant, req.method, req.params)
    log_debug(tenant, request_data, resp, True, f"backend_{target_tenant}")
    return resp

@app.get("/health")
async def health():
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    cert_dir = Path(__file__).parent / "certs"
    cert_file, key_file = cert_dir / "cert.pem", cert_dir / "key.pem"
    ca_file = cert_dir / "ca.pem"

    if not cert_file.exists() or not ca_file.exists():
        print("ERROR: TLS certificates not found. Run: bash certs/generate_ca.sh")
        sys.exit(1)

    print(f"JWT_SECRET loaded from Infisical: {JWT_SECRET[:8]}...")
    print(f"Starting Proxy Server on https://localhost:8443")
    print(f"Using CA: {ca_file}")
    uvicorn.run(app, host="0.0.0.0", port=8443, ssl_keyfile=str(key_file), ssl_certfile=str(cert_file))
