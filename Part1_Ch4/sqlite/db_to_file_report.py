"""
4-10. SQLite→파일 리포트 생성
데이터베이스 내용을 파일로 깔끔하게 정리하기

데이터베이스 내용을 다양한 형식의 파일로 출력
"""

from pathlib import Path
from typing import List, Dict, Any, Optional
import json
import csv
from datetime import datetime

from .db_design import DatabaseDesign
from .crud_api import CRUDOperations
from .query_api import QueryOperations, QueryFilter, SortParams


class DBToFileReport:
    """
    SQLite 데이터베이스 내용을 파일로 출력하는 클래스

    지원 형식:
    - JSON: 구조화된 데이터 출력
    - CSV: 표 형식 데이터 출력
    - Markdown: 읽기 쉬운 리포트 형식
    - Text: 단순 텍스트 형식
    """

    def __init__(self, db_design: DatabaseDesign):
        """
        Args:
            db_design: DatabaseDesign 인스턴스
        """
        self.db_design = db_design
        self.crud = CRUDOperations(db_design)
        self.query_ops = QueryOperations(db_design)

    def export_to_json(
        self,
        output_path: Path,
        filter_params: Optional[QueryFilter] = None,
        pretty: bool = True
    ) -> Dict[str, Any]:
        """
        JSON 파일로 출력

        Args:
            output_path: 출력 파일 경로
            filter_params: 필터 조건
            pretty: 들여쓰기 여부

        Returns:
            Dict[str, Any]: 출력 통계
        """
        # 데이터 조회
        if filter_params:
            result = self.query_ops.query(filter_params=filter_params)
            documents = result.items
        else:
            documents = self.crud.read_all()

        # JSON 파일 작성
        output_path.parent.mkdir(parents=True, exist_ok=True)

        data = {
            "exported_at": datetime.now().isoformat(),
            "tenant_id": self.db_design.config.tenant_id,
            "total_count": len(documents),
            "documents": documents
        }

        with open(output_path, 'w', encoding='utf-8') as f:
            if pretty:
                json.dump(data, f, indent=2, ensure_ascii=False)
            else:
                json.dump(data, f, ensure_ascii=False)

        return {
            "format": "json",
            "output_path": str(output_path),
            "document_count": len(documents),
            "file_size": output_path.stat().st_size
        }

    def export_to_csv(
        self,
        output_path: Path,
        filter_params: Optional[QueryFilter] = None,
        include_metadata: bool = False
    ) -> Dict[str, Any]:
        """
        CSV 파일로 출력

        Args:
            output_path: 출력 파일 경로
            filter_params: 필터 조건
            include_metadata: 메타데이터 포함 여부

        Returns:
            Dict[str, Any]: 출력 통계
        """
        # 데이터 조회
        if filter_params:
            result = self.query_ops.query(filter_params=filter_params)
            documents = result.items
        else:
            documents = self.crud.read_all()

        if not documents:
            return {
                "format": "csv",
                "output_path": str(output_path),
                "document_count": 0,
                "file_size": 0
            }

        # CSV 파일 작성
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # 필드명 정의
        if include_metadata:
            fieldnames = list(documents[0].keys())
        else:
            fieldnames = ['id', 'filename', 'content', 'file_type', 'file_size', 'created_at', 'updated_at']

        with open(output_path, 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()

            for doc in documents:
                # 메타데이터가 딕셔너리인 경우 JSON 문자열로 변환
                row = doc.copy()
                if 'metadata' in row and isinstance(row['metadata'], dict):
                    row['metadata'] = json.dumps(row['metadata'])

                # 필요한 필드만 선택
                filtered_row = {k: row.get(k, '') for k in fieldnames}
                writer.writerow(filtered_row)

        return {
            "format": "csv",
            "output_path": str(output_path),
            "document_count": len(documents),
            "file_size": output_path.stat().st_size
        }

    def export_to_markdown(
        self,
        output_path: Path,
        filter_params: Optional[QueryFilter] = None,
        include_statistics: bool = True
    ) -> Dict[str, Any]:
        """
        Markdown 파일로 출력

        Args:
            output_path: 출력 파일 경로
            filter_params: 필터 조건
            include_statistics: 통계 정보 포함 여부

        Returns:
            Dict[str, Any]: 출력 통계
        """
        # 데이터 조회
        if filter_params:
            result = self.query_ops.query(filter_params=filter_params)
            documents = result.items
        else:
            documents = self.crud.read_all()

        # Markdown 파일 작성
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            # 제목
            f.write(f"# 데이터베이스 리포트\n\n")
            f.write(f"**생성일시**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write(f"**테넌트**: {self.db_design.config.tenant_id}\n\n")

            # 통계 정보
            if include_statistics:
                stats = self.query_ops.get_statistics()
                f.write("## 통계 정보\n\n")
                f.write(f"- 전체 문서 수: {stats['total_count']}\n")
                f.write(f"- 전체 크기: {stats['total_size']:,} bytes\n")
                f.write(f"- 평균 크기: {stats['average_size']:.2f} bytes\n\n")

                if stats['type_distribution']:
                    f.write("### 파일 타입별 분포\n\n")
                    f.write("| 파일 타입 | 개수 |\n")
                    f.write("|----------|------|\n")
                    for dist in stats['type_distribution']:
                        f.write(f"| {dist['file_type']} | {dist['count']} |\n")
                    f.write("\n")

            # 문서 목록
            f.write("## 문서 목록\n\n")

            if documents:
                for i, doc in enumerate(documents, 1):
                    f.write(f"### {i}. {doc['filename']}\n\n")
                    f.write(f"- **ID**: {doc['id']}\n")
                    f.write(f"- **파일 타입**: {doc['file_type']}\n")
                    f.write(f"- **파일 크기**: {doc['file_size']} bytes\n")
                    f.write(f"- **생성일**: {doc['created_at']}\n")
                    f.write(f"- **수정일**: {doc['updated_at']}\n\n")

                    # 내용 미리보기 (최대 200자)
                    content_preview = doc['content'][:200]
                    if len(doc['content']) > 200:
                        content_preview += "..."
                    f.write(f"**내용 미리보기**:\n```\n{content_preview}\n```\n\n")

                    # 메타데이터
                    if doc.get('metadata'):
                        f.write("**메타데이터**:\n```json\n")
                        f.write(json.dumps(doc['metadata'], indent=2, ensure_ascii=False))
                        f.write("\n```\n\n")

                    f.write("---\n\n")
            else:
                f.write("문서가 없습니다.\n\n")

        return {
            "format": "markdown",
            "output_path": str(output_path),
            "document_count": len(documents),
            "file_size": output_path.stat().st_size
        }

    def export_to_text(
        self,
        output_path: Path,
        filter_params: Optional[QueryFilter] = None
    ) -> Dict[str, Any]:
        """
        텍스트 파일로 출력 (단순 형식)

        Args:
            output_path: 출력 파일 경로
            filter_params: 필터 조건

        Returns:
            Dict[str, Any]: 출력 통계
        """
        # 데이터 조회
        if filter_params:
            result = self.query_ops.query(filter_params=filter_params)
            documents = result.items
        else:
            documents = self.crud.read_all()

        # 텍스트 파일 작성
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("=" * 80 + "\n")
            f.write(f"데이터베이스 리포트 - {self.db_design.config.tenant_id}\n")
            f.write(f"생성일시: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("=" * 80 + "\n\n")

            f.write(f"전체 문서 수: {len(documents)}\n\n")

            for i, doc in enumerate(documents, 1):
                f.write("-" * 80 + "\n")
                f.write(f"문서 #{i}\n")
                f.write("-" * 80 + "\n")
                f.write(f"ID: {doc['id']}\n")
                f.write(f"파일명: {doc['filename']}\n")
                f.write(f"타입: {doc['file_type']}\n")
                f.write(f"크기: {doc['file_size']} bytes\n")
                f.write(f"생성일: {doc['created_at']}\n")
                f.write(f"수정일: {doc['updated_at']}\n")
                f.write("\n내용:\n")
                f.write(doc['content'])
                f.write("\n\n")

        return {
            "format": "text",
            "output_path": str(output_path),
            "document_count": len(documents),
            "file_size": output_path.stat().st_size
        }


if __name__ == "__main__":
    # 사용 예제
    from .db_design import create_database
    from .crud_api import CRUDOperations
    import tempfile

    print("=== SQLite→파일 리포트 생성 예제 ===\n")

    # 데이터베이스 생성 및 샘플 데이터 추가
    db_design = create_database("test_report")
    crud = CRUDOperations(db_design)
    report = DBToFileReport(db_design)

    # 샘플 데이터 생성
    print("1. 샘플 데이터 생성")
    for i in range(5):
        crud.create(
            filename=f"document_{i+1}.txt",
            content=f"This is the content of document {i+1}.\n" * 3,
            file_type="text" if i % 2 == 0 else "markdown",
            file_size=50 + i * 10,
            metadata={"category": "test", "index": i+1}
        )
    print(f"   {crud.count()}개 문서 생성 완료\n")

    # 출력 디렉토리 생성
    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir)

        # 2. JSON 출력
        print("2. JSON 형식으로 출력")
        result = report.export_to_json(output_dir / "report.json")
        print(f"   파일: {result['output_path']}")
        print(f"   문서 수: {result['document_count']}")
        print(f"   파일 크기: {result['file_size']} bytes\n")

        # 3. CSV 출력
        print("3. CSV 형식으로 출력")
        result = report.export_to_csv(output_dir / "report.csv")
        print(f"   파일: {result['output_path']}")
        print(f"   문서 수: {result['document_count']}")
        print(f"   파일 크기: {result['file_size']} bytes\n")

        # 4. Markdown 출력
        print("4. Markdown 형식으로 출력")
        result = report.export_to_markdown(output_dir / "report.md")
        print(f"   파일: {result['output_path']}")
        print(f"   문서 수: {result['document_count']}")
        print(f"   파일 크기: {result['file_size']} bytes\n")

        # 5. Text 출력
        print("5. Text 형식으로 출력")
        result = report.export_to_text(output_dir / "report.txt")
        print(f"   파일: {result['output_path']}")
        print(f"   문서 수: {result['document_count']}")
        print(f"   파일 크기: {result['file_size']} bytes\n")

        # 6. 필터링된 결과 출력
        print("6. 필터링된 결과 출력 (text 타입만)")
        result = report.export_to_json(
            output_dir / "filtered_report.json",
            filter_params=QueryFilter(file_type="text")
        )
        print(f"   문서 수: {result['document_count']}")
