# fastmcp 라이브러리에서 FastMCP 클래스를 임포트합니다.
from fastmcp import FastMCP

# FastMCP.as_proxy() 클래스 메소드를 사용하여 원격 MCP 서버에 대한 프록시를 생성합니다.
# 이 프록시는 원격 서버의 도구를 마치 로컬에 있는 것처럼 호출할 수 있게 해줍니다.
# http_server.py가 http://127.0.0.1:8000/mcp 엔드포인트에서 실행 중이라고 가정합니다.
proxy = FastMCP.as_proxy(
    "http://127.0.0.1:8000/mcp",  # 프록시가 연결할 원격 HTTP MCP 서버의 URL입니다.
    name="HTTP Server Proxy"      # 프록시 서버의 이름입니다.
)

# 이 스크립트가 직접 실행될 때 main 로직을 수행합니다.
if __name__ == "__main__":
    # proxy.run() 메소드를 호출하여 프록시 서버를 실행합니다.
    # transport 파라미터를 지정하지 않으면 기본값인 "stdio"로 설정됩니다.
    # "stdio" transport는 표준 입출력(standard input/output)을 통해 통신하며,
    # Claude Code와 같은 개발 환경에서 MCP 서버를 통합할 때 사용됩니다.
    proxy.run()  # 기본값이 STDIO transport
