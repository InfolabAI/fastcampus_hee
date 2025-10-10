from fastmcp import FastMCP

# 원격 HTTP 서버에 대한 프록시 생성
# http_server.py가 http://127.0.0.1:8000/mcp에서 실행 중이라고 가정
proxy = FastMCP.as_proxy(
    "http://127.0.0.1:8000/mcp",  # 원격 HTTP 서버 URL
    name="HTTP Server Proxy"
)

if __name__ == "__main__":
    # STDIO transport로 실행하여 Claude Code에서 사용 가능하게 함
    proxy.run()  # 기본값이 STDIO transport