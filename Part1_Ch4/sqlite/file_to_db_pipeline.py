"""
4-9. 파일→SQLite 적재 파이프라인
파일 내용을 데이터베이스에 자동으로 옮겨 담기

파일 시스템에서 파일을 읽어 SQLite 데이터베이스로 적재하는 파이프라인
"""

from pathlib import Path
from typing import List, Optional, Dict, Any
import json
from datetime import datetime

from .db_design import DatabaseDesign
from .crud_api import CRUDOperations


class FileToDBPipeline:
    """
    파일을 SQLite 데이터베이스로 적재하는 파이프라인

    파일 시스템의 파일들을 읽어서 데이터베이스에 저장
    """

    def __init__(self, db_design: DatabaseDesign):
        """
        Args:
            db_design: DatabaseDesign 인스턴스
        """
        self.db_design = db_design
        self.crud = CRUDOperations(db_design)

    def load_file(
        self,
        file_path: Path,
        additional_metadata: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        단일 파일을 데이터베이스에 적재

        Args:
            file_path: 파일 경로
            additional_metadata: 추가 메타데이터

        Returns:
            int: 생성된 문서 ID

        Raises:
            FileNotFoundError: 파일이 존재하지 않을 때
            PermissionError: 파일 읽기 권한이 없을 때
        """
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        # 파일 정보 수집
        file_stat = file_path.stat()
        file_size = file_stat.st_size

        # 파일 내용 읽기
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except UnicodeDecodeError:
            # 바이너리 파일인 경우
            with open(file_path, 'rb') as f:
                content = f.read().hex()  # 바이너리를 hex 문자열로 변환

        # 메타데이터 생성
        metadata = {
            "original_path": str(file_path.absolute()),
            "file_extension": file_path.suffix,
            "created_time": datetime.fromtimestamp(file_stat.st_ctime).isoformat(),
            "modified_time": datetime.fromtimestamp(file_stat.st_mtime).isoformat(),
        }

        # 추가 메타데이터 병합
        if additional_metadata:
            metadata.update(additional_metadata)

        # 데이터베이스에 저장
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
        디렉토리의 파일들을 데이터베이스에 적재

        Args:
            directory_path: 디렉토리 경로
            pattern: 파일 패턴 (예: "*.txt", "*.json")
            recursive: 하위 디렉토리 포함 여부
            skip_existing: 이미 존재하는 파일 건너뛰기

        Returns:
            Dict[str, Any]: 적재 결과 통계
        """
        if not directory_path.is_dir():
            raise NotADirectoryError(f"Not a directory: {directory_path}")

        # 파일 검색
        if recursive:
            files = list(directory_path.rglob(pattern))
        else:
            files = list(directory_path.glob(pattern))

        # 파일만 필터링 (디렉토리 제외)
        files = [f for f in files if f.is_file()]

        # 적재 통계
        stats = {
            "total_files": len(files),
            "loaded": 0,
            "skipped": 0,
            "failed": 0,
            "loaded_ids": [],
            "failed_files": []
        }

        # 기존 파일 목록 조회 (skip_existing=True인 경우)
        existing_filenames = set()
        if skip_existing:
            all_docs = self.crud.read_all()
            existing_filenames = {doc['filename'] for doc in all_docs}

        # 각 파일 적재
        for file_path in files:
            try:
                # 이미 존재하는 파일은 건너뛰기
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

    def load_files(
        self,
        file_paths: List[Path],
        skip_existing: bool = True
    ) -> Dict[str, Any]:
        """
        여러 파일을 데이터베이스에 적재

        Args:
            file_paths: 파일 경로 리스트
            skip_existing: 이미 존재하는 파일 건너뛰기

        Returns:
            Dict[str, Any]: 적재 결과 통계
        """
        stats = {
            "total_files": len(file_paths),
            "loaded": 0,
            "skipped": 0,
            "failed": 0,
            "loaded_ids": [],
            "failed_files": []
        }

        # 기존 파일 목록 조회
        existing_filenames = set()
        if skip_existing:
            all_docs = self.crud.read_all()
            existing_filenames = {doc['filename'] for doc in all_docs}

        for file_path in file_paths:
            try:
                # 이미 존재하는 파일은 건너뛰기
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
        파일 내용으로 기존 문서 업데이트

        Args:
            file_path: 파일 경로
            doc_id: 업데이트할 문서 ID

        Returns:
            bool: 업데이트 성공 여부
        """
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        # 파일 정보 수집
        file_stat = file_path.stat()
        file_size = file_stat.st_size

        # 파일 내용 읽기
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except UnicodeDecodeError:
            with open(file_path, 'rb') as f:
                content = f.read().hex()

        # 메타데이터 생성
        metadata = {
            "original_path": str(file_path.absolute()),
            "file_extension": file_path.suffix,
            "modified_time": datetime.fromtimestamp(file_stat.st_mtime).isoformat(),
            "updated_from_file": datetime.now().isoformat()
        }

        # 업데이트
        return self.crud.update(
            doc_id=doc_id,
            content=content,
            file_size=file_size,
            metadata=metadata
        )


if __name__ == "__main__":
    # 사용 예제
    from .db_design import create_database
    import tempfile

    print("=== 파일→SQLite 적재 파이프라인 예제 ===\n")

    # 데이터베이스 생성
    db_design = create_database("test_pipeline")
    pipeline = FileToDBPipeline(db_design)

    # 임시 디렉토리 및 테스트 파일 생성
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)

        # 테스트 파일 생성
        print("1. 테스트 파일 생성")
        test_files = []
        for i in range(5):
            file_path = tmp_path / f"test_{i+1}.txt"
            file_path.write_text(f"This is test file {i+1}")
            test_files.append(file_path)

        # JSON 파일 생성
        json_file = tmp_path / "data.json"
        json_file.write_text(json.dumps({"key": "value"}))
        test_files.append(json_file)

        print(f"   {len(test_files)}개 파일 생성 완료")

        # 2. 단일 파일 적재
        print("\n2. 단일 파일 적재")
        doc_id = pipeline.load_file(test_files[0])
        print(f"   파일 '{test_files[0].name}' 적재 완료 (ID: {doc_id})")

        # 3. 디렉토리 적재
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

        # 4. 여러 파일 적재
        print("\n4. 여러 파일 적재")
        stats = pipeline.load_files(
            [json_file],
            skip_existing=True
        )
        print(f"   JSON 파일 적재: {stats['loaded']}개")

        # 5. 전체 문서 수 확인
        print("\n5. 데이터베이스 현황")
        total_count = pipeline.crud.count()
        print(f"   전체 문서 수: {total_count}")

        # 6. 파일 업데이트
        print("\n6. 파일 내용 업데이트")
        test_files[0].write_text("Updated content!")
        success = pipeline.update_file(test_files[0], doc_id)
        print(f"   업데이트 성공: {success}")

        # 업데이트된 내용 확인
        doc = pipeline.crud.read(doc_id)
        print(f"   업데이트된 내용: {doc['content'][:30]}...")
