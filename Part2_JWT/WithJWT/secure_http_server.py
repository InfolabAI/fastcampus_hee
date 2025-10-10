import asyncio
from fastmcp import FastMCP
from fastmcp.server.auth import JWTVerifier
from typing import Optional

# JWT 검증기를 위한 RSA 키 페어 생성 (개발/테스트용)
from fastmcp.server.auth.providers.jwt import RSAKeyPair

# 개발/테스트용 키 페어 생성
key_pair = RSAKeyPair.generate()

# JWT 토큰 생성 함수 (RSA 키 페어 사용) - 실습용으로만 사용
def generate_jwt_token(user_id: str, permissions: list = None) -> str:
    """JWT 토큰을 생성합니다. (실제 운영환경에서는 별도 인증 서버에서 처리)"""
    return key_pair.create_token(
        subject=user_id,
        audience="mcp-server",
        scopes=permissions or ['read', 'calculate'],
        expires_in_seconds=24*3600  # 24시간
    )

# 실습용 미리 발급된 유효한 JWT 토큰들
VALID_TOKENS = {
    "legitimate_user": generate_jwt_token("legitimate_user"),
    "test_user": generate_jwt_token("test_user"),
    "admin": generate_jwt_token("admin")
}

# JWT 검증기 설정
auth = JWTVerifier(
    public_key=key_pair.public_key,
    audience="mcp-server"
)

# FastMCP 서버 인스턴스를 JWT 인증과 함께 생성
mcp = FastMCP("SecureCalculator", auth=auth)

@mcp.tool()
async def add(a: int, b: int) -> int:
    """
    두 개의 정수를 더합니다. (JWT 인증 필요)

    :param a: 첫 번째 숫자
    :param b: 두 번째 숫자
    :return: 두 숫자의 합
    """
    print(f"Executing authenticated add tool with: a={a}, b={b}")
    return a + b

@mcp.tool()
async def create_greeting(name: str) -> str:
    """
    주어진 이름으로 환영 메시지를 생성합니다. (JWT 인증 필요)

    :param name: 인사할 사람의 이름
    :return: "Hello, {name}!..." 형태의 환영 메시지
    """
    print(f"Executing authenticated create_greeting tool with: name={name}")
    return f"Hello, {name}! Welcome to the secure world of MCP."

if __name__ == "__main__":
    print("Starting Secure MCP server on http://127.0.0.1:8001")
    print("MCP endpoint is available at http://127.0.0.1:8001/mcp")
    print("This server requires JWT authentication for all tools")
    print("\n=== 실습용 미리 발급된 유효한 JWT 토큰들 ===")
    for user, token in VALID_TOKENS.items():
        print(f"{user}: {token[:50]}...")
    print("\n실제 운영환경에서는 별도 인증 서버에서 토큰을 발급받아야 합니다.")
    
    # 프록시가 사용할 수 있도록 토큰을 파일에 저장
    import os
    token_file = os.path.join(os.path.dirname(__file__), ".token")
    with open(token_file, "w") as f:
        f.write(VALID_TOKENS["legitimate_user"])
    print(f"\n토큰이 {token_file}에 저장되었습니다 (프록시 사용을 위해)")
    
    # JWT 인증이 적용된 서버 실행
    mcp.run(transport="http", host="127.0.0.1", port=8001)