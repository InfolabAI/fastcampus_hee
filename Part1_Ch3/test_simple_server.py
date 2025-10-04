import asyncio
from fastmcp import Client
from fastmcp.client.transports import StdioTransport


async def test_simple_server():
    """simple_server.py의 도구들을 테스트합니다."""

    # stdio transport를 직접 생성
    transport = StdioTransport(
        command="python",
        args=["simple_server.py"]
    )
    client = Client(transport)

    try:
        async with client:
            print("=== Simple Server 테스트 시작 ===\n")

            # 사용 가능한 도구 목록 확인
            tools = await client.list_tools()
            print("사용 가능한 도구:")
            for tool in tools:
                print(f"  - {tool.name}: {tool.description}")
            print()

            # add 도구 테스트
            print("1. add 도구 테스트:")
            print("   입력: a=5, b=3")
            result = await client.call_tool("add", {"a": 5, "b": 3})
            print(f"   결과: {result}")
            print()

            print("   입력: a=100, b=200")
            result = await client.call_tool("add", {"a": 100, "b": 200})
            print(f"   결과: {result}")
            print()

            # create_greeting 도구 테스트
            print("2. create_greeting 도구 테스트:")
            print("   입력: name='HTTP User'")
            result = await client.call_tool("create_greeting", {"name": "HTTP User"})
            print(f"   결과: {result}")
            print()

            print("   입력: name='MCP Developer'")
            result = await client.call_tool("create_greeting", {"name": "MCP Developer"})
            print(f"   결과: {result}")
            print()

            print("=== 테스트 완료 ===")

    except Exception as e:
        print(f"오류 발생: {e}")

if __name__ == "__main__":
    asyncio.run(test_simple_server())
