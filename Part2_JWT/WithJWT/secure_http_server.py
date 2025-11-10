# 필요한 라이브러리와 클래스를 가져옵니다.
import asyncio  # 비동기 작업을 위한 라이브러리 (여기서는 직접 사용되지 않음)
from fastmcp import FastMCP  # FastMCP 서버 생성 클래스
from fastmcp.server.auth import JWTVerifier  # JWT 토큰 검증을 위한 클래스
from typing import Optional  # 타입 힌트를 위한 라이브러리

# JWT 토큰 생성 및 검증에 필요한 RSA 키 페어를 다루는 클래스를 가져옵니다.
from fastmcp.server.auth.providers.jwt import RSAKeyPair

# --- JWT 키 및 토큰 생성 (실습용) ---
# 실제 운영 환경에서는 인증 서버가 별도로 존재하며, 키 관리 또한 안전하게 이루어져야 합니다.
# 여기서는 실습의 편의를 위해 서버 코드 내에서 키 페어를 생성하고 토큰을 발급합니다.

# RSAKeyPair.generate()를 호출하여 새로운 RSA 공개키/개인키 쌍을 생성합니다.
# 이 키 페어는 JWT 토큰의 서명 생성 및 검증에 사용됩니다.
key_pair = RSAKeyPair.generate()

# 실습용 JWT 토큰을 생성하는 함수입니다.
def generate_jwt_token(user_id: str, permissions: list = None) -> str:
    """
    주어진 사용자 ID와 권한으로 JWT 토큰을 생성합니다.
    실제 운영 환경에서는 이 기능이 별도의 인증 서버에 구현되어야 합니다.
    """
    # key_pair.create_token() 메소드를 사용하여 토큰을 생성합니다.
    return key_pair.create_token(
        subject=user_id,  # 토큰의 주체 (일반적으로 사용자 ID)
        audience="mcp-server",  # 토큰의 대상 (이 토큰을 사용할 서비스)
        scopes=permissions or ['read', 'calculate'],  # 사용자의 권한 범위
        expires_in_seconds=24*3600  # 토큰 만료 시간 (초 단위, 여기서는 24시간)
    )

# 테스트를 위해 미리 여러 개의 유효한 JWT 토큰을 생성해 둡니다.
VALID_TOKENS = {
    "legitimate_user": generate_jwt_token("legitimate_user"),
    "test_user": generate_jwt_token("test_user"),
    "admin": generate_jwt_token("admin", permissions=['read', 'calculate', 'admin'])
}

# --- JWT 검증기 설정 ---
# 클라이언트로부터 받은 JWT 토큰을 검증할 JWTVerifier 인스턴스를 생성합니다.
auth = JWTVerifier(
    public_key=key_pair.public_key,  # 토큰 서명 검증에 사용할 공개키
    audience="mcp-server"  # 토큰의 'aud' 필드가 이 값과 일치해야 함
)

# --- FastMCP 서버 설정 ---
# FastMCP 서버 인스턴스를 생성하면서 `auth` 파라미터에 위에서 만든 JWTVerifier를 전달합니다.
# 이렇게 하면 이 서버의 모든 도구에 대한 요청은 자동으로 JWT 인증을 거치게 됩니다.
mcp = FastMCP("SecureCalculator", auth=auth)

# --- 보안이 적용된 도구 정의 ---
# @mcp.tool() 데코레이터를 사용하여 서버에 등록될 도구를 정의합니다.
# 서버에 `auth`가 설정되었으므로, 이 도구들은 모두 JWT 인증을 통과해야만 호출될 수 있습니다.

@mcp.tool()
async def add(a: int, b: int) -> int:
    """
    두 개의 정수를 더합니다. (JWT 인증 필요)
    이 도구를 호출하려면 유효한 JWT 토큰이 Authorization 헤더에 포함되어야 합니다.
    """
    print(f"Executing authenticated add tool with: a={a}, b={b}")
    return a + b

@mcp.tool()
async def create_greeting(name: str) -> str:
    """
    주어진 이름으로 환영 메시지를 생성합니다. (JWT 인증 필요)
    이 도구를 호출하려면 유효한 JWT 토큰이 Authorization 헤더에 포함되어야 합니다.
    """
    print(f"Executing authenticated create_greeting tool with: name={name}")
    return f"Hello, {name}! Welcome to the secure world of MCP."

# 이 스크립트가 직접 실행될 때 main 함수 역할을 하는 부분입니다.
if __name__ == "__main__":
    # 서버 시작을 알리는 메시지를 출력합니다.
    print("Starting Secure MCP server on http://127.0.0.1:8001")
    print("MCP endpoint is available at http://127.0.0.1:8001/mcp")
    print("This server requires JWT authentication for all tools")
    
    # 실습용으로 생성된 토큰들을 출력하여 사용자가 테스트에 활용할 수 있도록 합니다.
    print("\n=== 실습용 미리 발급된 유효한 JWT 토큰들 ===")
    for user, token in VALID_TOKENS.items():
        print(f"{user}: {token[:50]}...")
    print("\n실제 운영환경에서는 별도 인증 서버에서 토큰을 발급받아야 합니다.")
    
    # --- 프록시 서버와의 연동을 위한 토큰 저장 ---
    # `secure_http_server_proxy.py`가 이 서버에 연결할 때 사용할 수 있도록
    # 생성된 토큰 중 하나를 파일에 저장합니다.
    import os
    # 토큰을 저장할 파일 경로를 지정합니다.
    token_file = os.path.join(os.path.dirname(__file__), ".token")
    # 파일을 열고 토큰을 씁니다.
    with open(token_file, "w") as f:
        f.write(VALID_TOKENS["legitimate_user"])
    print(f"\n토큰이 {token_file}에 저장되었습니다 (프록시 사용을 위해)")
    
    # JWT 인증이 활성화된 FastMCP 서버를 실행합니다.
    # transport="http"로 설정하여 HTTP 기반으로 통신합니다.
    mcp.run(transport="http", host="127.0.0.1", port=8001)
