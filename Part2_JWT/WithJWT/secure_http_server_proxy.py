from fastmcp import FastMCP, Client
from fastmcp.client.auth import BearerAuth

# 서버에서 저장한 토큰 파일을 읽어서 사용
def get_jwt_token():
    """서버에서 저장한 .token 파일을 읽어서 JWT 토큰 가져오기"""
    try:
        import os
        
        # 서버가 저장한 토큰 파일 경로
        token_file = os.path.join(os.path.dirname(__file__), ".token")
        
        if os.path.exists(token_file):
            with open(token_file, "r") as f:
                token = f.read().strip()
            print(f"서버에서 저장한 JWT 토큰 읽기 성공: {token[:50]}...")
            return token
        else:
            print(f"토큰 파일을 찾을 수 없습니다: {token_file}")
            print("secure_http_server.py를 먼저 실행하여 토큰 파일을 생성하세요.")
            return None
        
    except Exception as e:
        print(f"JWT 토큰 읽기 실패: {e}")
        return None

# JWT 토큰 생성
jwt_token = get_jwt_token()

# JWT 인증이 적용된 클라이언트 생성
authenticated_client = Client(
    "http://127.0.0.1:8001/mcp",
    auth=BearerAuth(token=jwt_token)
)

# JWT 인증을 자동으로 처리하는 보안 HTTP 서버 프록시 생성
proxy = FastMCP.as_proxy(
    authenticated_client,
    name="Secure HTTP Server Proxy with Auto JWT"
)

if __name__ == "__main__":
    print("Starting Secure HTTP Server Proxy with automatic JWT authentication")
    print(f"Connecting to: http://127.0.0.1:8001/mcp")
    print("JWT token automatically added to all requests via BearerAuth")
    print("STDIO transport enabled for MCP client connections")
    
    # STDIO transport로 실행하여 Claude Code에서 사용 가능하게 함
    proxy.run()  # 기본값이 STDIO transport