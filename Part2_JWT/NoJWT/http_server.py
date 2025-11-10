# asyncio 라이브러리를 임포트하여 비동기 함수를 정의할 수 있게 합니다.
import asyncio
# fastmcp 라이브러리에서 FastMCP 클래스를 임포트하여 MCP 서버를 생성합니다.
from fastmcp import FastMCP

# "SimpleCalculator"라는 이름으로 FastMCP 서버 인스턴스를 생성합니다.
# 이 이름은 서버를 식별하는 데 사용됩니다.
mcp = FastMCP("SimpleCalculator")

# @mcp.tool() 데코레이터를 사용하여 'add' 함수를 MCP 도구로 등록합니다.
# 이 도구는 외부 클라이언트가 호출할 수 있습니다.
@mcp.tool()
async def add(a: int, b: int) -> int:
    """
    두 개의 정수를 더합니다.

    :param a: 첫 번째 숫자
    :param b: 두 번째 숫자
    :return: 두 숫자의 합
    """
    # 도구가 실행될 때 입력 파라미터를 콘솔에 출력합니다.
    print(f"Executing add tool with: a={a}, b={b}")
    # 두 정수를 더한 결과를 반환합니다.
    return a + b

# @mcp.tool() 데코레이터를 사용하여 'create_greeting' 함수를 MCP 도구로 등록합니다.
@mcp.tool()
async def create_greeting(name: str) -> str:
    """
    주어진 이름으로 환영 메시지를 생성합니다.

    :param name: 인사할 사람의 이름
    :return: "Hello, {name}! Welcome to the world of MCP." 형태의 환영 메시지
    """
    # 도구가 실행될 때 입력 파라미터를 콘솔에 출력합니다.
    print(f"Executing create_greeting tool with: name={name}")
    # 환영 메시지를 생성하여 반환합니다.
    return f"Hello, {name}! Welcome to the world of MCP."

# 이 스크립트가 직접 실행될 때 main 로직을 수행합니다.
if __name__ == "__main__":
    # 서버가 시작되었음을 알리고, 접속할 수 있는 주소를 안내합니다.
    print("Starting MCP server on http://127.0.0.1:8000")
    print("MCP endpoint is available at http://127.0.0.1:8000/mcp")
    # mcp.run() 메소드를 호출하여 MCP 서버를 실행합니다.
    # transport="http"는 HTTP 프로토콜을 사용하도록 지정합니다.
    # host와 port는 서버가 바인딩할 주소와 포트를 설정합니다.
    # FastMCP는 내부적으로 uvicorn과 같은 ASGI 서버를 사용하여 비동기 웹 애플리케이션을 실행합니다.
    mcp.run(transport="http", host="127.0.0.1", port=8000)