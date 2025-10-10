import asyncio
from fastmcp import Client
from fastmcp.client.transports import StdioTransport

async def test_http_server_proxy():
    """http_server_proxy.py를 통해 HTTP 서버의 도구들을 테스트합니다."""
    
    # stdio transport를 통해 프록시에 연결
    transport = StdioTransport(
        command="python",
        args=["http_server_proxy.py"]
    )
    client = Client(transport)
    
    try:
        async with client:
            print("=== HTTP Server Proxy 테스트 시작 ===\n")
            
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
            print("   입력: name='Proxy User'")
            result = await client.call_tool("create_greeting", {"name": "Proxy User"})
            print(f"   결과: {result}")
            print()
            
            print("   입력: name='MCP Developer'")
            result = await client.call_tool("create_greeting", {"name": "MCP Developer"})
            print(f"   결과: {result}")
            print()
            
            # 프록시 동작 확인
            print("3. 프록시 특징:")
            print("   - stdio 프로토콜로 Claude Code와 연결")
            print("   - HTTP 프로토콜로 백엔드 서버와 통신")
            print("   - JWT 인증이 없는 서버로 누구나 접근 가능")
            print()
            
            print("=== 테스트 완료 ===")
            
    except Exception as e:
        print(f"오류 발생: {e}")
        print("HTTP 서버가 실행 중인지 확인하세요.")
        print("실행 명령: python http_server.py")

if __name__ == "__main__":
    asyncio.run(test_http_server_proxy())