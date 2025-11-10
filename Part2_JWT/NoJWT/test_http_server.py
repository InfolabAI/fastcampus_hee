# asyncio 라이브러리를 임포트하여 비동기 작업을 지원합니다.
import asyncio
# fastmcp 라이브러리에서 Client 클래스를 임포트하여 MCP 서버에 연결합니다.
from fastmcp import Client

# 비동기 함수로 HTTP 서버 테스트를 정의합니다.
async def test_http_server():
    """http_server.py의 도구들을 테스트합니다."""
    
    # 로컬호스트의 8000번 포트에서 실행 중인 MCP 서버의 http 전송용 엔드포인트 URL을 사용하여 클라이언트를 생성합니다.
    # 이 클라이언트는 http_server.py에 직접 연결하여 테스트합니다.
    client = Client("http://127.0.0.1:8000/mcp")
    
    try:
        # client 컨텍스트 매니저를 사용하여 서버와의 연결을 관리합니다.
        async with client:
            # 테스트 시작을 알리는 메시지를 출력합니다.
            print("=== HTTP Server 테스트 시작 ===\n")
            
            # 서버에 ping을 보내 연결 상태를 확인합니다.
            await client.ping()
            print("서버 연결 성공!\n")
            
            # 서버에서 사용 가능한 도구 목록을 가져와 출력합니다.
            tools = await client.list_tools()
            print("사용 가능한 도구:")
            for tool in tools:
                print(f"  - {tool.name}: {tool.description}")
            print()
            
            # 'add' 도구를 테스트합니다.
            print("1. add 도구 테스트:")
            # 첫 번째 테스트 케이스: a=5, b=3
            print("   입력: a=5, b=3")
            result = await client.call_tool("add", {"a": 5, "b": 3})
            print(f"   결과: {result}")
            print()
            
            # 두 번째 테스트 케이스: a=100, b=200
            print("   입력: a=100, b=200")
            result = await client.call_tool("add", {"a": 100, "b": 200})
            print(f"   결과: {result}")
            print()
            
            # 'create_greeting' 도구를 테스트합니다.
            print("2. create_greeting 도구 테스트:")
            # 첫 번째 테스트 케이스: name='HTTP User'
            print("   입력: name='HTTP User'")
            result = await client.call_tool("create_greeting", {"name": "HTTP User"})
            print(f"   결과: {result}")
            print()
            
            # 두 번째 테스트 케이스: name='MCP Developer'
            print("   입력: name='MCP Developer'")
            result = await client.call_tool("create_greeting", {"name": "MCP Developer"})
            print(f"   결과: {result}")
            print()
            
            # 모든 테스트가 완료되었음을 알립니다.
            print("=== 테스트 완료 ===")
            
    # 서버 연결 실패 등 예외 발생 시 처리합니다.
    except Exception as e:
        print(f"오류 발생: {e}")
        print("HTTP 서버가 실행 중인지 확인하세요.")
        print("실행 명령: python http_server.py")

# 이 스크립트가 직접 실행될 때 main 로직을 수행합니다.
if __name__ == "__main__":
    # 비동기 함수인 test_http_server를 실행합니다.
    asyncio.run(test_http_server())
