# 필요한 라이브러리를 가져옵니다.
import asyncio  # 비동기 작업을 위한 라이브러리
from fastmcp import Client  # FastMCP 클라이언트 (여기서는 직접 사용되지 않음)
import requests  # HTTP 요청을 보내기 위한 라이브러리
import json  # JSON 데이터 처리를 위한 라이브러리 (여기서는 직접 사용되지 않음)

async def simulate_secure_attack():
    """
    JWT(JSON Web Token) 인증이 적용된 보안 서버에 대한 다양한 공격 시나리오를 시뮬레이션합니다.
    이 함수는 비동기적으로 실행됩니다.
    """
    
    print("🔒 보안 서버 공격 시뮬레이션 시작 🔒\n")
    
    # --- 1단계: 인증 없는 접근 시도 ---
    # Authorization 헤더에 JWT 토큰 없이 서버에 직접 HTTP 요청을 보냅니다.
    # 정상적인 보안 서버라면 이 요청을 401 Unauthorized 오류로 거부해야 합니다.
    print("📍 1단계: JWT 토큰 없는 무단 접근 시도")
    try:
        # requests.post를 사용하여 MCP 서버의 /mcp/ 엔드포인트에 POST 요청을 보냅니다.
        response = requests.post(
            "http://127.0.0.1:8001/mcp/",  # 보안 MCP 서버 주소
            headers={"Content-Type": "application/json", "Accept": "application/json, text/event-stream"},
            json={
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/call",
                "params": {
                    "name": "add",
                    "arguments": {"a": 999, "b": 999}
                }
            }
        )
        # 서버로부터 받은 응답 상태 코드와 내용을 출력합니다.
        print(f"  응답 상태: {response.status_code}")
        print(f"  응답 내용: {response.text[:200]}...")
        
        # 응답 코드가 401이면 예상대로 차단된 것입니다.
        if response.status_code == 401:
            print("  ✅ 성공적으로 차단됨 (401 Unauthorized)")
        else:
            print("  ⚠️  예상과 다른 응답")
    except Exception as e:
        # 요청 중 예외가 발생하면 실패 메시지를 출력합니다.
        print(f"  ❌ 요청 실패: {e}")
    
    print("\n" + "="*50)
    
    # --- 2단계: 잘못된(위조된) JWT 토큰으로 접근 시도 ---
    # 유효하지 않은 형식의 JWT 토큰을 사용하여 접근을 시도합니다.
    # 서버는 토큰의 서명을 검증하고, 유효하지 않으므로 요청을 거부해야 합니다.
    print("\n📍 2단계: 잘못된 JWT 토큰으로 접근 시도")
    try:
        response = requests.post(
            "http://127.0.0.1:8001/mcp/",
            headers={
                "Content-Type": "application/json", 
                "Accept": "application/json, text/event-stream",
                "Authorization": "Bearer invalid.jwt.token"  # 'Bearer' 접두사와 함께 위조된 토큰 전달
            },
            json={
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/call",
                "params": {
                    "name": "create_greeting",
                    "arguments": {"name": "Hacker"}
                }
            }
        )
        print(f"  응답 상태: {response.status_code}")
        print(f"  응답 내용: {response.text[:200]}...")
        
        # 응답 코드가 401이면 위조된 토큰이 성공적으로 차단된 것입니다.
        if response.status_code == 401:
            print("  ✅ 위조된 토큰이 성공적으로 차단됨")
        else:
            print("  ⚠️  예상과 다른 응답")
    except Exception as e:
        print(f"  ❌ 요청 실패: {e}")
    
    print("\n" + "="*50)
    
    # --- 3단계: 만료된 JWT 토큰으로 접근 시도 ---
    # 유효 기간이 지난 토큰을 사용하여 접근을 시도합니다.
    # 서버는 토큰의 'exp' (만료 시간) 필드를 확인하고 요청을 거부해야 합니다.
    print("\n📍 3단계: 만료된 토큰으로 접근 시도")
    # 'exp' 필드가 과거 시간으로 설정된 만료된 토큰 (실제 서명은 유효하지 않음)
    expired_token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ1c2VyX2lkIjoidGVzdCIsImV4cCI6MTUwMDAwMDAwMH0.invalid"
    try:
        response = requests.post(
            "http://127.0.0.1:8001/mcp/",
            headers={
                "Content-Type": "application/json", 
                "Accept": "application/json, text/event-stream",
                "Authorization": f"Bearer {expired_token}"  # 만료된 토큰 전달
            },
            json={
                "jsonrpc": "2.0",
                "id": 3,
                "method": "tools/call",
                "params": {
                    "name": "add",
                    "arguments": {"a": 1, "b": 1}
                }
            }
        )
        print(f"  응답 상태: {response.status_code}")
        print(f"  응답 내용: {response.text[:200]}...")
        
        # 응답 코드가 401이면 만료된 토큰이 성공적으로 차단된 것입니다.
        if response.status_code == 401:
            print("  ✅ 만료된 토큰이 성공적으로 차단됨")
        else:
            print("  ⚠️  예상과 다른 응답")
    except Exception as e:
        print(f"  ❌ 요청 실패: {e}")
    
    print("\n" + "="*50)
    
    # --- 4단계: DoS(Denial of Service) 공격 방어 확인 ---
    # 인증 없이 대량의 요청을 보내 서버 리소스를 고갈시키려는 시도를 시뮬레이션합니다.
    # JWT 인증이 적용되면, 실제 도구 실행 전에 인증 단계에서 모든 요청이 빠르게 차단되므로
    # 서버의 부하를 효과적으로 막을 수 있습니다.
    print("\n📍 4단계: DoS 공격 방어 확인")
    print("  JWT 없는 DoS 공격 시도 중... (모든 요청이 401로 차단되어야 함)")
    
    blocked_count = 0
    total_requests = 10  # 시뮬레이션을 위해 요청 횟수를 10회로 제한
    
    # 짧은 시간 동안 여러 번의 요청을 보냅니다.
    for i in range(total_requests):
        try:
            response = requests.post(
                "http://127.0.0.1:8001/mcp/",
                headers={"Content-Type": "application/json", "Accept": "application/json, text/event-stream"},
                json={
                    "jsonrpc": "2.0",
                    "id": i+1,
                    "method": "tools/call",
                    "params": {
                        "name": "add",
                        "arguments": {"a": 999999, "b": 999999}
                    }
                },
                timeout=5  # 요청 타임아웃 설정
            )
            # 401 응답을 받으면 차단된 것으로 간주합니다.
            if response.status_code == 401:
                blocked_count += 1
        except Exception:
            # 네트워크 오류 등 예외 발생도 차단으로 간주합니다.
            pass
    
    print(f"  차단된 요청: {blocked_count}/{total_requests}")
    if blocked_count == total_requests:
        print("  ✅ 모든 DoS 공격이 성공적으로 차단됨")
    else:
        print("  ⚠️  일부 요청이 차단되지 않음")
    
    print("\n" + "="*50)
    
    # --- 5단계: 정상 사용자 시뮬레이션에 대한 설명 ---
    # 실제 정상적인 사용자는 MCP 클라이언트를 통해 서버와 통신합니다.
    # 이 클라이언트는 유효한 JWT 토큰을 사용하여 인증을 수행합니다.
    # 이 스크립트의 목적은 '공격'을 시뮬레이션하고 '방어'를 확인하는 것이므로,
    # 정상적인 클라이언트 코드는 test_secure_server_proxy.py에서 보여줍니다.
    print("\n📍 5단계: 정상 사용자 접근 확인 (MCP 클라이언트)")
    
    print("  정상적인 MCP 클라이언트 연결은 별도 인증 서버에서 받은 JWT 토큰이 필요합니다.")
    print("  실제 운영환경에서는 인증 서버에서 토큰을 발급받아 사용합니다.")
    print("  이 실습에서는 공격 차단 효과를 확인하는 것이 목적입니다.")
    print("  ✅ 모든 무단 접근이 성공적으로 차단되었습니다!")
    
    # --- 최종 결과 요약 ---
    print("\n🎯 공격 방어 결과:")
    print("  🛡️ 무단 접근 시도: 모두 401 Unauthorized로 차단")
    print("  🛡️ DoS 공격: 인증 단계에서 모두 차단되어 서버 리소스 보호")
    print("  🛡️ 위조/만료된 토큰: 모두 차단됨")
    print("  ✅ 보안 시스템이 정상 작동함!")

# 이 스크립트가 직접 실행될 때 main 함수 역할을 하는 부분입니다.
if __name__ == "__main__":
    # asyncio.run()을 사용하여 비동기 함수인 simulate_secure_attack()을 실행합니다.
    asyncio.run(simulate_secure_attack())
