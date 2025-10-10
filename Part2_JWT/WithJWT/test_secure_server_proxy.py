import asyncio
from fastmcp import Client
from fastmcp.client.transports import StdioTransport

async def test_secure_server_proxy():
    """secure_http_server_proxy.py를 통해 JWT 인증 없이 간편하게 보안 서버와 통신"""
    
    print("=== 보안 서버 프록시 통신 테스트 ===\n")
    
    # stdio transport를 통해 프록시에 연결
    transport = StdioTransport(
        command="python",
        args=["secure_http_server_proxy.py"]
    )
    client = Client(transport)
    
    try:
        async with client:
            print("✅ 보안 서버 프록시 연결 성공!")
            print("   프록시가 JWT 인증을 자동으로 처리합니다.\n")
            
            # 1. 사용 가능한 도구 목록 확인
            print("📋 1단계: 사용 가능한 도구 목록")
            tools = await client.list_tools()
            for tool in tools:
                print(f"   - {tool.name}: {tool.description}")
            print()
            
            # 2. JWT 인증된 add 도구 호출 (프록시가 자동 처리)
            print("📋 2단계: 보호된 add 도구 호출 (JWT 자동 인증)")
            result = await client.call_tool("add", {"a": 42, "b": 58})
            print(f"   ✅ 계산 결과: 42 + 58 = {result}")
            print("   JWT 토큰이 프록시에 의해 자동으로 추가되었습니다.")
            print()
            
            # 3. JWT 인증된 create_greeting 도구 호출
            print("📋 3단계: 보호된 create_greeting 도구 호출 (JWT 자동 인증)")
            greeting = await client.call_tool("create_greeting", {"name": "Secure User"})
            print(f"   ✅ 인사말: {greeting}")
            print("   JWT 토큰이 프록시에 의해 자동으로 추가되었습니다.")
            print()
            
            # 4. 연속 요청 테스트
            print("📋 4단계: 연속 요청 테스트")
            for i in range(3):
                result = await client.call_tool("add", {"a": i*10, "b": i*5})
                print(f"   요청 {i+1}: {i*10} + {i*5} = {result} ✅")
            print()
            
            print("🎯 프록시 통신 테스트 결과:")
            print("   ✅ 프록시를 통해 JWT 인증이 투명하게 처리됨")
            print("   ✅ 클라이언트는 JWT 토큰을 직접 관리할 필요 없음")
            print("   ✅ 모든 보호된 도구에 정상 접근 가능")
            print("   ✅ 연속 요청이 안정적으로 처리됨")
            
            print("\n📝 JWT 프록시 패턴의 장점:")
            print("   🔐 클라이언트 코드 단순화: JWT 처리 로직 불필요")
            print("   🔐 중앙화된 인증: 프록시에서 토큰 관리")
            print("   🔐 보안 분리: 비즈니스 로직과 인증 로직 분리")
            print("   🔐 투명한 보안: 기존 MCP 클라이언트 코드 변경 없음")
            
    except Exception as e:
        print(f"❌ 프록시 연결 실패: {e}")
        print("다음을 확인하세요:")
        print("1. secure_http_server.py가 실행 중인지 확인")
        print("2. secure_http_server_proxy.py가 올바르게 구성되었는지 확인")

if __name__ == "__main__":
    asyncio.run(test_secure_server_proxy())