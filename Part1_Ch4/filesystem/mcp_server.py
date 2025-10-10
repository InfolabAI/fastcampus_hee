
import asyncio
from fastmcp import FastMCP

# Import the functions from our modules
from list_directory import list_directory
from read_file import read_file
from write_file import write_file
from replace import replace_in_file

# Create a FastMCP server instance
mcp = FastMCP("FileAPIServer")

@mcp.tool()
async def list_dir(directory_path: str, ignore_patterns: list[str] = None) -> dict:
    """
    Lists the contents of a directory, with optional ignore patterns.
    """
    print(f"Executing list_dir tool with: directory_path={directory_path}")
    # Since the underlying function is synchronous, we run it in a thread pool
    # to avoid blocking the asyncio event loop.
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(
        None, list_directory, directory_path, ignore_patterns
    )
    # Wrap list result in a dict for fastmcp compatibility
    if isinstance(result, list):
        return {"entries": result}
    return result

@mcp.tool()
async def read(file_path: str, offset: int = None, limit: int = None) -> dict:
    """
    Reads the content of a file, with optional line-based offset and limit.
    """
    print(f"Executing read tool with: file_path={file_path}")
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(
        None, read_file, file_path, offset, limit
    )

@mcp.tool()
async def write(file_path: str, content: str) -> dict:
    """
    Writes content to a file.
    """
    print(f"Executing write tool with: file_path={file_path}")
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(
        None, write_file, file_path, content
    )

@mcp.tool()
async def replace(file_path: str, old_string: str, new_string: str, expected_replacements: int = 1) -> dict:
    """
    Replaces text within a file.
    """
    print(f"Executing replace tool with: file_path={file_path}")
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(
        None, replace_in_file, file_path, old_string, new_string, expected_replacements
    )

if __name__ == "__main__":
    print("Starting File API MCP server...")
    mcp.run()
