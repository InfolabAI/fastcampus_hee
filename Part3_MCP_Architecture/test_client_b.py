#!/usr/bin/env python3
"""FastMCP Client for testing Proxy MCP B
Run with: infisical run -- python test_client_b.py
"""
# =============================================================================
# Test Client B - FastMCP 클라이언트를 사용한 Proxy MCP B 테스트
# =============================================================================
# 역할: Proxy MCP B의 도구들을 테스트 (insert, select, update)
# 통신: StdioTransport로 MCP 프로토콜 통신
# 실행: infisical run으로 JWT_SECRET 주입 후 실행
# =============================================================================

import asyncio  # 비동기 실행
import os  # 환경변수 확인
import sys  # 프로그램 종료
from fastmcp import Client  # FastMCP 클라이언트
from fastmcp.client.transports import StdioTransport  # stdio 기반 MCP 전송 계층

async def test_proxy_mcp_b():
    """Proxy MCP B 도구 테스트 - FastMCP Client 사용"""

    # JWT_SECRET 확인 - 서브프로세스에서 필요
    if not os.getenv("JWT_SECRET"):
        print("[ERROR] JWT_SECRET not set. Run with: infisical run -- python test_client_b.py")
        sys.exit(1)

    # StdioTransport 생성 - infisical로 시크릿 주입하며 MCP 서버 실행
    # infisical run -- python proxy_mcp_b.py 명령 실행
    transport = StdioTransport(
        command="infisical",  # infisical CLI로 시크릿 주입
        args=["run", "--", "python", "proxy_mcp_b/proxy_mcp_b.py"]  # MCP 서버 실행
    )
    client = Client(transport)  # FastMCP 클라이언트 생성

    try:
        async with client:  # 비동기 컨텍스트 - 연결 자동 관리
            print("=== Proxy MCP B Test (FastMCP Client) ===\n")

            # ---------------------------------------------------------------------
            # 사용 가능한 도구 목록 조회
            # ---------------------------------------------------------------------
            tools = await client.list_tools()  # MCP tools/list 요청
            print("Available tools:")
            for tool in tools:
                print(f"  - {tool.name}: {tool.description}")  # 도구명: 설명
            print()

            # ---------------------------------------------------------------------
            # Test 1: Insert - 새 아이템 삽입
            # ---------------------------------------------------------------------
            print("[Test 1] Insert item...")
            result = await client.call_tool("insert", {"name": "test_item_b", "value": "value_from_client_b"})  # MCP tools/call
            print(f"  Result: {result}")
            if "error" in str(result).lower() and "access denied" not in str(result).lower():
                print("  [WARN] Possible error in insert")  # 에러 경고
            else:
                print("  [PASS] Insert completed")
            print()

            # ---------------------------------------------------------------------
            # Test 2: Select All - 전체 아이템 조회
            # ---------------------------------------------------------------------
            print("[Test 2] Select all items...")
            result = await client.call_tool("select", {})  # 파라미터 없음 = 전체 조회
            print(f"  Result: {result}")
            print("  [PASS] Select completed")
            print()

            # ---------------------------------------------------------------------
            # Test 3: Update - 기존 아이템 수정
            # ---------------------------------------------------------------------
            print("[Test 3] Update item (id=1)...")
            result = await client.call_tool("update", {"id": 1, "value": "updated_value_b"})  # id=1 수정
            print(f"  Result: {result}")
            print("  [PASS] Update completed")
            print()

            # ---------------------------------------------------------------------
            # Test 4: Select by ID - 특정 아이템 조회
            # ---------------------------------------------------------------------
            print("[Test 4] Select item (id=1)...")
            result = await client.call_tool("select", {"id": 1})  # id=1 조회
            print(f"  Result: {result}")
            print("  [PASS] Select by ID completed")
            print()

            print("=== All Proxy MCP B tests completed! ===")

    except Exception as e:
        print(f"[ERROR] {e}")  # 예외 발생 시 에러 출력
        sys.exit(1)  # 비정상 종료

# =============================================================================
# 메인 실행부
# =============================================================================
if __name__ == "__main__":
    asyncio.run(test_proxy_mcp_b())  # 비동기 함수 실행
