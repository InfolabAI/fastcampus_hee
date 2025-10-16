
import os
import subprocess
import sys
import shutil
import sqlite3

# 출력에 사용할 색상 코드
RED = '\033[0;31m'
GREEN = '\033[0;32m'
YELLOW = '\033[1;33m'
BLUE = '\033[0;34m'
NC = '\033[0m'

# 테스트 결과 카운터
TOTAL_TESTS = 0
PASSED_TESTS = 0
FAILED_TESTS = 0

# 경로 설정
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, '..', '..'))
TEST_DATA_DIR = os.path.join(SCRIPT_DIR, "test_data")
TEST_OUTPUT_DIR = os.path.join(SCRIPT_DIR, "test_output")
TEST_REPORT_DIR = os.path.join(SCRIPT_DIR, "test_report")

# PYTHONPATH 설정
os.environ['PYTHONPATH'] = f"{PROJECT_ROOT}:{os.environ.get('PYTHONPATH', '')}"

# 헬퍼 함수
def print_header(message):
    print("")
    print(f"{BLUE}================================================================================{NC}")
    print(f"{BLUE}{message}{NC}")
    print(f"{BLUE}================================================================================{NC}")
    print("")

def print_test(message):
    print(f"{YELLOW}[TEST]{NC} {message}")

def print_pass(message):
    global PASSED_TESTS, TOTAL_TESTS
    print(f"{GREEN}[PASS]{NC} {message}")
    PASSED_TESTS += 1
    TOTAL_TESTS += 1

def print_fail(message):
    global FAILED_TESTS, TOTAL_TESTS
    print(f"{RED}[FAIL]{NC} {message}")
    FAILED_TESTS += 1
    TOTAL_TESTS += 1

def print_info(message):
    print(f"{BLUE}[INFO]{NC} {message}")

def cleanup(skip_message=False):
    if not skip_message:
        print_info("테스트 아티팩트 정리 중...")
    
    shutil.rmtree(TEST_DATA_DIR, ignore_errors=True)
    shutil.rmtree(TEST_OUTPUT_DIR, ignore_errors=True)
    shutil.rmtree(TEST_REPORT_DIR, ignore_errors=True)
    shutil.rmtree(os.path.join(SCRIPT_DIR, "data"), ignore_errors=True)
    shutil.rmtree(os.path.join(SCRIPT_DIR, "sqlite_mcp_test_workspace"), ignore_errors=True)
    
    for item in os.listdir(SCRIPT_DIR):
        if item.endswith(".db"):
            os.remove(os.path.join(SCRIPT_DIR, item))
    
    if os.path.exists("checklist_result.json"):
        os.remove("checklist_result.json")

    if not skip_message:
        print_info("정리 완료")

def setup_test_environment():
    print_info("테스트 환경 설정 중...")
    os.makedirs(TEST_DATA_DIR, exist_ok=True)
    os.makedirs(TEST_OUTPUT_DIR, exist_ok=True)
    os.makedirs(TEST_REPORT_DIR, exist_ok=True)

    with open(os.path.join(TEST_DATA_DIR, "test1.txt"), "w") as f:
        f.write("테스트 파일 1 내용")
    with open(os.path.join(TEST_DATA_DIR, "test2.txt"), "w") as f:
        f.write("테스트 파일 2 내용")
    with open(os.path.join(TEST_DATA_DIR, "test.json"), "w") as f:
        f.write('{"key": "value"}')
    with open(os.path.join(TEST_DATA_DIR, "test.md"), "w") as f:
        f.write("# 테스트 마크다운")
    
    print_info("테스트 환경 준비 완료")

def run_python_module(module_name):
    result = subprocess.run([sys.executable, "-m", module_name], capture_output=True, text=True, encoding="utf-8")
    if result.stdout:
        print(result.stdout.strip())
    return result

# 테스트 함수
def test_db_design():
    print_test("db_design.py 테스트 (4-6: 데이터베이스 설계)")
    result = run_python_module("Part1_Ch4.sqlite.db_design")
    if result.returncode == 0:
        db1 = os.path.join(SCRIPT_DIR, "data/tenant1.db")
        db2 = os.path.join(SCRIPT_DIR, "data/tenant2.db")
        if os.path.exists(db1) and os.path.exists(db2):
            print_pass("데이터베이스 설계 모듈이 올바르게 작동합니다.")
            
            conn = sqlite3.connect(db1)
            cursor = conn.cursor()
            
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='documents';")
            if cursor.fetchone():
                print_pass("데이터베이스 스키마가 올바르게 생성되었습니다.")
            else:
                print_fail("데이터베이스 스키마가 생성되지 않았습니다.")

            cursor.execute("SELECT name FROM sqlite_master WHERE type='index' AND name LIKE 'idx_documents%';")
            if cursor.fetchone():
                 print_pass("데이터베이스 인덱스가 올바르게 생성되었습니다.")
            else:
                 print_fail("데이터베이스 인덱스가 생성되지 않았습니다.")
            conn.close()
        else:
            print_fail("데이터베이스 파일이 생성되지 않았습니다.")
    else:
        print_fail(f"db_design.py 실행에 실패했습니다.\n{result.stderr}")

def test_crud_api():
    print_test("crud_api.py 테스트 (4-7: CRUD 연산)")
    result = run_python_module("Part1_Ch4.sqlite.crud_api")
    if result.returncode == 0:
        print_pass("CRUD API 모듈이 올바르게 작동합니다.")
        db_path = os.path.join(SCRIPT_DIR, "data/test_crud.db")
        if os.path.exists(db_path):
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM documents;")
            count = cursor.fetchone()[0]
            conn.close()
            if count > 0:
                print_pass(f"CRUD 연산을 통해 문서가 생성되었습니다 (개수: {count}).")
            else:
                print_fail("CRUD 연산으로 문서가 생성되지 않았습니다.")
        else:
            print_fail("CRUD 데이터베이스 파일이 생성되지 않았습니다.")
    else:
        print_fail(f"crud_api.py 실행에 실패했습니다.\n{result.stderr}")

def test_query_api():
    print_test("query_api.py 테스트 (4-8: 쿼리/페이지네이션/정렬)")
    result = run_python_module("Part1_Ch4.sqlite.query_api")
    if result.returncode == 0:
        print_pass("쿼리 API 모듈이 올바르게 작동합니다.")
        db_path = os.path.join(SCRIPT_DIR, "data/test_query.db")
        if os.path.exists(db_path):
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM documents;")
            count = cursor.fetchone()[0]
            conn.close()
            if count == 25:
                print_pass(f"쿼리 API가 정확한 수의 테스트 문서를 생성했습니다 ({count}개).")
            else:
                print_fail(f"문서 수가 올바르지 않습니다 (예상: 25, 실제: {count}).")
        else:
            print_fail("쿼리 데이터베이스 파일이 생성되지 않았습니다.")
    else:
        print_fail(f"query_api.py 실행에 실패했습니다.\n{result.stderr}")

def test_file_to_db_pipeline():
    print_test("file_to_db_pipeline.py 테스트 (4-9: 파일→DB 파이프라인)")
    result = run_python_module("Part1_Ch4.sqlite.file_to_db_pipeline")
    if result.returncode == 0:
        print_pass("파일→DB 파이프라인 모듈이 올바르게 작동합니다.")
        db_path = os.path.join(SCRIPT_DIR, "data/test_pipeline.db")
        if os.path.exists(db_path):
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM documents;")
            count = cursor.fetchone()[0]
            conn.close()
            if count > 0:
                print_pass(f"파이프라인이 파일들을 데이터베이스에 로드했습니다 (개수: {count}).")
            else:
                print_fail("파이프라인이 파일을 로드하지 않았습니다.")
        else:
            print_fail("파이프라인 데이터베이스가 생성되지 않았습니다.")
    else:
        print_fail(f"file_to_db_pipeline.py 실행에 실패했습니다.\n{result.stderr}")

def test_db_to_file_report():
    print_test("db_to_file_report.py 테스트 (4-10: DB→파일 보고서)")
    result = run_python_module("Part1_Ch4.sqlite.db_to_file_report")
    if result.returncode == 0:
        print_pass("DB→파일 보고서 모듈이 올바르게 작동합니다.")
    else:
        print_fail(f"db_to_file_report.py 실행에 실패했습니다.\n{result.stderr}")

def test_mcp_server_integration():
    print_test("test_mcp_server.py 테스트 (MCP 종단간 테스트)")
    try:
        import fastmcp
        print_info("fastmcp 라이브러리가 설치되어 있습니다.")
    except ImportError:
        print_fail("MCP 서버 통합 테스트 실패 (fastmcp 라이브러리가 설치되지 않았습니다. 'make up'을 실행하여 의존성을 설치하세요.)")
        return

    result = run_python_module("Part1_Ch4.sqlite.test_mcp_server")
    if result.returncode == 0:
        print_pass("MCP 서버 통합 테스트를 통과했습니다.")
    else:
        print_fail(f"MCP 서버 통합 테스트에 실패했습니다.\n{result.stderr}")

def test_imports():
    print_test("모듈 임포트 테스트")
    script = """
import sys
try:
    from Part1_Ch4.sqlite.db_design import create_database, DatabaseDesign, DatabaseConfig
    from Part1_Ch4.sqlite.crud_api import CRUDOperations
    from Part1_Ch4.sqlite.query_api import QueryOperations, QueryFilter, SortParams, PaginationParams
    from Part1_Ch4.sqlite.file_to_db_pipeline import FileToDBPipeline
    from Part1_Ch4.sqlite.db_to_file_report import DBToFileReport
    from Part1_Ch4.sqlite.checklist import SQLiteChecklist
    print("모든 임포트 성공")
    sys.exit(0)
except Exception as e:
    print(f"임포트 실패: {e}")
    sys.exit(1)
"""
    result = subprocess.run([sys.executable, "-c", script], capture_output=True, text=True)
    print(result.stdout)
    if result.returncode == 0:
        print_pass("모든 모듈 임포트에 성공했습니다.")
    else:
        print_fail(f"모듈 임포트에 실패했습니다.\n{result.stderr}")

def test_error_handling():
    print_test("오류 처리 테스트")
    result = run_python_module("Part1_Ch4.sqlite.test_error_handling")
    if result.returncode == 0:
        print_pass("오류 처리가 올바르게 작동합니다.")
    else:
        print_fail(f"오류 처리가 미흡합니다.\n{result.stderr}")

def test_multi_tenancy():
    print_test("멀티 테넌시 데이터 격리 테스트")
    result = run_python_module("Part1_Ch4.sqlite.test_multi_tenancy")
    if result.returncode == 0:
        print_pass("멀티 테넌시 데이터 격리가 올바르게 작동합니다.")
    else:
        print_fail(f"멀티 테넌시 데이터 격리에 실패했습니다.\n{result.stderr}")

def main():
    print_header("SQLite 모듈 종합 테스트 스위트 (Python)")
    cleanup()
    setup_test_environment()

    print_header("모듈 테스트")
    test_imports()
    test_db_design()
    test_crud_api()
    test_query_api()
    test_file_to_db_pipeline()
    test_db_to_file_report()

    print_header("통합 테스트")
    test_mcp_server_integration()

    print_header("특수 테스트")
    test_error_handling()
    test_multi_tenancy()

    # cleanup() # 주석 처리하여 결과 파일 확인 가능

    print_header("테스트 요약")
    print(f"총 테스트:  {BLUE}{TOTAL_TESTS}{NC}")
    print(f"성공:       {GREEN}{PASSED_TESTS}{NC}")
    print(f"실패:       {RED}{FAILED_TESTS}{NC}")

    if FAILED_TESTS == 0:
        print("")
        print(f"{GREEN}🎉 모든 테스트를 통과했습니다! 모든 파이썬 파일이 올바르게 구현되었습니다.{NC}")
        print("")
        sys.exit(0)
    else:
        print("")
        print(f"{RED}❌ 일부 테스트가 실패했습니다. 구현을 다시 확인해주세요.{NC}")
        print("")
        sys.exit(1)

if __name__ == "__main__":
    main()
