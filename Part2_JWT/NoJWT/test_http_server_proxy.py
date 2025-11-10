# asyncio 라이브러리를 임포트하여 비동기 작업을 지원합니다.
import asyncio
# fastmcp 라이브러리에서 Client 클래스를 임포트하여 MCP 서버에 연결합니다.
from fastmcp import Client
# fastmcp.client.transports 모듈에서 StdioTransport 클래스를 임포트하여 표준 입출력 기반 통신을 사용합니다.
from fastmcp.client.transports import StdioTransport

# 비동기 함수로 HTTP 서버 프록시 테스트를 정의합니다.
async def test_http_server_proxy():
    """http_server_proxy.py를 통해 HTTP 서버의 도구들을 테스트합니다."""
    
    # StdioTransport를 사용하여 프록시 서버(http_server_proxy.py)를 자식 프로세스로 실행하고 통신합니다.
    # command="python"은 'python' 명령어를 사용하여 스크립트를 실행하도록 지정합니다.
    # args=["http_server_proxy.py"]는 실행할 스크립트 파일을 지정합니다.
    transport = StdioTransport(
        command="python",
        args=["http_server_proxy.py"]
    )
    # 생성된 transport를 사용하여 MCP 클라이언트를 초기화합니다.
    client = Client(transport)
    
    try:
        # client 컨텍스트 매니저를 사용하여 프록시 서버와의 연결을 관리합니다.
        async with client:
            # 테스트 시작을 알리는 메시지를 출력합니다.
            print("=== HTTP Server Proxy 테스트 시작 ===\n")
            
            # 프록시를 통해 원격 서버의 사용 가능한 도구 목록을 가져와 출력합니다.
            tools = await client.list_tools()
            print("사용 가능한 도구:")
            for tool in tools:
                print(f"  - {tool.name}: {tool.description}")
            print()
            
            # 프록시를 통해 'add' 도구를 테스트합니다.
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
            
            # 프록시를 통해 'create_greeting' 도구를 테스트합니다.
            print("2. create_greeting 도구 테스트:")
            # 첫 번째 테스트 케이스: name='Proxy User'
            print("   입력: name='Proxy User'")
            result = await client.call_tool("create_greeting", {"name": "Proxy User"})
            print(f"   결과: {result}")
            print()
            
            # 두 번째 테스트 케이스: name='MCP Developer'
            print("   입력: name='MCP Developer'")
            result = await client.call_tool("create_greeting", {"name": "MCP Developer"})
            print(f"   결과: {result}")
            print()
            
            # 프록시 서버의 동작 방식을 설명합니다.
            print("3. 프록시 특징:")
            print("   - stdio 프로토콜로 Claude Code와 연결")
            print("   - HTTP 프로토콜로 백엔드 서버와 통신")
            print("   - JWT 인증이 없는 서버로 누구나 접근 가능")
            print()
            
            # 모든 테스트가 완료되었음을 알립니다.
            print("=== 테스트 완료 ===")
            
    # 프록시 서버 연결 실패 등 예외 발생 시 처리합니다.
    except Exception as e:
        print(f"오류 발생: {e}")
        print("HTTP 서버가 실행 중인지 확인하세요.")
        print("실행 명령: python http_server.py")

# 이 스크립트가 직접 실행될 때 main 로직을 수행합니다.
if __name__ == "__main__":
    # 비동기 함수인 test_http_server_proxy를 실행합니다.
    asyncio.run(test_http_server_proxy())
