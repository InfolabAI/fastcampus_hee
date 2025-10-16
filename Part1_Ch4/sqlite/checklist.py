"""
4-11. 종합 점검 체크리스트
지금까지 만든 모든 기능이 잘 작동하는지 확인하기

SQLite 모듈의 모든 기능을 테스트하는 체크리스트
"""

# pathlib.Path: 파일 시스템 경로를 객체 지향적으로 다루기 위한 클래스입니다.
from pathlib import Path
# typing: 타입 힌트를 지원하는 라이브러리입니다.
from typing import Dict, Any, List
# tempfile: 임시 파일 및 디렉토리를 생성하는 모듈입니다.
import tempfile
# datetime: 날짜와 시간을 다루는 모듈입니다.
from datetime import datetime

# 이전에 구현한 SQLite 관련 모듈들을 모두 임포트합니다.
# 이 클래스들은 체크리스트에서 각 기능을 테스트하는 데 사용됩니다.
from .db_design import create_database, DatabaseDesign, DatabaseConfig
from .crud_api import CRUDOperations
from .query_api import QueryOperations, QueryFilter, SortParams, PaginationParams, SortOrder
from .file_to_db_pipeline import FileToDBPipeline
from .db_to_file_report import DBToFileReport


class SQLiteChecklist:
    """
    SQLite 모듈의 모든 기능을 종합적으로 점검하는 클래스입니다.
    각 기능이 예상대로 정상 작동하는지 확인하기 위한 테스트들을 포함합니다.
    """

    def __init__(self):
        """체크리스트를 초기화합니다."""
        # 각 테스트의 결과를 저장할 리스트입니다.
        self.results: List[Dict[str, Any]] = []
        # 통과한 테스트의 수를 저장합니다.
        self.passed = 0
        # 실패한 테스트의 수를 저장합니다.
        self.failed = 0

    def _check(self, name: str, test_func) -> bool:
        """
        개별 테스트를 실행하고 결과를 기록합니다.

        Args:
            name (str): 테스트의 이름입니다.
            test_func: 실행할 테스트 로직을 담고 있는 함수입니다.

        Returns:
            bool: 테스트가 성공했으면 True, 실패했으면 False를 반환합니다.
        """
        try:
            # 테스트 함수를 실행합니다.
            test_func()
            # 테스트가 성공하면, 통과 카운트를 1 증가시킵니다.
            self.passed += 1
            # 결과 리스트에 'PASS' 상태와 함께 테스트 결과를 추가합니다.
            self.results.append({
                "name": name,
                "status": "PASS",
                "error": None
            })
            return True
        except Exception as e:
            # 테스트 중 예외가 발생하면, 실패 카운트를 1 증가시킵니다.
            self.failed += 1
            # 결과 리스트에 'FAIL' 상태와 발생한 오류 메시지를 추가합니다.
            self.results.append({
                "name": name,
                "status": "FAIL",
                "error": str(e)
            })
            return False

    def run_all_checks(self) -> Dict[str, Any]:
        """
        정의된 모든 체크리스트 항목을 순서대로 실행합니다.

        Returns:
            Dict[str, Any]: 모든 테스트의 실행 결과 요약 정보를 담은 딕셔너리입니다.
        """
        print("=" * 80)
        print("SQLite 모듈 종합 점검 체크리스트")
        print("=" * 80)
        print()

        # 임시 디렉토리를 생성하여 테스트 중에 발생하는 파일들을 관리합니다.
        # 'with' 구문이 끝나면 임시 디렉토리와 그 안의 파일들은 자동으로 삭제됩니다.
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)

            # =================================================================
            # 1. 데이터베이스 설계 및 초기화 체크 (4-6)
            # =================================================================
            print("[1] 데이터베이스 설계 및 초기화")
            db_design = None  # 테스트에서 사용될 DatabaseDesign 인스턴스를 담을 변수

            def test_db_creation():
                """데이터베이스 파일이 정상적으로 생성되는지 테스트합니다."""
                nonlocal db_design
                # 'checklist_test' 테넌트 ID와 임시 경로를 사용하여 데이터베이스를 생성합니다.
                db_design = create_database("checklist_test", tmp_path / "test.db")
                # 데이터베이스 객체가 생성되었는지 확인합니다.
                assert db_design is not None
                # 실제 데이터베이스 파일이 디스크에 생성되었는지 확인합니다.
                assert db_design.db_path.exists()

            self._check("데이터베이스 생성", test_db_creation)

            def test_schema_info():
                """스키마 정보 조회가 정상적으로 작동하는지 테스트합니다."""
                info = db_design.get_schema_info()
                # 테이블 정보가 존재하는지 확인합니다.
                assert len(info['tables']) > 0
                # 'documents' 테이블이 스키마에 포함되어 있는지 확인합니다.
                assert 'documents' in [t['name'] for t in info['tables']]

            self._check("스키마 정보 조회", test_schema_info)

            # =================================================================
            # 2. CRUD 작업 체크 (4-7)
            # =================================================================
            print("\n[2] CRUD 작업")
            crud = CRUDOperations(db_design)

            def test_create():
                """문서 생성(Create) 기능이 정상 작동하는지 테스트합니다."""
                doc_id = crud.create(
                    filename="test.txt",
                    content="Test content",
                    file_type="text",
                    file_size=12
                )
                # 생성된 문서 ID가 0보다 큰 값인지 확인합니다.
                assert doc_id > 0

            self._check("문서 생성 (Create)", test_create)

            def test_read():
                """문서 조회(Read) 기능이 정상 작동하는지 테스트합니다."""
                doc = crud.read(1)
                # 문서가 정상적으로 조회되었는지 확인합니다.
                assert doc is not None
                # 조회된 문서의 파일명이 일치하는지 확인합니다.
                assert doc['filename'] == "test.txt"

            self._check("문서 조회 (Read)", test_read)

            def test_update():
                """문서 수정(Update) 기능이 정상 작동하는지 테스트합니다."""
                success = crud.update(1, content="Updated content")
                # 업데이트가 성공적으로 완료되었는지 확인합니다.
                assert success is True
                doc = crud.read(1)
                # 내용이 실제로 변경되었는지 확인합니다.
                assert doc['content'] == "Updated content"

            self._check("문서 수정 (Update)", test_update)

            def test_count():
                """문서 개수 조회 기능이 정상 작동하는지 테스트합니다."""
                count = crud.count()
                assert count == 1

            self._check("문서 개수 조회", test_count)

            # 테스트를 위한 추가 샘플 데이터를 생성합니다.
            for i in range(2, 11):
                crud.create(
                    filename=f"file_{i}.txt",
                    content=f"Content {i}",
                    file_type="text" if i % 2 == 0 else "json",
                    file_size=10 + i
                )

            def test_read_all():
                """전체 문서 조회 기능이 정상 작동하는지 테스트합니다."""
                docs = crud.read_all()
                # 총 10개의 문서가 조회되는지 확인합니다.
                assert len(docs) == 10

            self._check("전체 문서 조회", test_read_all)

            def test_delete():
                """문서 삭제(Delete) 기능이 정상 작동하는지 테스트합니다."""
                success = crud.delete(10)
                # 삭제가 성공적으로 완료되었는지 확인합니다.
                assert success is True
                # 문서 개수가 9개로 줄었는지 확인합니다.
                assert crud.count() == 9

            self._check("문서 삭제 (Delete)", test_delete)

            # =================================================================
            # 3. 쿼리/페이징/정렬 체크 (4-8)
            # =================================================================
            print("\n[3] 쿼리/페이징/정렬")
            query_ops = QueryOperations(db_design)

            def test_pagination():
                """페이지네이션 기능이 정상 작동하는지 테스트합니다."""
                result = query_ops.query(
                    pagination=PaginationParams(page=1, page_size=5)
                )
                # 한 페이지에 5개의 항목이 있는지 확인합니다.
                assert len(result.items) == 5
                # 전체 항목 수가 9개인지 확인합니다.
                assert result.total_count == 9
                # 전체 페이지 수가 2개인지 확인합니다.
                assert result.total_pages == 2

            self._check("페이지네이션", test_pagination)

            def test_sorting():
                """정렬 기능이 정상 작동하는지 테스트합니다."""
                result = query_ops.query(
                    sort_params=SortParams(field="filename", order=SortOrder.DESC),
                    pagination=PaginationParams(page=1, page_size=3)
                )
                # 3개의 항목이 반환되었는지 확인합니다.
                assert len(result.items) == 3

            self._check("정렬", test_sorting)

            def test_filtering():
                """필터링 기능이 정상 작동하는지 테스트합니다."""
                result = query_ops.query(
                    filter_params=QueryFilter(file_type="text")
                )
                # 'text' 타입의 문서가 1개 이상 존재하는지 확인합니다.
                assert result.total_count > 0

            self._check("필터링", test_filtering)

            def test_search():
                """키워드 검색 기능이 정상 작동하는지 테스트합니다."""
                results = query_ops.search(keyword="file")
                # 'file' 키워드를 포함하는 결과가 있는지 확인합니다.
                assert len(results) > 0

            self._check("키워드 검색", test_search)

            def test_statistics():
                """통계 정보 조회 기능이 정상 작동하는지 테스트합니다."""
                stats = query_ops.get_statistics()
                # 전체 문서 수가 9개인지 확인합니다.
                assert stats['total_count'] == 9
                # 파일 타입별 분포 정보가 포함되어 있는지 확인합니다.
                assert 'type_distribution' in stats

            self._check("통계 정보 조회", test_statistics)

            # =================================================================
            # 4. 파일→데이터베이스 파이프라인 체크 (4-9)
            # =================================================================
            print("\n[4] 파일→데이터베이스 파이프라인")
            pipeline = FileToDBPipeline(db_design)

            # 파이프라인 테스트를 위한 임시 파일들을 생성합니다.
            test_files_dir = tmp_path / "test_files"
            test_files_dir.mkdir()

            for i in range(3):
                file_path = test_files_dir / f"pipeline_{i}.txt"
                file_path.write_text(f"Pipeline test {i}")

            def test_load_file():
                """단일 파일 적재 기능이 정상 작동하는지 테스트합니다."""
                file_path = test_files_dir / "pipeline_0.txt"
                doc_id = pipeline.load_file(file_path)
                # 적재 후 문서 ID가 반환되는지 확인합니다.
                assert doc_id > 0

            self._check("단일 파일 적재", test_load_file)

            def test_load_directory():
                """디렉토리 파일 적재 기능이 정상 작동하는지 테스트합니다."""
                stats = pipeline.load_directory(
                    test_files_dir,
                    pattern="*.txt",
                    skip_existing=True
                )
                # 적재된 파일 수가 0 이상인지 확인합니다.
                assert stats['loaded'] >= 0
                # 전체 파일 수가 3개인지 확인합니다.
                assert stats['total_files'] == 3

            self._check("디렉토리 파일 적재", test_load_directory)

            def test_update_file():
                """파일 내용으로 문서를 업데이트하는 기능이 정상 작동하는지 테스트합니다."""
                file_path = test_files_dir / "pipeline_0.txt"
                file_path.write_text("Updated pipeline test")
                # 이전에 적재된 문서 ID(10)를 사용하여 업데이트를 시도합니다.
                success = pipeline.update_file(file_path, 10)  # 적재된 문서 ID 사용
                assert success is True

            self._check("파일로 문서 업데이트", test_update_file)

            # =================================================================
            # 5. 데이터베이스→파일 리포트 체크 (4-10)
            # =================================================================
            print("\n[5] 데이터베이스→파일 리포트")
            report = DBToFileReport(db_design)
            report_dir = tmp_path / "reports"
            report_dir.mkdir()

            def test_export_json():
                """JSON 리포트 생성 기능이 정상 작동하는지 테스트합니다."""
                result = report.export_to_json(report_dir / "report.json")
                # 리포트에 포함된 문서 수가 0보다 큰지 확인합니다.
                assert result['document_count'] > 0
                # 리포트 파일이 실제로 생성되었는지 확인합니다.
                assert (report_dir / "report.json").exists()

            self._check("JSON 리포트 생성", test_export_json)

            def test_export_csv():
                """CSV 리포트 생성 기능이 정상 작동하는지 테스트합니다."""
                result = report.export_to_csv(report_dir / "report.csv")
                assert result['document_count'] > 0
                assert (report_dir / "report.csv").exists()

            self._check("CSV 리포트 생성", test_export_csv)

            def test_export_markdown():
                """Markdown 리포트 생성 기능이 정상 작동하는지 테스트합니다."""
                result = report.export_to_markdown(report_dir / "report.md")
                assert result['document_count'] > 0
                assert (report_dir / "report.md").exists()

            self._check("Markdown 리포트 생성", test_export_markdown)

            def test_export_text():
                """Text 리포트 생성 기능이 정상 작동하는지 테스트합니다."""
                result = report.export_to_text(report_dir / "report.txt")
                assert result['document_count'] > 0
                assert (report_dir / "report.txt").exists()

            self._check("Text 리포트 생성", test_export_text)

            # =================================================================
            # 6. 멀티테넌시 체크
            # =================================================================
            print("\n[6] 멀티테넌시")

            def test_multi_tenant():
                """데이터베이스가 테넌트별로 격리되는지 테스트합니다."""
                # 두 개의 다른 테넌트에 대한 데이터베이스를 생성합니다.
                tenant1_db = create_database("tenant1", tmp_path / "tenant1.db")
                tenant2_db = create_database("tenant2", tmp_path / "tenant2.db")

                # 각 테넌트의 데이터베이스에 데이터를 추가합니다.
                crud1 = CRUDOperations(tenant1_db)
                crud2 = CRUDOperations(tenant2_db)

                crud1.create(filename="tenant1_file.txt", content="Tenant 1 data")
                crud2.create(filename="tenant2_file.txt", content="Tenant 2 data")

                # 각 테넌트의 데이터가 서로 격리되어 있는지 확인합니다.
                assert crud1.count() == 1
                assert crud2.count() == 1

                doc1 = crud1.read(1)
                doc2 = crud2.read(1)

                assert doc1['content'] == "Tenant 1 data"
                assert doc2['content'] == "Tenant 2 data"

            self._check("멀티테넌시 지원", test_multi_tenant)

        # =================================================================
        # 결과 요약 출력
        # =================================================================
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

        # 최종 결과 요약 딕셔너리를 반환합니다.
        return {
            "total": len(self.results),
            "passed": self.passed,
            "failed": self.failed,
            "success_rate": round(self.passed / len(self.results) * 100, 2),
            "results": self.results,
            "timestamp": datetime.now().isoformat()
        }


# 이 스크립트가 직접 실행될 때,
if __name__ == "__main__":
    # SQLiteChecklist 인스턴스를 생성합니다.
    checklist = SQLiteChecklist()
    # 모든 체크를 실행하고 결과를 받습니다.
    summary = checklist.run_all_checks()

    # 결과를 JSON 파일로 저장합니다.
    import json
    result_path = Path("checklist_result.json")
    with open(result_path, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    print(f"\n체크리스트 결과가 {result_path}에 저장되었습니다.")
