import asyncio
from fastmcp import FastMCP

# FastMCP 서버 인스턴스를 생성합니다.
mcp = FastMCP("SimpleCalculator")


@mcp.tool()
async def add(a: int, b: int) -> int:
    """
    두 개의 정수를 더합니다.

    :param a: 첫 번째 숫자
    :param b: 두 번째 숫자
    :return: 두 숫자의 합
    """
    print(f"Executing add tool with: a={a}, b={b}")
    return a + b


@mcp.tool()
async def create_greeting(name: str) -> str:
    """
    주어진 이름으로 환영 메시지를 생성합니다.

    :param name: 인사할 사람의 이름
    :return: "Hello, {name}!..." 형태의 환영 메시지
    """
    print(f"Executing create_greeting tool with: name={name}")
    return f"Hello, {name}! Welcome to the world of MCP."

if __name__ == "__main__":
    ip = "127.0.0.1"
    port = 8000
    print(f"Starting MCP server on http://{ip}:{port}")
    print(f"MCP endpoint is available at http://{ip}:{port}/mcp")
    # FastMCP가 내부적으로 uvicorn과 같은 ASGI 서버를 사용하여 실행합니다.
    mcp.run(transport="http", host=ip, port=port)
