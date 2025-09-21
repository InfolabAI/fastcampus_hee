import asyncio
from fastmcp import Client

async def test_http_server():
    """http_server.py의 도구들을 테스트합니다."""
    
    # HTTP 서버에 연결 (서버가 실행 중이어야 함)
    client = Client("http://127.0.0.1:8000/mcp")
    
    try:
        async with client:
            print("=== HTTP Server 테스트 시작 ===\n")
            
            # 서버 상태 확인
            await client.ping()
            print("서버 연결 성공!\n")
            
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
        print("HTTP 서버가 실행 중인지 확인하세요.")
        print("실행 명령: python http_server.py")

if __name__ == "__main__":
    asyncio.run(test_http_server())