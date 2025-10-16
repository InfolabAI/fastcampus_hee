"""
4-9. 파일→SQLite 적재 파이프라인
파일 내용을 데이터베이스에 자동으로 옮겨 담기

파일 시스템에서 파일을 읽어 SQLite 데이터베이스로 적재하는 파이프라인
"""

# pathlib.Path: 파일 시스템 경로를 객체 지향적으로 다루기 위한 클래스입니다.
from pathlib import Path
# typing: 타입 힌트를 지원하는 라이브러리입니다.
from typing import List, Optional, Dict, Any
# json: JSON 데이터를 다루기 위한 모듈입니다.
import json
# datetime: 날짜와 시간을 다루는 모듈입니다.
from datetime import datetime

# 이전에 구현한 데이터베이스 관련 모듈들을 임포트합니다.
from .db_design import DatabaseDesign
from .crud_api import CRUDOperations


class FileToDBPipeline:
    """
    파일 시스템의 파일들을 읽어서 SQLite 데이터베이스에 저장하는
    파이프라인 클래스입니다.
    """

    def __init__(self, db_design: DatabaseDesign):
        """
        FileToDBPipeline 클래스의 인스턴스를 초기화합니다.

        Args:
            db_design (DatabaseDesign): 데이터베이스 연결 및 스키마 정보를 담고 있는
                                       DatabaseDesign 객체입니다.
        """
        self.db_design = db_design
        self.crud = CRUDOperations(db_design)

    def load_file(
        self,
        file_path: Path,
        additional_metadata: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        단일 파일을 읽어 데이터베이스에 적재합니다.

        Args:
            file_path (Path): 데이터베이스에 적재할 파일의 경로입니다.
            additional_metadata (Optional[Dict[str, Any]]): 파일과 함께 저장할 추가 메타데이터입니다.

        Returns:
            int: 데이터베이스에 생성된 새 문서의 ID.

        Raises:
            FileNotFoundError: 지정된 경로에 파일이 존재하지 않을 경우 발생합니다.
            PermissionError: 파일을 읽을 권한이 없을 경우 발생할 수 있습니다.
        """
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        # 파일의 상태 정보(크기, 생성/수정 시간 등)를 가져옵니다.
        file_stat = file_path.stat()
        file_size = file_stat.st_size

        # 파일을 읽습니다. 텍스트 파일로 먼저 시도하고, 실패하면 바이너리로 처리합니다.
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except UnicodeDecodeError:
            # UTF-8로 디코딩할 수 없는 경우, 바이너리 파일로 간주하고
            # 16진수 문자열로 변환하여 저장합니다.
            with open(file_path, 'rb') as f:
                content = f.read().hex()

        # 파일 시스템 정보로부터 기본 메타데이터를 생성합니다.
        metadata = {
            "original_path": str(file_path.absolute()),
            "file_extension": file_path.suffix,
            "created_time": datetime.fromtimestamp(file_stat.st_ctime).isoformat(),
            "modified_time": datetime.fromtimestamp(file_stat.st_mtime).isoformat(),
        }

        # 사용자가 제공한 추가 메타데이터가 있으면 병합합니다.
        if additional_metadata:
            metadata.update(additional_metadata)

        # CRUDOperations를 사용하여 데이터베이스에 문서를 생성합니다.
        doc_id = self.crud.create(
            filename=file_path.name,
            content=content,
            file_type=file_path.suffix.lstrip('.') or 'unknown',
            file_size=file_size,
            metadata=metadata
        )

        return doc_id

    def load_directory(
        self,
        directory_path: Path,
        pattern: str = "*",
        recursive: bool = False,
        skip_existing: bool = True
    ) -> Dict[str, Any]:
        """
        지정된 디렉토리 내의 파일들을 데이터베이스에 적재합니다.

        Args:
            directory_path (Path): 파일들을 가져올 디렉토리의 경로입니다.
            pattern (str): 찾을 파일의 패턴 (e.g., "*.txt", "*.json").
            recursive (bool): 하위 디렉토리까지 재귀적으로 탐색할지 여부입니다.
            skip_existing (bool): 데이터베이스에 이미 파일명이 존재하는 경우 건너뛸지 여부입니다.

        Returns:
            Dict[str, Any]: 적재 작업의 통계(총 파일 수, 성공, 건너뜀, 실패 등)를 담은 딕셔너리.
        """
        if not directory_path.is_dir():
            raise NotADirectoryError(f"Not a directory: {directory_path}")

        # `rglob`은 재귀적으로, `glob`은 현재 디렉토리에서만 파일을 찾습니다.
        if recursive:
            files = list(directory_path.rglob(pattern))
        else:
            files = list(directory_path.glob(pattern))

        # 검색된 경로 중 파일만 필터링합니다.
        files = [f for f in files if f.is_file()]

        # 적재 결과를 기록할 통계 딕셔너리를 초기화합니다.
        stats = {
            "total_files": len(files),
            "loaded": 0,
            "skipped": 0,
            "failed": 0,
            "loaded_ids": [],
            "failed_files": []
        }

        # 기존 파일 건너뛰기 옵션이 켜져 있으면, DB의 모든 파일명을 미리 조회해 둡니다.
        existing_filenames = set()
        if skip_existing:
            all_docs = self.crud.read_all()
            existing_filenames = {doc['filename'] for doc in all_docs}

        # 각 파일을 순회하며 적재를 시도합니다.
        for file_path in files:
            try:
                # 파일명이 이미 존재하면 건너뜁니다.
                if skip_existing and file_path.name in existing_filenames:
                    stats["skipped"] += 1
                    continue

                doc_id = self.load_file(file_path)
                stats["loaded"] += 1
                stats["loaded_ids"].append(doc_id)

            except Exception as e:
                # 적재 중 오류가 발생하면 실패로 기록합니다.
                stats["failed"] += 1
                stats["failed_files"].append({
                    "file": str(file_path),
                    "error": str(e)
                })

        return stats

    def load_files(
        self,
        file_paths: List[Path],
        skip_existing: bool = True
    ) -> Dict[str, Any]:
        """
        파일 경로 리스트를 받아 여러 파일을 데이터베이스에 적재합니다.

        Args:
            file_paths (List[Path]): 적재할 파일들의 경로 리스트입니다.
            skip_existing (bool): 이미 존재하는 파일을 건너뛸지 여부입니다.

        Returns:
            Dict[str, Any]: 적재 결과 통계를 담은 딕셔너리.
        """
        stats = {
            "total_files": len(file_paths),
            "loaded": 0,
            "skipped": 0,
            "failed": 0,
            "loaded_ids": [],
            "failed_files": []
        }

        existing_filenames = set()
        if skip_existing:
            all_docs = self.crud.read_all()
            existing_filenames = {doc['filename'] for doc in all_docs}

        for file_path in file_paths:
            try:
                if skip_existing and file_path.name in existing_filenames:
                    stats["skipped"] += 1
                    continue

                doc_id = self.load_file(file_path)
                stats["loaded"] += 1
                stats["loaded_ids"].append(doc_id)

            except Exception as e:
                stats["failed"] += 1
                stats["failed_files"].append({
                    "file": str(file_path),
                    "error": str(e)
                })

        return stats

    def update_file(
        self,
        file_path: Path,
        doc_id: int
    ) -> bool:
        """
        파일의 현재 내용으로 데이터베이스의 기존 문서를 업데이트합니다.

        Args:
            file_path (Path): 업데이트할 내용을 담고 있는 파일의 경로입니다.
            doc_id (int): 업데이트할 데이터베이스 문서의 ID입니다.

        Returns:
            bool: 업데이트 성공 여부.
        """
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        file_stat = file_path.stat()
        file_size = file_stat.st_size

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except UnicodeDecodeError:
            with open(file_path, 'rb') as f:
                content = f.read().hex()

        # 업데이트 시점의 정보를 포함하는 메타데이터를 생성합니다.
        metadata = {
            "original_path": str(file_path.absolute()),
            "file_extension": file_path.suffix,
            "modified_time": datetime.fromtimestamp(file_stat.st_mtime).isoformat(),
            "updated_from_file": datetime.now().isoformat()
        }

        # CRUDOperations를 사용하여 문서를 업데이트합니다.
        return self.crud.update(
            doc_id=doc_id,
            content=content,
            file_size=file_size,
            metadata=metadata
        )


# 이 스크립트가 직접 실행될 때, 아래의 예제 코드를 실행합니다.
if __name__ == "__main__":
    from .db_design import create_database
    import tempfile

    print("=== 파일→SQLite 적재 파이프라인 예제 ===\n")

    # 'test_pipeline' 테넌트용 데이터베이스를 생성합니다.
    db_design = create_database("test_pipeline")
    pipeline = FileToDBPipeline(db_design)

    # 임시 디렉토리를 생성하여 테스트 파일을 관리합니다.
    # with tempfile.TemporaryDirectory() as tmpdir:
    tmpdir = "./test_files_for_pipeline"
    tmp_path = Path(tmpdir)

    tmp_path.mkdir(parents=True, exist_ok=True)

    print("1. 테스트 파일 생성")
    test_files = []
    for i in range(5):
        file_path = tmp_path / f"test_{i+1}.txt"
        file_path.write_text(f"This is test file {i+1}")
        test_files.append(file_path)

    json_file = tmp_path / "data.json"
    json_file.write_text(json.dumps({"key": "value"}))
    test_files.append(json_file)

    print(f"   {len(test_files)}개 파일 생성 완료")

    print("\n2. 단일 파일 적재")
    doc_id = pipeline.load_file(test_files[0])
    print(f"   파일 '{test_files[0].name}' 적재 완료 (ID: {doc_id})")

    print("\n3. 디렉토리 적재 (*.txt)")
    stats = pipeline.load_directory(
        tmp_path,
        pattern="*.txt",
        skip_existing=True
    )
    print(f"   전체: {stats['total_files']}개")
    print(f"   적재: {stats['loaded']}개")
    print(f"   건너뜀: {stats['skipped']}개")
    print(f"   실패: {stats['failed']}개")

    print("\n4. 여러 파일 적재")
    stats = pipeline.load_files(
        [json_file],
        skip_existing=True
    )
    print(f"   JSON 파일 적재: {stats['loaded']}개")

    print("\n5. 데이터베이스 현황")
    total_count = pipeline.crud.count()
    print(f"   전체 문서 수: {total_count}")

    print("\n6. 파일 내용 업데이트")
    test_files[0].write_text("Updated content!")
    success = pipeline.update_file(test_files[0], doc_id)
    print(f"   업데이트 성공: {success}")

    doc = pipeline.crud.read(doc_id)
    print(f"   업데이트된 내용: {doc['content'][:30]}...")
