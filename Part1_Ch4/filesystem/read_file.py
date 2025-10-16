# -*- coding: utf-8 -*-
"""
이 모듈은 지정된 파일의 내용을 읽는 기능을 제공합니다.
파일의 특정 줄(line) 범위를 읽을 수 있는 옵션(offset, limit)을 포함합니다.
"""

import os

def read_file(file_path: str, offset: int = None, limit: int = None):
    """
    파일의 내용을 읽습니다. 선택적으로 줄 기반의 offset과 limit을 지정할 수 있습니다.

    Args:
        file_path (str): 읽을 파일의 절대 경로입니다.
        offset (int, optional): 읽기 시작할 0 기반의 줄 번호입니다. 기본값은 None입니다.
        limit (int, optional): 읽을 최대 줄 수입니다. 기본값은 None입니다.

    Returns:
        dict: 파일 내용 및 관련 정보를 담은 딕셔너리를 반환합니다.
              오류 발생 시, 오류 메시지를 담은 딕셔너리를 반환합니다.
    """
    # 입력된 경로가 절대 경로인지 확인합니다.
    if not os.path.isabs(file_path):
        return {"error": f"경로는 절대 경로여야 합니다: {file_path}"}

    # 파일이 실제로 존재하는지 확인합니다.
    if not os.path.exists(file_path):
        return {"error": f"파일을 찾을 수 없습니다: {file_path}"}

    # 지정된 경로가 파일이 맞는지 확인합니다.
    if not os.path.isfile(file_path):
        return {"error": f"경로가 파일이 아닙니다: {file_path}"}

    try:
        # 파일을 읽기 모드('r')와 UTF-8 인코딩으로 엽니다.
        with open(file_path, 'r', encoding='utf-8') as f:
            # 파일의 모든 줄을 읽어 리스트로 저장합니다.
            lines = f.readlines()

        # 전체 줄 수를 계산합니다.
        total_lines = len(lines)
        # 내용이 잘렸는지 여부를 나타내는 플래그입니다.
        is_truncated = False

        # offset과 limit이 모두 지정된 경우, 페이징 처리를 합니다.
        if offset is not None and limit is not None:
            if offset < 0:
                return {"error": "Offset은 0 이상의 숫자여야 합니다."}
            if limit <= 0:
                return {"error": "Limit은 0보다 큰 숫자여야 합니다."}

            # 읽기 시작할 인덱스와 끝 인덱스를 계산합니다.
            start = offset
            end = offset + limit
            # 지정된 범위의 줄들을 슬라이싱하여 가져옵니다.
            content_lines = lines[start:end]
            # 사용자에게 보여주는 줄 번호 범위를 계산합니다. (1 기반)
            lines_shown = (start + 1, min(end, total_lines))
            # 전체 줄 수가 끝 인덱스보다 크면 내용이 잘린 것입니다.
            is_truncated = total_lines > end
            # 다음 읽기를 위한 offset 값을 설정합니다.
            next_offset = end

        else:
            # offset이나 limit이 지정되지 않은 경우, 파일 전체를 읽습니다.
            content_lines = lines
            lines_shown = (1, total_lines)

        # 줄 리스트를 하나의 문자열로 합칩니다.
        content = "".join(content_lines)

        # 결과 딕셔너리를 생성합니다.
        result = {
            "llm_content": content,  # LLM이 사용할 파일 내용
            "is_truncated": is_truncated,
            "lines_shown": lines_shown,
            "original_line_count": total_lines,
        }

        # 내용이 잘렸을 경우, 추가 정보를 결과에 포함합니다.
        if is_truncated:
            result["next_offset"] = next_offset
            result["message"] = f"{total_lines}줄 중 {lines_shown[0]}-{lines_shown[1]}줄을 표시합니다. 더 읽으려면 offset: {next_offset}을 사용하세요."

        return result

    except Exception as e:
        # 파일 읽기 중 예외가 발생하면 오류 메시지를 반환합니다.
        return {"error": f"파일 읽기 오류: {e}"}