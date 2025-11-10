# 필요한 라이브러리와 클래스를 가져옵니다.
from fastmcp import FastMCP, Client  # FastMCP 서버/클라이언트 생성 클래스
from fastmcp.client.auth import BearerAuth  # Bearer 토큰 인증을 위한 클래스

# --- JWT 토큰 로드 ---
# `secure_http_server.py`가 실행될 때 생성하고 파일에 저장한 JWT 토큰을 읽어옵니다.
# 이를 통해 프록시는 보안 서버에 인증된 요청을 보낼 수 있습니다.


def get_jwt_token():
    """
    `.token` 파일에서 JWT 토큰을 읽어옵니다.
    이 파일은 `secure_http_server.py`에 의해 생성됩니다.
    """
    try:
        import os

        # 현재 파일과 동일한 디렉토리에 있는 .token 파일의 경로를 구성합니다.
        token_file = os.path.join(os.path.dirname(__file__), ".token")

        # 파일이 존재하는지 확인합니다.
        if os.path.exists(token_file):
            # 파일을 열고 내용을 읽어와 앞뒤 공백을 제거합니다.
            with open(token_file, "r") as f:
                token = f.read().strip()
            print(f"서버에서 저장한 JWT 토큰 읽기 성공: {token}...")
            return token
        else:
            # 파일이 없으면 오류 메시지를 출력합니다.
            print(f"토큰 파일을 찾을 수 없습니다: {token_file}")
            print("secure_http_server.py를 먼저 실행하여 토큰 파일을 생성하세요.")
            return None

    except Exception as e:
        # 파일 읽기 중 다른 예외가 발생하면 오류 메시지를 출력합니다.
        print(f"JWT 토큰 읽기 실패: {e}")
        return None


# get_jwt_token 함수를 호출하여 토큰을 가져옵니다.
jwt_token = get_jwt_token()

# --- 인증된 MCP 클라이언트 생성 ---
# 이 프록시가 내부적으로 사용할 MCP 클라이언트를 생성합니다.
# 이 클라이언트는 실제 보안 서버(secure_http_server)와 통신하는 역할을 합니다.
authenticated_client = Client(
    "http://127.0.0.1:8001/mcp",  # 실제 보안 서버의 MCP 엔드포인트 주소
    # `auth` 파라미터에 `BearerAuth`를 설정합니다.
    # 이렇게 하면 이 클라이언트가 보내는 모든 요청의 `Authorization` 헤더에
    # "Bearer <jwt_token>"이 자동으로 추가됩니다.
    auth=BearerAuth(token=jwt_token)
)

# --- FastMCP 프록시 생성 ---
# `FastMCP.as_proxy()`를 사용하여 프록시 서버를 생성합니다.
# 이 프록시는 외부(예: 다른 MCP 클라이언트)로부터 요청을 받아서,
# 내부적으로 `authenticated_client`를 통해 실제 서버로 전달하는 역할을 합니다.
# 이 과정에서 JWT 인증이 자동으로 처리되므로, 프록시에 연결하는 클라이언트는
# JWT 토큰에 대해 전혀 신경 쓸 필요가 없습니다.
proxy = FastMCP.as_proxy(
    authenticated_client,  # 내부적으로 사용할 인증된 클라이언트
    name="Secure HTTP Server Proxy with Auto JWT"  # 프록시 서버의 이름
)

# 이 스크립트가 직접 실행될 때 main 함수 역할을 하는 부분입니다.
if __name__ == "__main__":
    # 프록시 서버 시작을 알리는 메시지를 출력합니다.
    print("Starting Secure HTTP Server Proxy with automatic JWT authentication")
    print(f"Connecting to: http://127.0.0.1:8001/mcp")
    print("JWT token automatically added to all requests via BearerAuth")
    print("STDIO transport enabled for MCP client connections")

    # 프록시 서버를 실행합니다.
    # `proxy.run()`은 기본적으로 STDIO(Standard Input/Output) transport를 사용합니다.
    # 이는 다른 프로세스(예: `test_secure_server_proxy.py`)가 이 프록시를
    # 자식 프로세스로 실행하고 표준 입출력을 통해 통신할 수 있게 해줍니다.
    proxy.run()
