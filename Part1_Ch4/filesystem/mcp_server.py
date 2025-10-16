# -*- coding: utf-8 -*-
"""
이 모듈은 FastMCP를 사용하여 파일 시스템 작업을 위한 API 서버를 생성합니다.
list_directory, read_file, write_file, replace_in_file 함수들을
비동기적으로 실행할 수 있는 MCP 툴로 래핑하여 제공합니다.
"""

import asyncio
from fastmcp import FastMCP

# 다른 모듈에서 구현된 파일 시스템 관련 함수들을 임포트합니다.
from list_directory import list_directory
from read_file import read_file
from write_file import write_file
from replace import replace_in_file

# "FileAPIServer"라는 이름으로 FastMCP 서버 인스턴스를 생성합니다.
# 이 이름은 서버를 식별하는 데 사용됩니다.
mcp = FastMCP("FileAPIServer")


# list_directory 함수를 MCP 툴로 등록합니다.
# 클라이언트는 "list_dir"라는 이름으로 이 툴을 호출할 수 있습니다.
@mcp.tool()
async def list_dir(directory_path: str, ignore_patterns: list[str] = None) -> dict:
    """
    디렉터리의 내용을 나열하며, 선택적으로 특정 패턴을 무시할 수 있습니다.

    Args:
        directory_path (str): 내용을 나열할 디렉터리의 경로입니다.
        ignore_patterns (list[str], optional): 무시할 패턴의 리스트입니다. 기본값은 None입니다.
    """
    print(f"list_dir 툴 실행: directory_path={directory_path}")
    
    # list_directory 함수는 동기 함수이므로, asyncio 이벤트 루프를 차단하지 않기 위해
    # 별도의 스레드 풀에서 실행합니다.
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(
        None,  # 기본 스레드 풀 사용
        list_directory,  # 실행할 함수
        directory_path,  # 함수에 전달할 인수
        ignore_patterns
    )
    
    # 결과가 리스트 형태일 경우, fastmcp 호환성을 위해 딕셔너리로 감싸줍니다.
    if isinstance(result, list):
        return {"entries": result}
    return result


# read_file 함수를 MCP 툴로 등록합니다.
# 클라이언트는 "read"라는 이름으로 이 툴을 호출할 수 있습니다.
@mcp.tool()
async def read(file_path: str, offset: int = None, limit: int = None) -> dict:
    """
    파일의 내용을 읽습니다. 선택적으로 줄 기반의 offset과 limit을 지정할 수 있습니다.

    Args:
        file_path (str): 읽을 파일의 경로입니다.
        offset (int, optional): 읽기 시작할 줄의 오프셋입니다. 기본값은 None입니다.
        limit (int, optional): 읽을 최대 줄 수입니다. 기본값은 None입니다.
    """
    print(f"read 툴 실행: file_path={file_path}")
    loop = asyncio.get_event_loop()
    # 동기 함수인 read_file을 스레드 풀에서 실행합니다.
    return await loop.run_in_executor(
        None, read_file, file_path, offset, limit
    )


# write_file 함수를 MCP 툴로 등록합니다.
# 클라이언트는 "write"라는 이름으로 이 툴을 호출할 수 있습니다.
@mcp.tool()
async def write(file_path: str, content: str) -> dict:
    """
    파일에 내용을 씁니다.

    Args:
        file_path (str): 내용을 쓸 파일의 경로입니다.
        content (str): 파일에 쓸 내용입니다.
    """
    print(f"write 툴 실행: file_path={file_path}")
    loop = asyncio.get_event_loop()
    # 동기 함수인 write_file을 스레드 풀에서 실행합니다.
    return await loop.run_in_executor(
        None, write_file, file_path, content
    )


# replace_in_file 함수를 MCP 툴로 등록합니다.
# 클라이언트는 "replace"라는 이름으로 이 툴을 호출할 수 있습니다.
@mcp.tool()
async def replace(file_path: str, old_string: str, new_string: str, expected_replacements: int = 1) -> dict:
    """
    파일 내의 텍스트를 교체합니다.

    Args:
        file_path (str): 텍스트를 교체할 파일의 경로입니다.
        old_string (str): 교체될 기존 문자열입니다.
        new_string (str): `old_string`을 대체할 새로운 문자열입니다.
        expected_replacements (int, optional): 예상되는 교체 횟수입니다. 기본값은 1입니다.
    """
    print(f"replace 툴 실행: file_path={file_path}")
    loop = asyncio.get_event_loop()
    # 동기 함수인 replace_in_file을 스레드 풀에서 실행합니다.
    return await loop.run_in_executor(
        None, replace_in_file, file_path, old_string, new_string, expected_replacements
    )


# 이 스크립트가 직접 실행될 때만 아래 코드가 실행됩니다.
if __name__ == "__main__":
    print("File API MCP 서버를 시작합니다...")
    # FastMCP 서버를 실행하여 클라이언트의 요청을 기다립니다.
    mcp.run()