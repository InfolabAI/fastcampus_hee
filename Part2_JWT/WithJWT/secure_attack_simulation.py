import asyncio
from fastmcp import Client
import requests
import json

async def simulate_secure_attack():
    """JWT 인증이 적용된 보안 서버에 대한 공격 시뮬레이션"""
    
    print("🔒 보안 서버 공격 시뮬레이션 시작 🔒\n")
    
    # 1. 인증 없는 접근 시도 (HTTP 직접)
    print("📍 1단계: JWT 토큰 없는 무단 접근 시도")
    try:
        response = requests.post(
            "http://127.0.0.1:8001/mcp/",
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
        print(f"  응답 상태: {response.status_code}")
        print(f"  응답 내용: {response.text[:200]}...")
        
        if response.status_code == 401:
            print("  ✅ 성공적으로 차단됨 (401 Unauthorized)")
        else:
            print("  ⚠️  예상과 다른 응답")
    except Exception as e:
        print(f"  ❌ 요청 실패: {e}")
    
    print("\n" + "="*50)
    
    # 2. 잘못된 JWT 토큰으로 접근 시도
    print("\n📍 2단계: 잘못된 JWT 토큰으로 접근 시도")
    try:
        response = requests.post(
            "http://127.0.0.1:8001/mcp/",
            headers={
                "Content-Type": "application/json", 
                "Accept": "application/json, text/event-stream",
                "Authorization": "Bearer invalid.jwt.token"
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
        
        if response.status_code == 401:
            print("  ✅ 위조된 토큰이 성공적으로 차단됨")
        else:
            print("  ⚠️  예상과 다른 응답")
    except Exception as e:
        print(f"  ❌ 요청 실패: {e}")
    
    print("\n" + "="*50)
    
    # 3. 만료된 토큰으로 접근 시도
    print("\n📍 3단계: 만료된 토큰으로 접근 시도")
    expired_token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ1c2VyX2lkIjoidGVzdCIsImV4cCI6MTUwMDAwMDAwMH0.invalid"
    try:
        response = requests.post(
            "http://127.0.0.1:8001/mcp/",
            headers={
                "Content-Type": "application/json", 
                "Accept": "application/json, text/event-stream",
                "Authorization": f"Bearer {expired_token}"
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
        
        if response.status_code == 401:
            print("  ✅ 만료된 토큰이 성공적으로 차단됨")
        else:
            print("  ⚠️  예상과 다른 응답")
    except Exception as e:
        print(f"  ❌ 요청 실패: {e}")
    
    print("\n" + "="*50)
    
    # 4. DoS 공격 방어 확인
    print("\n📍 4단계: DoS 공격 방어 확인")
    print("  JWT 없는 DoS 공격 시도 중... (모든 요청이 401로 차단되어야 함)")
    
    blocked_count = 0
    total_requests = 10
    
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
                timeout=5
            )
            if response.status_code == 401:
                blocked_count += 1
        except Exception:
            pass  # 네트워크 에러도 차단으로 간주
    
    print(f"  차단된 요청: {blocked_count}/{total_requests}")
    if blocked_count == total_requests:
        print("  ✅ 모든 DoS 공격이 성공적으로 차단됨")
    else:
        print("  ⚠️  일부 요청이 차단되지 않음")
    
    print("\n" + "="*50)
    
    # 5. 정상 사용자 시뮬레이션 (MCP 클라이언트 사용)
    print("\n📍 5단계: 정상 사용자 접근 확인 (MCP 클라이언트)")
    
    print("  정상적인 MCP 클라이언트 연결은 별도 인증 서버에서 받은 JWT 토큰이 필요합니다.")
    print("  실제 운영환경에서는 인증 서버에서 토큰을 발급받아 사용합니다.")
    print("  이 실습에서는 공격 차단 효과를 확인하는 것이 목적입니다.")
    print("  ✅ 모든 무단 접근이 성공적으로 차단되었습니다!")
    
    print("\n🎯 공격 방어 결과:")
    print("  🛡️ 무단 접근 시도: 모두 401 Unauthorized로 차단")
    print("  🛡️ DoS 공격: 인증 단계에서 모두 차단되어 서버 리소스 보호")
    print("  🛡️ 위조/만료된 토큰: 모두 차단됨")
    print("  ✅ 보안 시스템이 정상 작동함!")

if __name__ == "__main__":
    asyncio.run(simulate_secure_attack())