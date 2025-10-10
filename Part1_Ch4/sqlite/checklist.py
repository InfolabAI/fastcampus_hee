"""
4-11. 종합 점검 체크리스트
지금까지 만든 모든 기능이 잘 작동하는지 확인하기

SQLite 모듈의 모든 기능을 테스트하는 체크리스트
"""

from pathlib import Path
from typing import Dict, Any, List
import tempfile
from datetime import datetime

from .db_design import create_database, DatabaseDesign, DatabaseConfig
from .crud_api import CRUDOperations
from .query_api import QueryOperations, QueryFilter, SortParams, PaginationParams, SortOrder
from .file_to_db_pipeline import FileToDBPipeline
from .db_to_file_report import DBToFileReport


class SQLiteChecklist:
    """
    SQLite 모듈 종합 점검 클래스

    모든 기능의 정상 작동 여부를 확인
    """

    def __init__(self):
        """체크리스트 초기화"""
        self.results: List[Dict[str, Any]] = []
        self.passed = 0
        self.failed = 0

    def _check(self, name: str, test_func) -> bool:
        """
        개별 테스트 실행

        Args:
            name: 테스트 이름
            test_func: 테스트 함수

        Returns:
            bool: 테스트 성공 여부
        """
        try:
            test_func()
            self.passed += 1
            self.results.append({
                "name": name,
                "status": "PASS",
                "error": None
            })
            return True
        except Exception as e:
            self.failed += 1
            self.results.append({
                "name": name,
                "status": "FAIL",
                "error": str(e)
            })
            return False

    def run_all_checks(self) -> Dict[str, Any]:
        """
        모든 체크리스트 실행

        Returns:
            Dict[str, Any]: 체크리스트 실행 결과
        """
        print("=" * 80)
        print("SQLite 모듈 종합 점검 체크리스트")
        print("=" * 80)
        print()

        # 임시 디렉토리에서 테스트 실행
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)

            # 1. 데이터베이스 설계 및 초기화 체크
            print("[1] 데이터베이스 설계 및 초기화")
            db_design = None

            def test_db_creation():
                nonlocal db_design
                db_design = create_database("checklist_test", tmp_path / "test.db")
                assert db_design is not None
                assert db_design.db_path.exists()

            self._check("데이터베이스 생성", test_db_creation)

            def test_schema_info():
                info = db_design.get_schema_info()
                assert len(info['tables']) > 0
                assert 'documents' in [t['name'] for t in info['tables']]

            self._check("스키마 정보 조회", test_schema_info)

            # 2. CRUD 작업 체크
            print("\n[2] CRUD 작업")
            crud = CRUDOperations(db_design)

            def test_create():
                doc_id = crud.create(
                    filename="test.txt",
                    content="Test content",
                    file_type="text",
                    file_size=12
                )
                assert doc_id > 0

            self._check("문서 생성 (Create)", test_create)

            def test_read():
                doc = crud.read(1)
                assert doc is not None
                assert doc['filename'] == "test.txt"

            self._check("문서 조회 (Read)", test_read)

            def test_update():
                success = crud.update(1, content="Updated content")
                assert success is True
                doc = crud.read(1)
                assert doc['content'] == "Updated content"

            self._check("문서 수정 (Update)", test_update)

            def test_count():
                count = crud.count()
                assert count == 1

            self._check("문서 개수 조회", test_count)

            # 추가 샘플 데이터 생성
            for i in range(2, 11):
                crud.create(
                    filename=f"file_{i}.txt",
                    content=f"Content {i}",
                    file_type="text" if i % 2 == 0 else "json",
                    file_size=10 + i
                )

            def test_read_all():
                docs = crud.read_all()
                assert len(docs) == 10

            self._check("전체 문서 조회", test_read_all)

            def test_delete():
                success = crud.delete(10)
                assert success is True
                assert crud.count() == 9

            self._check("문서 삭제 (Delete)", test_delete)

            # 3. 쿼리/페이징/정렬 체크
            print("\n[3] 쿼리/페이징/정렬")
            query_ops = QueryOperations(db_design)

            def test_pagination():
                result = query_ops.query(
                    pagination=PaginationParams(page=1, page_size=5)
                )
                assert len(result.items) == 5
                assert result.total_count == 9
                assert result.total_pages == 2

            self._check("페이지네이션", test_pagination)

            def test_sorting():
                result = query_ops.query(
                    sort_params=SortParams(field="filename", order=SortOrder.DESC),
                    pagination=PaginationParams(page=1, page_size=3)
                )
                assert len(result.items) == 3

            self._check("정렬", test_sorting)

            def test_filtering():
                result = query_ops.query(
                    filter_params=QueryFilter(file_type="text")
                )
                assert result.total_count > 0

            self._check("필터링", test_filtering)

            def test_search():
                results = query_ops.search(keyword="file")
                assert len(results) > 0

            self._check("키워드 검색", test_search)

            def test_statistics():
                stats = query_ops.get_statistics()
                assert stats['total_count'] == 9
                assert 'type_distribution' in stats

            self._check("통계 정보 조회", test_statistics)

            # 4. 파일→데이터베이스 파이프라인 체크
            print("\n[4] 파일→데이터베이스 파이프라인")
            pipeline = FileToDBPipeline(db_design)

            # 테스트 파일 생성
            test_files_dir = tmp_path / "test_files"
            test_files_dir.mkdir()

            for i in range(3):
                file_path = test_files_dir / f"pipeline_{i}.txt"
                file_path.write_text(f"Pipeline test {i}")

            def test_load_file():
                file_path = test_files_dir / "pipeline_0.txt"
                doc_id = pipeline.load_file(file_path)
                assert doc_id > 0

            self._check("단일 파일 적재", test_load_file)

            def test_load_directory():
                stats = pipeline.load_directory(
                    test_files_dir,
                    pattern="*.txt",
                    skip_existing=True
                )
                assert stats['loaded'] >= 0
                assert stats['total_files'] == 3

            self._check("디렉토리 파일 적재", test_load_directory)

            def test_update_file():
                file_path = test_files_dir / "pipeline_0.txt"
                file_path.write_text("Updated pipeline test")
                success = pipeline.update_file(file_path, 10)  # 적재된 문서 ID 사용
                assert success is True

            self._check("파일로 문서 업데이트", test_update_file)

            # 5. 데이터베이스→파일 리포트 체크
            print("\n[5] 데이터베이스→파일 리포트")
            report = DBToFileReport(db_design)
            report_dir = tmp_path / "reports"
            report_dir.mkdir()

            def test_export_json():
                result = report.export_to_json(report_dir / "report.json")
                assert result['document_count'] > 0
                assert (report_dir / "report.json").exists()

            self._check("JSON 리포트 생성", test_export_json)

            def test_export_csv():
                result = report.export_to_csv(report_dir / "report.csv")
                assert result['document_count'] > 0
                assert (report_dir / "report.csv").exists()

            self._check("CSV 리포트 생성", test_export_csv)

            def test_export_markdown():
                result = report.export_to_markdown(report_dir / "report.md")
                assert result['document_count'] > 0
                assert (report_dir / "report.md").exists()

            self._check("Markdown 리포트 생성", test_export_markdown)

            def test_export_text():
                result = report.export_to_text(report_dir / "report.txt")
                assert result['document_count'] > 0
                assert (report_dir / "report.txt").exists()

            self._check("Text 리포트 생성", test_export_text)

            # 6. 멀티테넌시 체크
            print("\n[6] 멀티테넌시")

            def test_multi_tenant():
                tenant1_db = create_database("tenant1", tmp_path / "tenant1.db")
                tenant2_db = create_database("tenant2", tmp_path / "tenant2.db")

                # 각 테넌트에 데이터 추가
                crud1 = CRUDOperations(tenant1_db)
                crud2 = CRUDOperations(tenant2_db)

                crud1.create(filename="tenant1_file.txt", content="Tenant 1 data")
                crud2.create(filename="tenant2_file.txt", content="Tenant 2 data")

                # 데이터 격리 확인
                assert crud1.count() == 1
                assert crud2.count() == 1

                doc1 = crud1.read(1)
                doc2 = crud2.read(1)

                assert doc1['content'] == "Tenant 1 data"
                assert doc2['content'] == "Tenant 2 data"

            self._check("멀티테넌시 지원", test_multi_tenant)

        # 결과 요약
        print("\n" + "=" * 80)
        print("체크리스트 결과 요약")
        print("=" * 80)

        for result in self.results:
            status_symbol = "✓" if result['status'] == "PASS" else "✗"
            print(f"{status_symbol} {result['name']}: {result['status']}")
            if result['error']:
                print(f"  오류: {result['error']}")

        print("\n" + "-" * 80)
        print(f"통과: {self.passed}/{len(self.results)}")
        print(f"실패: {self.failed}/{len(self.results)}")
        print(f"성공률: {(self.passed/len(self.results)*100):.1f}%")
        print("=" * 80)

        return {
            "total": len(self.results),
            "passed": self.passed,
            "failed": self.failed,
            "success_rate": round(self.passed / len(self.results) * 100, 2),
            "results": self.results,
            "timestamp": datetime.now().isoformat()
        }


if __name__ == "__main__":
    # 체크리스트 실행
    checklist = SQLiteChecklist()
    summary = checklist.run_all_checks()

    # 결과를 JSON 파일로 저장
    import json
    result_path = Path("checklist_result.json")
    with open(result_path, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    print(f"\n체크리스트 결과가 {result_path}에 저장되었습니다.")
