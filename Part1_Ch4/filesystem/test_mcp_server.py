
import asyncio
import os
import shutil
import pathlib
import json
from fastmcp import Client
from fastmcp.client.transports import StdioTransport


async def test_file_api_server():
    """Tests the tools in mcp_server.py."""

    # 1. Set up a temporary test directory
    test_dir = pathlib.Path("./mcp_test_workspace").resolve()
    if test_dir.exists():
        shutil.rmtree(test_dir)
    test_dir.mkdir()

    # Create some initial files and directories
    (test_dir / "subdir").mkdir()
    (test_dir / "file1.txt").write_text("This is file 1.\nIt has two lines.")
    (test_dir / "file_to_replace.txt").write_text("Replace this content.")
    (test_dir / ".ignored_file").write_text("should be ignored")

    print(f"Test workspace created at: {test_dir}\n")

    # Use StdioTransport to run the server script
    transport = StdioTransport(
        command="python",
        args=["mcp_server.py"]  # Run as a script
    )
    client = Client(transport)

    try:
        async with client:
            print("=== File API Server Test Started ===\n")

            # List available tools
            tools = await client.list_tools()
            print("Available Tools:")
            for tool in tools:
                print(f"  - {tool.name}: {tool.description}")
            print()

            # 1. Test list_dir tool
            print("1. Testing 'list_dir' tool...")
            result = await client.call_tool("list_dir", {
                "directory_path": str(test_dir),
                "ignore_patterns": [".*"]  # Ignore hidden files
            })
            print(f"   Found {len(result.data['entries'])} entries:")
            for entry in result.data['entries']:
                print(
                    f"     - {entry['name']} ({'dir' if entry['is_directory'] else 'file'})")
            print()
            # subdir, file1.txt, file_to_replace.txt
            assert len(result.data["entries"]) == 3

            # 2. Test read tool
            print("2. Testing 'read' tool...")
            read_path = str(test_dir / "file1.txt")
            result = await client.call_tool("read", {"file_path": read_path})
            print(f"   Content:\n{result.data['llm_content']}\n")
            assert "This is file 1" in result.data['llm_content']

            # 3. Test write tool
            print("3. Testing 'write' tool...")
            write_path = str(test_dir / "newly_created_file.txt")
            result = await client.call_tool("write", {"file_path": write_path, "content": "Hello from MCP!"})
            print(f"   {result.data['message']}")
            # Verify the file was created and has correct content
            actual_content = (test_dir / "newly_created_file.txt").read_text()
            print(f"   Verified content: {actual_content}\n")
            assert os.path.exists(write_path)
            assert actual_content == "Hello from MCP!"

            # 4. Test replace tool
            print("4. Testing 'replace' tool...")
            replace_path = str(test_dir / "file_to_replace.txt")
            print(
                f"   Original content: {(test_dir / 'file_to_replace.txt').read_text()}")
            result = await client.call_tool("replace", {
                "file_path": replace_path,
                "old_string": "this content",
                "new_string": "the new shiny content"
            })
            print(f"   {result.data['message']}")
            # Verify the replacement was made correctly
            actual_content = (test_dir / "file_to_replace.txt").read_text()
            print(f"   New content: {actual_content}\n")
            assert actual_content == "Replace the new shiny content."

            print("=== Test Completed ===")

    except Exception as e:
        import traceback
        print(f"An error occurred: {e}")
        traceback.print_exc()
    finally:
        # 5. Clean up the test directory
        print("\nCleaning up test workspace...")
        shutil.rmtree(test_dir)
        print("Cleanup complete.")

if __name__ == "__main__":

    asyncio.run(test_file_api_server())
