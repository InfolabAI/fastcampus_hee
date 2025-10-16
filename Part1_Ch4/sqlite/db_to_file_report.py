"""
4-10. SQLite→파일 리포트 생성
데이터베이스 내용을 파일로 깔끔하게 정리하기

데이터베이스 내용을 다양한 형식의 파일로 출력
"""

# pathlib.Path: 파일 시스템 경로를 객체 지향적으로 다루기 위한 클래스입니다.
from pathlib import Path
# typing: 타입 힌트를 지원하는 라이브러리입니다.
from typing import List, Dict, Any, Optional
# json: JSON 데이터를 다루기 위한 모듈입니다.
import json
# csv: CSV(Comma Separated Values) 파일을 다루기 위한 모듈입니다.
import csv
# datetime: 날짜와 시간을 다루는 모듈입니다.
from datetime import datetime

# 이전에 구현한 데이터베이스 관련 모듈들을 임포트합니다.
from .db_design import DatabaseDesign
from .crud_api import CRUDOperations
from .query_api import QueryOperations, QueryFilter, SortParams


class DBToFileReport:
    """
    SQLite 데이터베이스의 내용을 다양한 형식의 파일로 내보내는(export) 클래스입니다.

    지원하는 형식:
    - JSON: 구조화된 데이터를 표현하기에 적합합니다.
    - CSV: 표 형식의 데이터를 다루는 데 유용합니다.
    - Markdown: 사람이 읽기 쉬운 리포트 형식으로 문서를 정리합니다.
    - Text: 가장 기본적인 텍스트 형식으로 데이터를 나열합니다.
    """

    def __init__(self, db_design: DatabaseDesign):
        """
        DBToFileReport 클래스의 인스턴스를 초기화합니다.

        Args:
            db_design (DatabaseDesign): 데이터베이스 연결 및 스키마 정보를 담고 있는
                                       DatabaseDesign 객체입니다.
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
        데이터베이스의 문서들을 JSON 파일로 내보냅니다.

        Args:
            output_path (Path): 결과 JSON 파일을 저장할 경로입니다.
            filter_params (Optional[QueryFilter]): 문서들을 필터링할 조건입니다.
            pretty (bool): JSON 출력을 사람이 읽기 쉽게 들여쓰기할지 여부입니다.

        Returns:
            Dict[str, Any]: 내보내기 작업의 결과(포맷, 경로, 문서 수, 파일 크기)를 담은 딕셔너리.
        """
        # 필터 조건이 있으면 쿼리를 통해, 없으면 전체 문서를 조회합니다.
        if filter_params:
            result = self.query_ops.query(filter_params=filter_params)
            documents = result.items
        else:
            documents = self.crud.read_all()

        # 출력 디렉토리가 없으면 생성합니다.
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # JSON 파일에 저장할 데이터를 구성합니다.
        data = {
            "exported_at": datetime.now().isoformat(),
            "tenant_id": self.db_design.config.tenant_id,
            "total_count": len(documents),
            "documents": documents
        }

        # 파일에 JSON 데이터를 씁니다.
        with open(output_path, 'w', encoding='utf-8') as f:
            if pretty:
                # indent=2: 2칸 들여쓰기로 가독성을 높입니다.
                # ensure_ascii=False: 한글 등 비-ASCII 문자가 깨지지 않도록 합니다.
                json.dump(data, f, indent=2, ensure_ascii=False)
            else:
                json.dump(data, f, ensure_ascii=False)

        # 내보내기 작업의 통계 정보를 반환합니다.
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
        데이터베이스의 문서들을 CSV 파일로 내보냅니다.

        Args:
            output_path (Path): 결과 CSV 파일을 저장할 경로입니다.
            filter_params (Optional[QueryFilter]): 문서들을 필터링할 조건입니다.
            include_metadata (bool): CSV 파일에 'metadata' 컬럼을 포함할지 여부입니다.

        Returns:
            Dict[str, Any]: 내보내기 작업의 결과 정보를 담은 딕셔너리.
        """
        if filter_params:
            result = self.query_ops.query(filter_params=filter_params)
            documents = result.items
        else:
            documents = self.crud.read_all()

        # 문서가 없으면 빈 파일을 만들지 않고 바로 반환합니다.
        if not documents:
            return {
                "format": "csv",
                "output_path": str(output_path),
                "document_count": 0,
                "file_size": 0
            }

        output_path.parent.mkdir(parents=True, exist_ok=True)

        # CSV 파일의 헤더(필드명)를 정의합니다.
        if include_metadata:
            fieldnames = list(documents[0].keys())
        else:
            fieldnames = ['id', 'filename', 'content',
                          'file_type', 'file_size', 'created_at', 'updated_at']

        # CSV 파일을 씁니다. newline=''은 불필요한 빈 줄이 생기는 것을 방지합니다.
        with open(output_path, 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()

            for doc in documents:
                row = doc.copy()
                # metadata가 딕셔너리 형태이면 CSV에 쓰기 위해 JSON 문자열로 변환합니다.
                if 'metadata' in row and isinstance(row['metadata'], dict):
                    row['metadata'] = json.dumps(row['metadata'])

                # 정의된 필드명에 해당하는 값만 선택하여 행을 구성합니다.
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
        데이터베이스의 문서들을 Markdown 파일 형식의 리포트로 내보냅니다.

        Args:
            output_path (Path): 결과 Markdown 파일을 저장할 경로입니다.
            filter_params (Optional[QueryFilter]): 문서들을 필터링할 조건입니다.
            include_statistics (bool): 리포트에 통계 정보를 포함할지 여부입니다.

        Returns:
            Dict[str, Any]: 내보내기 작업의 결과 정보를 담은 딕셔너리.
        """
        if filter_params:
            result = self.query_ops.query(filter_params=filter_params)
            documents = result.items
        else:
            documents = self.crud.read_all()

        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            # 리포트의 제목과 기본 정보를 작성합니다.
            f.write(f"# 데이터베이스 리포트\n\n")
            f.write(
                f"**생성일시**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write(f"**테넌트**: {self.db_design.config.tenant_id}\n\n")

            # 통계 정보를 포함하도록 설정된 경우, 통계 섹션을 추가합니다.
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

            # 문서 목록 섹션을 작성합니다.
            f.write("## 문서 목록\n\n")

            if documents:
                for i, doc in enumerate(documents, 1):
                    f.write(f"### {i}. {doc['filename']}\n\n")
                    f.write(f"- **ID**: {doc['id']}\n")
                    f.write(f"- **파일 타입**: {doc['file_type']}\n")
                    f.write(f"- **파일 크기**: {doc['file_size']} bytes\n")
                    f.write(f"- **생성일**: {doc['created_at']}\n")
                    f.write(f"- **수정일**: {doc['updated_at']}\n\n")

                    # 내용의 일부(최대 200자)를 미리보기로 보여줍니다.
                    content_preview = doc['content'][:200]
                    if len(doc['content']) > 200:
                        content_preview += "..."
                    f.write(f"**내용 미리보기**:\n```\n{content_preview}\n```\n\n")

                    # 메타데이터가 있으면 JSON 형식으로 예쁘게 보여줍니다.
                    if doc.get('metadata'):
                        f.write("**메타데이터**:\n```json\n")
                        f.write(json.dumps(
                            doc['metadata'], indent=2, ensure_ascii=False))
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
        데이터베이스의 문서들을 단순 텍스트 파일로 내보냅니다.

        Args:
            output_path (Path): 결과 텍스트 파일을 저장할 경로입니다.
            filter_params (Optional[QueryFilter]): 문서들을 필터링할 조건입니다.

        Returns:
            Dict[str, Any]: 내보내기 작업의 결과 정보를 담은 딕셔너리.
        """
        if filter_params:
            result = self.query_ops.query(filter_params=filter_params)
            documents = result.items
        else:
            documents = self.crud.read_all()

        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            # 리포트 헤더를 작성합니다.
            f.write("=" * 80 + "\n")
            f.write(f"데이터베이스 리포트 - {self.db_design.config.tenant_id}\n")
            f.write(f"생성일시: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("=" * 80 + "\n\n")

            f.write(f"전체 문서 수: {len(documents)}\n\n")

            # 각 문서를 순회하며 정보를 텍스트 형식으로 씁니다.
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


# 이 스크립트가 직접 실행될 때, 아래의 예제 코드를 실행합니다.
if __name__ == "__main__":
    from .db_design import create_database
    from .crud_api import CRUDOperations
    import tempfile

    print("=== SQLite→파일 리포트 생성 예제 ===\n")

    # 'test_report' 테넌트용 데이터베이스를 생성하고 샘플 데이터를 추가합니다.
    db_design = create_database("test_report")
    crud = CRUDOperations(db_design)
    report = DBToFileReport(db_design)

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

    # 임시 디렉토리를 사용하여 리포트 파일을 생성합니다.
    tmpdir = './test_report'
    output_dir = Path(tmpdir)

    print(f"리포트 파일이 생성될 임시 디렉토리: {output_dir}\n")
    print("2. JSON 형식으로 출력")
    result = report.export_to_json(output_dir / "report.json")
    print(f"   파일: {result['output_path']}")
    print(f"   문서 수: {result['document_count']}")
    print(f"   파일 크기: {result['file_size']} bytes\n")

    print("3. CSV 형식으로 출력")
    result = report.export_to_csv(output_dir / "report.csv")
    print(f"   파일: {result['output_path']}")
    print(f"   문서 수: {result['document_count']}")
    print(f"   파일 크기: {result['file_size']} bytes\n")

    print("4. Markdown 형식으로 출력")
    result = report.export_to_markdown(output_dir / "report.md")
    print(f"   파일: {result['output_path']}")
    print(f"   문서 수: {result['document_count']}")
    print(f"   파일 크기: {result['file_size']} bytes\n")

    print("5. Text 형식으로 출력")
    result = report.export_to_text(output_dir / "report.txt")
    print(f"   파일: {result['output_path']}")
    print(f"   문서 수: {result['document_count']}")
    print(f"   파일 크기: {result['file_size']} bytes\n")

    print("6. 필터링된 결과 출력 (text 타입만)")
    result = report.export_to_json(
        output_dir / "filtered_report.json",
        filter_params=QueryFilter(file_type="text")
    )
    print(f"   문서 수: {result['document_count']}")
