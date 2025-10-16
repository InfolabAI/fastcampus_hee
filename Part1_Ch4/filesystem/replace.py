# -*- coding: utf-8 -*-
"""
이 모듈은 파일 내의 특정 문자열을 다른 문자열로 교체하는 기능을 제공합니다.
정확한 교체를 위해 예상 교체 횟수를 지정할 수 있습니다.
"""

import os

def replace_in_file(file_path: str, old_string: str, new_string: str, expected_replacements: int = 1):
    """
    파일 내의 텍스트를 교체합니다.

    Args:
        file_path (str): 수정할 파일의 절대 경로입니다.
        old_string (str): 교체될 대상 텍스트입니다.
        new_string (str): 새로 교체할 텍스트입니다.
        expected_replacements (int, optional): 예상되는 교체 횟수입니다. 
                                             실제 발생 횟수와 다르면 교체가 수행되지 않습니다. 
                                             기본값은 1입니다.

    Returns:
        dict: 성공 또는 오류 메시지를 담은 딕셔너리를 반환합니다.
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
        # 파일을 읽기 모드로 열어 전체 내용을 읽습니다.
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # 내용에서 old_string이 몇 번 나타나는지 계산합니다.
        occurrences = content.count(old_string)

        # 교체할 문자열을 찾지 못한 경우 오류를 반환합니다.
        if occurrences == 0:
            return {"error": "편집 실패, 교체할 문자열을 찾을 수 없습니다."}

        # 실제 발생 횟수가 예상 횟수와 다른 경우 오류를 반환합니다.
        # 이는 의도하지 않은 교체를 방지하는 안전 장치입니다.
        if occurrences != expected_replacements:
            return {"error": f"편집 실패, 예상 교체 횟수는 {expected_replacements}이지만 {occurrences}번 발생했습니다."}

        # 이전 문자열과 새 문자열이 동일하면 변경할 내용이 없습니다.
        if old_string == new_string:
            return {"error": "적용할 변경 사항이 없습니다. 이전 문자열과 새 문자열이 동일합니다."}

        # 문자열을 교체합니다. 세 번째 인수는 최대 교체 횟수를 지정합니다.
        new_content = content.replace(old_string, new_string, expected_replacements)

        # 파일을 쓰기 모드로 열어 교체된 내용으로 덮어씁니다.
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)

        # 성공 메시지를 반환합니다.
        return {"message": f"파일을 성공적으로 수정했습니다: {file_path} ({occurrences}번 교체)."}

    except Exception as e:
        # 파일 처리 중 예외가 발생하면 오류 메시지를 반환합니다.
        return {"error": f"파일 처리 오류: {e}"}