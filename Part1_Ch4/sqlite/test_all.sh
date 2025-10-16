#!/bin/bash
################################################################################
# SQLite 모듈 종합 테스트 스크립트
#
# 이 스크립트는 Part1_Ch4/sqlite 폴더의 모든 파이썬 파일이 올바르게 구현되었는지
# 확인하기 위해 테스트를 실행합니다. 각 스크립트는 강의의 특정 섹션에 해당하며,
# 이 테스트를 통해 모든 기능이 예상대로 작동하는지 검증할 수 있습니다.
#
# 사용법: ./test_all.sh
# 스크립트를 실행하면 전체 테스트가 진행되고, 각 단계별 성공/실패 여부와
# 최종 요약 결과를 출력합니다.
################################################################################

# `set -e`를 사용하지 않습니다. 특정 테스트가 실패하더라도 전체 테스트를 계속 진행하기 위함입니다.
# 만약 하나의 테스트라도 실패하면 즉시 스크립트를 중단하고 싶다면 아래 줄의 주석을 해제하세요.
# set -e  # 오류 발생 시 즉시 종료

# 출력에 사용할 색상 코드 정의
# 터미널 출력에 색을 입혀 가독성을 높입니다.
RED='\033[0;31m'    # 실패 (빨간색)
GREEN='\033[0;32m'  # 성공 (녹색)
YELLOW='\033[1;33m' # 테스트 진행 (노란색)
BLUE='\033[0;34m'   # 정보 (파란색)
NC='\033[0m'        # 색상 없음 (기본값으로 복원)

# 테스트 결과 카운터
# 전체 테스트 수, 성공한 테스트 수, 실패한 테스트 수를 추적합니다.
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

# 프로젝트 루트 디렉토리 설정
# 이 스크립트가 있는 위치를 기준으로 프로젝트의 최상위 디렉토리를 찾습니다.
# 이렇게 하면 어디서 스크립트를 실행하든 일관된 경로를 유지할 수 있습니다.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# 파이썬 경로(PYTHONPATH) 설정
# 파이썬이 `Part1_Ch4.sqlite` 같은 모듈을 찾을 수 있도록 프로젝트 루트를 경로에 추가합니다.
export PYTHONPATH="${PROJECT_ROOT}:${PYTHONPATH}"

# 테스트에 필요한 데이터 및 출력 디렉토리 경로 설정
TEST_DATA_DIR="${SCRIPT_DIR}/test_data"
TEST_OUTPUT_DIR="${SCRIPT_DIR}/test_output"
TEST_REPORT_DIR="${SCRIPT_DIR}/test_report"

################################################################################
# 헬퍼 함수 (Helper Functions)
# 스크립트 전반에서 반복적으로 사용되는 출력 관련 기능들을 함수로 정의합니다.
################################################################################

# 헤더 출력 함수
# 테스트 섹션 구분을 위해 파란색 구분선을 출력합니다.
print_header() {
    echo ""
    echo -e "${BLUE}================================================================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}================================================================================${NC}"
    echo ""
}

# 테스트 시작 메시지 출력 함수
print_test() {
    echo -e "${YELLOW}[TEST]${NC} $1"
}

# 테스트 통과 메시지 출력 함수
print_pass() {
    echo -e "${GREEN}[PASS]${NC} $1"
    ((PASSED_TESTS++)) # 성공 카운터 증가
    ((TOTAL_TESTS++))  # 전체 카운터 증가
}

# 테스트 실패 메시지 출력 함수
print_fail() {
    echo -e "${RED}[FAIL]${NC} $1"
    ((FAILED_TESTS++)) # 실패 카운터 증가
    ((TOTAL_TESTS++))  # 전체 카운터 증가
}

# 정보 메시지 출력 함수
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

# 테스트 환경 정리(cleanup) 함수
# 테스트 실행 후 생성된 파일이나 디렉토리를 삭제하여 다음 테스트에 영향을 주지 않도록 합니다.
cleanup() {
    # "skip_message" 인자가 없으면 정리 시작 메시지를 출력합니다.
    if [ "${1:-}" != "skip_message" ]; then
        print_info "테스트 아티팩트 정리 중..."
    fi
    # 테스트 데이터, 출력, 보고서 디렉토리 및 생성된 DB 파일들을 삭제합니다.
    rm -rf "${TEST_DATA_DIR}" "${TEST_OUTPUT_DIR}" "${TEST_REPORT_DIR}"
    rm -rf data/ *.db
    rm -f checklist_result.json
    rm -rf sqlite_mcp_test_workspace/
    # "skip_message" 인자가 없으면 정리 완료 메시지를 출력합니다.
    if [ "${1:-}" != "skip_message" ]; then
        print_info "정리 완료"
    fi
}

# 테스트 환경 설정(setup) 함수
# 테스트에 필요한 디렉토리와 파일들을 미리 생성합니다.
setup_test_environment() {
    print_info "테스트 환경 설정 중..."
    mkdir -p "${TEST_DATA_DIR}"
    mkdir -p "${TEST_OUTPUT_DIR}"
    mkdir -p "${TEST_REPORT_DIR}"

    # file_to_db_pipeline.py 테스트에 사용될 테스트 파일들을 생성합니다.
    echo "테스트 파일 1 내용" > "${TEST_DATA_DIR}/test1.txt"
    echo "테스트 파일 2 내용" > "${TEST_DATA_DIR}/test2.txt"
    echo '{"key": "value"}' > "${TEST_DATA_DIR}/test.json"
    echo "# 테스트 마크다운" > "${TEST_DATA_DIR}/test.md"

    print_info "테스트 환경 준비 완료"
}

################################################################################
# 테스트 함수들 (Test Functions)
# 각 파이썬 모듈의 기능을 검증하는 실제 테스트 로직입니다.
################################################################################

# db_design.py 테스트 함수
test_db_design() {
    print_test "db_design.py 테스트 (4-6: 데이터베이스 설계)"

    # 파이썬 모듈을 실행합니다.
    if python -m Part1_Ch4.sqlite.db_design; then
        # 데이터베이스 파일이 정상적으로 생성되었는지 확인합니다.
        if [ -f "data/tenant1.db" ] && [ -f "data/tenant2.db" ]; then
            print_pass "데이터베이스 설계 모듈이 올바르게 작동합니다."

            # tenant1.db 파일에 'documents' 테이블 스키마가 생성되었는지 확인합니다.
            if sqlite3 data/tenant1.db ".schema documents" 2>/dev/null | grep -q "CREATE TABLE"; then
                print_pass "데이터베이스 스키마가 올바르게 생성되었습니다."
            else
                print_fail "데이터베이스 스키마가 생성되지 않았습니다."
            fi

            # tenant1.db 파일에 인덱스가 생성되었는지 확인합니다.
            if sqlite3 data/tenant1.db ".indexes" 2>/dev/null | grep -q "idx_documents"; then
                print_pass "데이터베이스 인덱스가 올바르게 생성되었습니다."
            else
                print_fail "데이터베이스 인덱스가 생성되지 않았습니다."
            fi
        else
            print_fail "데이터베이스 파일이 생성되지 않았습니다."
        fi
    else
        print_fail "db_design.py 실행에 실패했습니다."
    fi
    return 0
}

# crud_api.py 테스트 함수
test_crud_api() {
    print_test "crud_api.py 테스트 (4-7: CRUD 연산)"

    if python -m Part1_Ch4.sqlite.crud_api; then
        print_pass "CRUD API 모듈이 올바르게 작동합니다."

        # CRUD 연산 후 데이터베이스에 데이터가 실제로 삽입되었는지 확인합니다.
        # sqlite3 명령어로 'documents' 테이블의 행 수를 셉니다.
        COUNT=$(sqlite3 data/test_crud.db "SELECT COUNT(*) FROM documents;" 2>/dev/null || echo "0")
        if [ "$COUNT" -gt 0 ]; then
            print_pass "CRUD 연산을 통해 문서가 생성되었습니다 (개수: $COUNT)."
        else
            print_fail "CRUD 연산으로 문서가 생성되지 않았습니다."
        fi
    else
        print_fail "crud_api.py 실행에 실패했습니다."
    fi
    return 0
}

# query_api.py 테스트 함수
test_query_api() {
    print_test "query_api.py 테스트 (4-8: 쿼리/페이지네이션/정렬)"

    if python -m Part1_Ch4.sqlite.query_api; then
        print_pass "쿼리 API 모듈이 올바르게 작동합니다."

        # 테스트 데이터가 정확히 25개 생성되었는지 확인합니다.
        COUNT=$(sqlite3 data/test_query.db "SELECT COUNT(*) FROM documents;" 2>/dev/null || echo "0")
        if [ "$COUNT" -eq 25 ]; then
            print_pass "쿼리 API가 정확한 수의 테스트 문서를 생성했습니다 (25개)."
        else
            print_fail "문서 수가 올바르지 않습니다 (예상: 25, 실제: $COUNT)."
        fi
    else
        print_fail "query_api.py 실행에 실패했습니다."
    fi
    return 0
}

# file_to_db_pipeline.py 테스트 함수
test_file_to_db_pipeline() {
    print_test "file_to_db_pipeline.py 테스트 (4-9: 파일→DB 파이프라인)"

    if python -m Part1_Ch4.sqlite.file_to_db_pipeline; then
        print_pass "파일→DB 파이프라인 모듈이 올바르게 작동합니다."

        # 파이프라인 실행 후, 파일 내용이 데이터베이스에 저장되었는지 확인합니다.
        if [ -f "data/test_pipeline.db" ]; then
            COUNT=$(sqlite3 data/test_pipeline.db "SELECT COUNT(*) FROM documents;" 2>/dev/null || echo "0")
            if [ "$COUNT" -gt 0 ]; then
                print_pass "파이프라인이 파일들을 데이터베이스에 로드했습니다 (개수: $COUNT)."
            else
                print_fail "파이프라인이 파일을 로드하지 않았습니다."
            fi
        else
            print_fail "파이프라인 데이터베이스가 생성되지 않았습니다."
        fi
    else
        print_fail "file_to_db_pipeline.py 실행에 실패했습니다."
    fi
    return 0
}

# db_to_file_report.py 테스트 함수
test_db_to_file_report() {
    print_test "db_to_file_report.py 테스트 (4-10: DB→파일 보고서)"

    if python -m Part1_Ch4.sqlite.db_to_file_report; then
        print_pass "DB→파일 보고서 모듈이 올바르게 작동합니다."

        # 이 테스트는 임시 디렉토리에 보고서를 생성하고, 이 디렉토리는 cleanup 시 삭제됩니다.
        # 따라서, 스크립트가 오류 없이 실행되는 것만으로도 기본적인 성공으로 간주합니다.
        # (파일 존재 여부나 내용은 test_mcp_server.py에서 더 상세히 검증됩니다.)
    else
        print_fail "db_to_file_report.py 실행에 실패했습니다."
    fi
    return 0
}

# test_mcp_server.py 통합 테스트 함수
test_mcp_server_integration() {
    print_test "test_mcp_server.py 테스트 (MCP 종단간 테스트)"

    # MCP 서버 테스트는 fastmcp 라이브러리가 필요하므로, 설치되어 있는지 먼저 확인합니다.
    if ! python -c "import fastmcp" 2>/dev/null; then
        print_fail "MCP 서버 통합 테스트 실패 (fastmcp 라이브러리가 설치되지 않았습니다. 'make up'을 실행하여 의존성을 설치하세요.)"
        return 0
    fi

    # 전체 MCP 서버 테스트를 실행합니다.
    # 이 테스트는 서버를 구동하고 API 요청을 보내는 등 실제 사용 사례와 유사한 시나리오를 검증합니다.
    if python -m Part1_Ch4.sqlite.test_mcp_server; then
        print_pass "MCP 서버 통합 테스트를 통과했습니다."
    else
        print_fail "MCP 서버 통합 테스트에 실패했습니다."
    fi
    return 0
}

# 모듈 임포트 테스트 함수
# 모든 주요 클래스와 함수들이 문제없이 임포트되는지 확인합니다.
# 임포트 오류는 종종 순환 참조나 경로 문제로 인해 발생하므로 중요한 검증 단계입니다.
test_imports() {
    print_test "모듈 임포트 테스트"

    # 파이썬 스크립트를 here-document(<<)를 이용해 직접 실행합니다.
    OUTPUT=$(python << 'EOF' 2>&1
import sys
try:
    # 각 모듈의 주요 구성 요소들을 임포트해 봅니다.
    from Part1_Ch4.sqlite.db_design import create_database, DatabaseDesign, DatabaseConfig
    from Part1_Ch4.sqlite.crud_api import CRUDOperations
    from Part1_Ch4.sqlite.query_api import QueryOperations, QueryFilter, SortParams, PaginationParams
    from Part1_Ch4.sqlite.file_to_db_pipeline import FileToDBPipeline
    from Part1_Ch4.sqlite.db_to_file_report import DBToFileReport
    from Part1_Ch4.sqlite.checklist import SQLiteChecklist
    print("모든 임포트 성공")
    sys.exit(0) # 성공 시 종료 코드 0
except Exception as e:
    print(f"임포트 실패: {e}")
    sys.exit(1) # 실패 시 종료 코드 1
EOF
)
    EXIT_CODE=$? # 파이썬 스크립트의 종료 코드를 저장합니다.
    echo "$OUTPUT" # 파이썬 스크립트의 출력(성공 또는 오류 메시지)을 보여줍니다.

    if [ $EXIT_CODE -eq 0 ]; then
        print_pass "모든 모듈 임포트에 성공했습니다."
        return 0
    else
        print_fail "모듈 임포트에 실패했습니다."
        return 1
    fi
}

# 오류 처리(Error Handling) 테스트 함수
test_error_handling() {
    print_test "오류 처리 테스트"

    # 예외적인 상황(예: 존재하지 않는 파일 접근)에서 프로그램이 의도대로 오류를 처리하는지 검증합니다.
    if python -m Part1_Ch4.sqlite.test_error_handling; then
        print_pass "오류 처리가 올바르게 작동합니다."
    else
        print_fail "오류 처리가 미흡합니다."
    fi
    return 0
}

# 멀티 테넌시(Multi-tenancy) 테스트 함수
test_multi_tenancy() {
    print_test "멀티 테넌시 데이터 격리 테스트"

    # 각 테넌트의 데이터가 서로 격리되어 다른 테넌트에 영향을 주지 않는지 검증합니다.
    if python -m Part1_Ch4.sqlite.test_multi_tenancy; then
        print_pass "멀티 테넌시 데이터 격리가 올바르게 작동합니다."
    else
        print_fail "멀티 테넌시 데이터 격리에 실패했습니다."
    fi
    return 0
}

################################################################################
# 메인 테스트 실행 로직 (Main Test Execution)
################################################################################

main() {
    print_header "SQLite 모듈 종합 테스트 스위트"
    # 이전 테스트 실행으로 남은 아티팩트들을 정리합니다.
    cleanup

    # 테스트 실행에 필요한 환경을 설정합니다.
    setup_test_environment

    # 개별 모듈 테스트를 순서대로 실행합니다.
    print_header "모듈 테스트"
    test_imports
    test_db_design
    test_crud_api
    test_query_api
    test_file_to_db_pipeline
    test_db_to_file_report

    # 여러 모듈이 함께 작동하는 통합 테스트를 실행합니다.
    print_header "통합 테스트"
    test_mcp_server_integration

    # 특수 목적의 테스트(오류 처리, 멀티 테넌시)를 실행합니다.
    print_header "특수 테스트"
    test_error_handling
    test_multi_tenancy

    # 테스트 완료 후 생성된 파일들을 검토하고 싶을 경우 아래 cleanup 줄을 주석 처리하세요.
    # cleanup

    # 최종 테스트 결과 요약 출력
    print_header "테스트 요약"
    echo -e "총 테스트:  ${BLUE}${TOTAL_TESTS}${NC}"
    echo -e "성공:       ${GREEN}${PASSED_TESTS}${NC}"
    echo -e "실패:       ${RED}${FAILED_TESTS}${NC}"

    # 실패한 테스트가 없으면 성공 메시지와 함께 종료 코드 0을 반환합니다.
    if [ $FAILED_TESTS -eq 0 ]; then
        echo ""
        echo -e "${GREEN}🎉 모든 테스트를 통과했습니다! 모든 파이썬 파일이 올바르게 구현되었습니다.${NC}"
        echo ""
        exit 0
    # 실패한 테스트가 있으면 실패 메시지와 함께 종료 코드 1을 반환합니다.
    # 종료 코드 1은 CI/CD 파이프라인에서 빌드 실패로 간주됩니다.
    else
        echo ""
        echo -e "${RED}❌ 일부 테스트가 실패했습니다. 구현을 다시 확인해주세요.${NC}"
        echo ""
        exit 1
    fi
}

# main 함수를 호출하여 전체 테스트를 시작합니다.
main
