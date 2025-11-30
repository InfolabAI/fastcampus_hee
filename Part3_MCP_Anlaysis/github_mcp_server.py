#!/usr/bin/env python3
"""
Local Project Analysis MCP Server

로컬 프로젝트를 분석하여 파일 구조와 코드를 추출하는 도구를 제공합니다.

사용법:
1. 먼저 local_analyze_structure를 사용하여 프로젝트의 전체 구조를 파악하세요.
2. 필요한 특정 파일이나 함수/클래스가 있다면 local_extract_code를 사용하여 세부 코드를 추출하세요.

예시:
- 구조 분석: local_analyze_structure("/home/user/myproject", extensions=["py", "js"])
- 코드 추출: local_extract_code("/home/user/myproject", targets=["src/main.py", "src/utils.py:process_data"])
"""

from typing import List
from mcp.server.fastmcp import FastMCP
from analyze_project import analyze_project_structure, extract_code_contents

mcp = FastMCP("Local Project Analysis Server")


@mcp.tool()
def local_analyze_structure(project_path: str, extensions: List[str] = None, skip_details: bool = False) -> dict:
    """
    로컬 프로젝트의 파일 구조와 Python 파일의 클래스/함수 정보를 분석합니다.

    Args:
        project_path: 분석할 프로젝트 루트 경로
        extensions: 분석할 파일 확장자 리스트 (기본값: ["py"])
        skip_details: True일 경우 함수/클래스 정보 수집을 건너뜀 (기본값: False)

    Returns:
        dict: 파일 구조 정보 (file_count, structure)

    예시:
        local_analyze_structure("/home/user/myproject", ["py", "md", "yaml"])
    """
    if extensions is None:
        extensions = ["py"]

    try:
        result = analyze_project_structure(project_path, extensions)
        if "error" not in result:
            result["usage_guide"] = {
                "next_step": "특정 파일이나 함수/클래스의 코드를 보려면 local_extract_code를 사용하세요",
                "examples": [
                    f"전체 파일: local_extract_code('{project_path}', ['path/to/file.py'])",
                    f"특정 함수: local_extract_code('{project_path}', ['path/to/file.py:function_name'])"
                ]
            }
        return result
    except Exception as e:
        return {"error": f"구조 분석 중 오류 발생: {str(e)}"}


@mcp.tool()
def local_extract_code(project_path: str, targets: List[str]) -> dict:
    """
    로컬 프로젝트에서 특정 파일, 클래스, 함수들의 코드를 추출합니다.

    Args:
        project_path: 프로젝트 루트 경로
        targets: 추출할 대상들의 리스트
                형식: "파일경로", "파일경로:클래스명", "파일경로:함수명"

    Returns:
        dict: 추출된 코드 정보

    예시:
        local_extract_code("/home/user/myproject", [
            "src/main.py",
            "src/utils.py:process_data",
            "src/models.py:DataModel"
        ])
    """
    try:
        result = extract_code_contents(project_path, targets)
        successful = sum(1 for v in result.values() if "error" not in v)
        result["extraction_summary"] = {
            "total_targets": len(targets),
            "successful": successful,
            "failed": len(result) - successful
        }
        return result
    except Exception as e:
        return {"error": f"코드 추출 중 오류 발생: {str(e)}"}


if __name__ == "__main__":
    mcp.run()
