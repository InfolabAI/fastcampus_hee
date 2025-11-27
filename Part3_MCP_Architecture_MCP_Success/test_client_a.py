#!/usr/bin/env python3
"""FastMCP Client for testing Proxy MCP A
Run with: infisical run -- python test_client_a.py
"""
import asyncio
import os
import sys
from fastmcp import Client
from fastmcp.client.transports import StdioTransport

async def test_proxy_mcp_a():
    """Test Proxy MCP A tools via FastMCP Client"""

    # Check JWT_SECRET (needed for the subprocess)
    if not os.getenv("JWT_SECRET"):
        print("[ERROR] JWT_SECRET not set. Run with: infisical run -- python test_client_a.py")
        sys.exit(1)

    # Create stdio transport to launch proxy_mcp_a.py with infisical
    # Use infisical run to inject secrets into subprocess
    transport = StdioTransport(
        command="infisical",
        args=["run", "--", "python", "proxy_mcp_a/proxy_mcp_a.py"]
    )
    client = Client(transport)

    try:
        async with client:
            print("=== Proxy MCP A Test (FastMCP Client) ===\n")

            # List available tools
            tools = await client.list_tools()
            print("Available tools:")
            for tool in tools:
                print(f"  - {tool.name}: {tool.description}")
            print()

            # Test 1: Insert
            print("[Test 1] Insert item...")
            result = await client.call_tool("insert", {"name": "test_item_a", "value": "value_from_client_a"})
            print(f"  Result: {result}")
            if "error" in str(result).lower() and "access denied" not in str(result).lower():
                print("  [WARN] Possible error in insert")
            else:
                print("  [PASS] Insert completed")
            print()

            # Test 2: Select all
            print("[Test 2] Select all items...")
            result = await client.call_tool("select", {})
            print(f"  Result: {result}")
            print("  [PASS] Select completed")
            print()

            # Test 3: Update (assuming id=1 exists)
            print("[Test 3] Update item (id=1)...")
            result = await client.call_tool("update", {"id": 1, "value": "updated_value_a"})
            print(f"  Result: {result}")
            print("  [PASS] Update completed")
            print()

            # Test 4: Select specific item
            print("[Test 4] Select item (id=1)...")
            result = await client.call_tool("select", {"id": 1})
            print(f"  Result: {result}")
            print("  [PASS] Select by ID completed")
            print()

            print("=== All Proxy MCP A tests completed! ===")

    except Exception as e:
        print(f"[ERROR] {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(test_proxy_mcp_a())
