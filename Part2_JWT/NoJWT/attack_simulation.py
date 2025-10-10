import asyncio
from fastmcp import Client

async def simulate_attack():
    """공격자가 인증 없이 HTTP MCP 서버에 접근하는 시나리오를 시뮬레이션합니다."""
    
    # HTTP 서버에 연결 (공격자가 직접 접근)
    client = Client("http://127.0.0.1:8000/mcp")
    
    try:
        async with client:
            print("🚨 공격 시뮬레이션 시작 🚨\n")
            print("공격자가 HTTP MCP 서버에 무단 접근을 시도합니다...")
            
            # 서버 연결 확인
            await client.ping()
            print("✅ 서버 연결 성공! (인증 없이 접근 가능)")
            
            # 사용 가능한 도구 탐색 (정찰)
            tools = await client.list_tools()
            print(f"\n🔍 발견된 도구들 ({len(tools)}개):")
            for tool in tools:
                print(f"  - {tool.name}: {tool.description}")
            
            print("\n⚠️  공격자가 모든 도구에 무제한 접근 가능!")
            
            # 1. 정상적인 기능 남용
            print("\n📊 1단계: 정상 기능 남용")
            for i in range(5):
                result = await client.call_tool("add", {"a": 999999, "b": 999999})
                print(f"  악용된 계산 {i+1}: {result}")
            
            # 2. 악의적인 입력 시도
            print("\n💀 2단계: 악의적인 입력 시도")
            malicious_names = [
                "<script>alert('XSS')</script>",
                "'; DROP TABLE users; --",
                "../../../etc/passwd",
                "admin'; DELETE FROM *; --"
            ]
            
            for name in malicious_names:
                try:
                    result = await client.call_tool("create_greeting", {"name": name})
                    print(f"  악의적 입력 시도: {name[:30]}...")
                    print(f"  서버 응답: {result}")
                except Exception as e:
                    print(f"  입력 차단됨: {e}")
            
            # 3. 리소스 고갈 공격 시도
            print("\n🔥 3단계: 리소스 고갈 공격 (DoS)")
            print("  연속으로 대량 요청 전송 중...")
            
            tasks = []
            for i in range(20):  # 20개 동시 요청
                task = client.call_tool("add", {"a": i*100000, "b": i*100000})
                tasks.append(task)
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            success_count = sum(1 for r in results if not isinstance(r, Exception))
            print(f"  {success_count}/{len(tasks)} 요청 성공 - 서버가 모든 요청을 처리함!")
            
            print("\n🎯 공격 결과:")
            print("  ✅ 인증 없이 모든 기능에 접근 가능")
            print("  ✅ 악의적인 입력 주입 시도 가능")
            print("  ✅ 서버 리소스 무제한 사용 가능")
            print("  ⚠️  보안 취약점 확인!")
            
    except Exception as e:
        print(f"❌ 공격 실패: {e}")
        print("HTTP 서버가 실행 중인지 확인하세요.")
        print("실행 명령: python http_server.py")

if __name__ == "__main__":
    asyncio.run(simulate_attack())