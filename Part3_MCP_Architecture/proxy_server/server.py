#!/usr/bin/env python3
"""FastAPI Proxy Server with JWT + Casbin + Multi-tenant routing
JWT_SECRET must be loaded from Infisical (no hardcoding)
"""
# =============================================================================
# Proxy Server - 중앙 프록시 서버 (멀티테넌트 라우팅)
# =============================================================================
# 역할: MCP 클라이언트 요청을 적절한 백엔드로 라우팅
# 인증: JWT 토큰 검증 (Infisical에서 시크릿 로드)
# 인가: Casbin RBAC 정책으로 접근 제어
# 흐름: Proxy MCP -> [HTTPS+JWT] -> Proxy Server -> [stdin/stdout] -> Backend
# =============================================================================

import os, json, subprocess, sys  # os: 환경변수, json: 직렬화, subprocess: 백엔드 프로세스
from pathlib import Path  # 파일 경로 처리
from datetime import datetime  # 타임스탬프 로깅
from fastapi import FastAPI, HTTPException, Depends  # FastAPI 웹 프레임워크
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials  # Bearer 토큰 인증
from authlib.jose import jwt  # JWT 토큰 검증
from pydantic import BaseModel  # 요청 스키마 정의
import casbin  # RBAC 정책 엔진

# -----------------------------------------------------------------------------
# 경로 설정
# -----------------------------------------------------------------------------
BASE_DIR = Path(__file__).parent.parent  # 프로젝트 루트 디렉토리
DATA_DIR = BASE_DIR / "data"  # SQLite DB 저장 디렉토리
DATA_DIR.mkdir(exist_ok=True)  # 디렉토리 생성 (없으면)

# -----------------------------------------------------------------------------
# 시크릿 로드 - Infisical에서 주입 (하드코딩 금지)
# -----------------------------------------------------------------------------
JWT_SECRET = os.getenv("JWT_SECRET")  # 환경변수에서 JWT 시크릿 로드
if not JWT_SECRET:
    print("ERROR: JWT_SECRET not set. Run with: infisical run -- python server.py")
    sys.exit(1)

# -----------------------------------------------------------------------------
# FastAPI 앱 및 보안 설정
# -----------------------------------------------------------------------------
app = FastAPI()  # FastAPI 앱 인스턴스
security = HTTPBearer()  # Bearer 토큰 인증 스킴
enforcer = casbin.Enforcer(str(Path(__file__).parent / "model.conf"), str(Path(__file__).parent / "policy.csv"))  # Casbin: model.conf(RBAC 모델) + policy.csv(정책 규칙)
BACKENDS = {}  # 백엔드 프로세스 캐시 {tenant: subprocess.Popen}

# -----------------------------------------------------------------------------
# 요청 스키마 정의
# -----------------------------------------------------------------------------
class MCPRequest(BaseModel):
    """MCP 요청 스키마 - Pydantic 모델로 자동 검증"""
    method: str  # CRUD 메서드: insert, update, select
    params: dict = {}  # 메서드 파라미터 (선택적)

# -----------------------------------------------------------------------------
# 로깅 함수들 - 디버깅 및 감사 로그
# -----------------------------------------------------------------------------
def log_debug(tenant: str, request: dict, response: dict, allowed: bool, backend: str, extra: dict = None):
    """요청/응답 로깅 - 감사 및 디버깅용"""
    log_entry = {
        "timestamp": datetime.utcnow().isoformat(),  # UTC 타임스탬프
        "tenant": tenant,  # 요청 테넌트
        "request": request,  # 요청 내용
        "response": response,  # 응답 내용
        "allowed": allowed,  # Casbin 인가 결과
        "backend": backend  # 대상 백엔드
    }
    if extra:
        log_entry.update(extra)  # 추가 정보 병합
    with open(BASE_DIR / "proxy_server" / "debug.log", "a") as f:
        f.write(json.dumps(log_entry) + "\n")  # 파일에 JSON 라인 추가
    print(f"[LOG] {json.dumps(log_entry)}")  # stderr로 실시간 출력

def log_casbin_decision(subject: str, obj: str, action: str, allowed: bool):
    """Casbin 정책 평가 결과 로깅 - RBAC 감사용"""
    log_entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "type": "CASBIN_DECISION",  # 로그 타입 식별자
        "subject": subject,  # 주체 (tenant_a, tenant_b)
        "object": obj,  # 객체 (backend_a, backend_b)
        "action": action,  # 액션 (access)
        "allowed": allowed,  # 허용 여부
        "policy_rule": f"p, {subject}, {obj}, {action}" if allowed else None,  # 매칭된 정책 규칙
        "message": f"Request: {subject}, {obj}, {action} ---> {allowed}"  # 사람이 읽기 쉬운 메시지
    }
    print(f"[CASBIN] {json.dumps(log_entry)}")  # 콘솔 출력
    with open(BASE_DIR / "proxy_server" / "debug.log", "a") as f:
        f.write(json.dumps(log_entry) + "\n")  # 파일 저장

def log_jwt_verification(claims: dict, success: bool, error: str = None):
    """JWT 검증 결과 로깅 - 인증 감사용"""
    now = datetime.utcnow()
    log_entry = {
        "timestamp": now.isoformat(),
        "type": "JWT_VERIFICATION",  # 로그 타입 식별자
        "success": success,  # 검증 성공 여부
    }
    if success and claims:
        log_entry["tenant"] = claims.get("tenant", "unknown")  # 테넌트 식별자
        if "iat" in claims:  # issued at (발급 시간)
            iat = datetime.utcfromtimestamp(claims["iat"])
            log_entry["jwt_issued_at"] = iat.isoformat()
        if "exp" in claims:  # expiration (만료 시간)
            exp = datetime.utcfromtimestamp(claims["exp"])
            log_entry["jwt_expires_at"] = exp.isoformat()
            remaining = (exp - now).total_seconds()  # 남은 시간 계산
            log_entry["jwt_remaining_sec"] = int(remaining)
            log_entry["jwt_expired"] = remaining <= 0  # 만료 여부
    if error:
        log_entry["error"] = error  # 에러 메시지 (실패 시)
    print(f"[JWT_VERIFY] {json.dumps(log_entry)}")  # 콘솔 출력

# -----------------------------------------------------------------------------
# JWT 검증 함수 - FastAPI 의존성 주입
# -----------------------------------------------------------------------------
def verify_jwt(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """JWT 토큰 검증 - FastAPI Depends로 자동 주입"""
    try:
        claims = jwt.decode(credentials.credentials, JWT_SECRET)  # 토큰 디코드 (서명 검증)
        claims.validate()  # 만료 시간 검증 (exp 클레임)
        claims_dict = dict(claims)  # JWTClaims → dict 변환
        log_jwt_verification(claims_dict, success=True)  # 성공 로깅
        return claims_dict  # 클레임 반환 (tenant 등)
    except Exception as e:
        error_msg = str(e)
        log_jwt_verification(None, success=False, error=error_msg)  # 실패 로깅
        raise HTTPException(status_code=401, detail=f"Invalid token: {e}")  # 401 Unauthorized

# -----------------------------------------------------------------------------
# 백엔드 프로세스 관리 - 서브프로세스로 백엔드 실행
# -----------------------------------------------------------------------------
async def get_backend(tenant: str) -> subprocess.Popen:
    """백엔드 프로세스 가져오기 - 없으면 생성, 있으면 재사용"""
    if tenant in BACKENDS and BACKENDS[tenant].poll() is None:  # 이미 실행 중인지 확인
        return BACKENDS[tenant]  # 기존 프로세스 재사용
    script = BASE_DIR / f"backend_{tenant}" / f"backend_{tenant}.py"  # 백엔드 스크립트 경로
    env = os.environ.copy()  # 현재 환경변수 복사
    env["DB_PATH"] = str(DATA_DIR / f"tenant_{tenant}.db")  # 테넌트별 DB 경로 설정
    proc = subprocess.Popen([sys.executable, str(script)], stdin=subprocess.PIPE,  # stdin으로 요청 전송
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, env=env)  # stdout으로 응답 수신
    BACKENDS[tenant] = proc  # 프로세스 캐시에 저장
    return proc

async def call_backend(tenant: str, method: str, params: dict) -> dict:
    """백엔드에 JSON-RPC 요청 전송 및 응답 수신"""
    proc = await get_backend(tenant)  # 백엔드 프로세스 가져오기
    request = {"jsonrpc": "2.0", "id": 1, "method": method, "params": params}  # JSON-RPC 2.0 형식
    try:
        proc.stdin.write(json.dumps(request) + "\n")  # 요청 전송 (줄바꿈 필수)
        proc.stdin.flush()  # 버퍼 즉시 비우기
        line = proc.stdout.readline()  # 응답 한 줄 읽기
        return json.loads(line) if line else {"error": "No response"}  # JSON 파싱
    except Exception as e:
        return {"error": str(e)}  # 에러 반환

# -----------------------------------------------------------------------------
# API 엔드포인트 - MCP 프록시 및 헬스 체크
# -----------------------------------------------------------------------------
@app.post("/mcp/{target_tenant}")
async def proxy_mcp(target_tenant: str, req: MCPRequest, claims: dict = Depends(verify_jwt)):
    """
    MCP 프록시 엔드포인트 - 인증 후 Casbin 인가 검사 후 백엔드 라우팅
    1. JWT 검증 (verify_jwt 의존성)
    2. Casbin 정책 평가 (tenant → backend 접근 권한)
    3. 백엔드 호출 및 응답 반환
    """
    tenant = claims.get("tenant", "unknown")  # JWT에서 테넌트 추출
    backend_resource = f"backend_{target_tenant}"  # Casbin 객체 이름

    # Casbin 정책 평가: p, tenant_a, backend_a, access → 허용
    allowed = enforcer.enforce(tenant, backend_resource, "access")
    log_casbin_decision(tenant, backend_resource, "access", allowed)

    request_data = {"method": req.method, "params": req.params, "target": target_tenant}

    if not allowed:  # 인가 실패 → 403 Forbidden
        resp = {"error": f"Access denied: {tenant} cannot access {backend_resource}"}
        log_debug(tenant, request_data, resp, False, backend_resource,
                  extra={"casbin_subject": tenant, "casbin_object": backend_resource, "casbin_action": "access"})
        raise HTTPException(status_code=403, detail=resp["error"])

    # 인가 성공 → 백엔드 호출
    resp = await call_backend(target_tenant, req.method, req.params)
    log_debug(tenant, request_data, resp, True, backend_resource,
              extra={"casbin_subject": tenant, "casbin_object": backend_resource, "casbin_action": "access"})
    return resp  # 백엔드 응답 반환

@app.get("/health")
async def health():
    """헬스 체크 엔드포인트 - 로드밸런서/모니터링용"""
    return {"status": "ok"}

# =============================================================================
# 메인 실행부 - HTTPS 서버 시작
# =============================================================================
if __name__ == "__main__":
    import uvicorn  # ASGI 서버
    cert_dir = Path(__file__).parent / "certs"  # 인증서 디렉토리
    cert_file, key_file = cert_dir / "cert.pem", cert_dir / "key.pem"  # 서버 인증서/키
    ca_file = cert_dir / "ca.pem"  # CA 인증서 (클라이언트 피닝용)

    # 인증서 존재 확인 - 없으면 생성 스크립트 안내
    if not cert_file.exists() or not ca_file.exists():
        print("ERROR: TLS certificates not found. Run: bash certs/generate_ca.sh")
        sys.exit(1)

    # 시작 정보 출력
    print(f"JWT_SECRET loaded from Infisical: {JWT_SECRET[:8]}...")  # 시크릿 일부만 출력 (보안)
    print(f"Starting Proxy Server on https://localhost:8443")
    print(f"Using CA: {ca_file}")
    # uvicorn 실행: HTTPS (TLS) 활성화
    uvicorn.run(app, host="0.0.0.0", port=8443, ssl_keyfile=str(key_file), ssl_certfile=str(cert_file))
