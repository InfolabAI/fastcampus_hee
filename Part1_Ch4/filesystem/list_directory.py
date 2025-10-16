# -*- coding: utf-8 -*-
"""
이 모듈은 지정된 디렉터리의 내용을 나열하는 기능을 제공합니다.
특정 패턴과 일치하는 파일이나 디렉터리를 무시하는 옵션도 포함합니다.
"""

import os
import pathlib
import fnmatch
from datetime import datetime


def list_directory(directory_path: str, ignore_patterns: list[str] = None):
    """
    디렉터리의 내용을 나열하며, 선택적으로 특정 패턴을 무시할 수 있습니다.

    Args:
        directory_path (str): 내용을 나열할 디렉터리의 절대 경로입니다.
        ignore_patterns (list[str], optional): 무시할 glob 패턴의 리스트입니다. 기본값은 None입니다.

    Returns:
        list[dict]: 각 파일이나 디렉터리를 나타내는 딕셔너리들의 리스트를 반환합니다.
                     오류 발생 시, 오류 메시지를 담은 딕셔너리를 반환합니다.
    """
    # 입력된 경로가 절대 경로인지 확인합니다.
    # 보안 및 일관성을 위해 절대 경로만 허용합니다.
    if not os.path.isabs(directory_path):
        return {"error": f"경로는 절대 경로여야 합니다: {directory_path}"}

    # 지정된 경로가 실제로 존재하는지 확인합니다.
    if not os.path.exists(directory_path):
        return {"error": f"디렉터리를 찾을 수 없습니다: {directory_path}"}

    # 지정된 경로가 디렉터리가 맞는지 확인합니다.
    if not os.path.isdir(directory_path):
        return {"error": f"경로가 디렉터리가 아닙니다: {directory_path}"}

    # 디렉터리 내의 항목들을 저장할 리스트를 초기화합니다.
    entries = []
    # 'os.scandir'를 사용하여 디렉터리를 순회합니다. 'os.listdir'보다 효율적입니다.
    with os.scandir(directory_path) as it:
        for entry in it:
            # 현재 항목을 무시해야 하는지 여부를 나타내는 플래그입니다.
            should_ignore = False
            # 무시 패턴이 제공된 경우, 각 패턴을 확인합니다.
            if ignore_patterns:
                for pattern in ignore_patterns:
                    # 'fnmatch'를 사용하여 파일 이름이 패턴과 일치하는지 확인합니다.
                    if fnmatch.fnmatch(entry.name, pattern):
                        should_ignore = True
                        break  # 일치하는 패턴을 찾으면 더 이상 확인할 필요가 없습니다.

            # 이 항목을 무시해야 한다면, 다음 항목으로 넘어갑니다.
            if should_ignore:
                continue

            try:
                # 'entry.stat()'을 호출하여 파일의 메타데이터를 가져옵니다.
                stat = entry.stat()
                # 'entry.is_dir()'을 호출하여 디렉터리인지 확인합니다.
                is_dir = entry.is_dir()
                # 파일/디렉터리 정보를 딕셔너리로 만들어 리스트에 추가합니다.
                entries.append({
                    "name": entry.name,
                    "path": entry.path,
                    "is_directory": is_dir,
                    # 디렉터리는 크기를 0으로 설정합니다.
                    "size": stat.st_size if not is_dir else 0,
                    # 수정 시간을 datetime 객체로 변환합니다.
                    "modified_time": datetime.fromtimestamp(stat.st_mtime)
                })
            except OSError as e:
                # 파일 정보(stat)를 가져오는 동안 오류가 발생하면 메시지를 출력합니다.
                print(f"{entry.path}의 정보를 가져오는 중 오류 발생: {e}")

    # 결과를 정렬합니다. 디렉터리가 파일보다 먼저 오고, 그 다음 이름순으로 정렬합니다.
    # 정렬 키: (디렉터리 여부(True=1, False=0)의 역, 이름)
    entries.sort(key=lambda x: (not x["is_directory"], x["name"]))

    # 최종적으로 수집된 파일 및 디렉터리 정보 리스트를 반환합니다.
    return entries
