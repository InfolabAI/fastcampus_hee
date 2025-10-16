# -*- coding: utf-8 -*-
"""
이 모듈은 지정된 파일에 내용을 쓰는 기능을 제공합니다.
파일이 존재하지 않을 경우, 필요한 상위 디렉터리를 포함하여 파일을 생성합니다.
"""

import os

def write_file(file_path: str, content: str):
    """
    파일에 내용을 씁니다.

    Args:
        file_path (str): 내용을 쓸 파일의 절대 경로입니다.
        content (str): 파일에 쓸 내용입니다.

    Returns:
        dict: 성공 또는 오류 메시지를 담은 딕셔너리를 반환합니다.
    """
    # 입력된 경로가 절대 경로인지 확인합니다.
    if not os.path.isabs(file_path):
        return {"error": f"경로는 절대 경로여야 합니다: {file_path}"}

    try:
        # 파일의 상위 디렉터리 경로를 가져옵니다.
        parent_dir = os.path.dirname(file_path)
        # 상위 디렉터리가 존재하지 않으면 생성합니다.
        if not os.path.exists(parent_dir):
            os.makedirs(parent_dir)

        # 파일이 쓰기 작업 전에 이미 존재했는지 여부를 확인합니다.
        is_new_file = not os.path.exists(file_path)

        # 파일을 쓰기 모드('w')와 UTF-8 인코딩으로 엽니다.
        # 'w' 모드는 파일이 이미 존재할 경우 내용을 덮어씁니다.
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)

        # 파일이 새로 생성되었는지, 아니면 덮어쓰기되었는지에 따라 다른 성공 메시지를 반환합니다.
        if is_new_file:
            return {"message": f"새 파일을 성공적으로 생성하고 내용을 썼습니다: {file_path}"}
        else:
            return {"message": f"파일을 성공적으로 덮어썼습니다: {file_path}"}

    except Exception as e:
        # 파일 쓰기 중 예외가 발생하면 오류 메시지를 반환합니다.
        return {"error": f"파일 쓰기 오류: {e}"}