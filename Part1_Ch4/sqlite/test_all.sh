#!/bin/bash
################################################################################
# SQLite Module Comprehensive Test Script
#
# This script tests all Python files in the Part1_Ch4/sqlite folder to verify
# they are implemented correctly.
#
# Usage: ./test_all.sh
################################################################################

# Don't use set -e as we want to continue testing even if some tests fail
# set -e  # Exit on any error

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test counters
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

# Project root (assuming script is in Part1_Ch4/sqlite/)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Setup Python path
export PYTHONPATH="${PROJECT_ROOT}:${PYTHONPATH}"

# Test data directories
TEST_DATA_DIR="${SCRIPT_DIR}/test_data"
TEST_OUTPUT_DIR="${SCRIPT_DIR}/test_output"

################################################################################
# Helper Functions
################################################################################

print_header() {
    echo ""
    echo -e "${BLUE}================================================================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}================================================================================${NC}"
    echo ""
}

print_test() {
    echo -e "${YELLOW}[TEST]${NC} $1"
}

print_pass() {
    echo -e "${GREEN}[PASS]${NC} $1"
    ((PASSED_TESTS++))
    ((TOTAL_TESTS++))
}

print_fail() {
    echo -e "${RED}[FAIL]${NC} $1"
    ((FAILED_TESTS++))
    ((TOTAL_TESTS++))
}

print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

cleanup() {
    if [ "${1:-}" != "skip_message" ]; then
        print_info "Cleaning up test artifacts..."
    fi
    rm -rf "${TEST_DATA_DIR}" "${TEST_OUTPUT_DIR}"
    rm -rf data/ *.db
    rm -f checklist_result.json
    rm -rf sqlite_mcp_test_workspace/
    if [ "${1:-}" != "skip_message" ]; then
        print_info "Cleanup complete"
    fi
}

setup_test_environment() {
    print_info "Setting up test environment..."
    mkdir -p "${TEST_DATA_DIR}"
    mkdir -p "${TEST_OUTPUT_DIR}"

    # Create test files
    echo "Test file 1 content" > "${TEST_DATA_DIR}/test1.txt"
    echo "Test file 2 content" > "${TEST_DATA_DIR}/test2.txt"
    echo '{"key": "value"}' > "${TEST_DATA_DIR}/test.json"
    echo "# Test Markdown" > "${TEST_DATA_DIR}/test.md"

    print_info "Test environment ready"
}

################################################################################
# Test Functions
################################################################################

test_db_design() {
    print_test "Testing db_design.py (4-6: Database Design)"

    if python -m Part1_Ch4.sqlite.db_design > /dev/null 2>&1; then
        # Verify database files were created
        if [ -f "data/tenant1.db" ] && [ -f "data/tenant2.db" ]; then
            print_pass "Database design module works correctly"

            # Verify schema
            if sqlite3 data/tenant1.db ".schema documents" 2>/dev/null | grep -q "CREATE TABLE"; then
                print_pass "Database schema created correctly"
            else
                print_fail "Database schema not created"
            fi

            # Verify indexes
            if sqlite3 data/tenant1.db ".indexes" 2>/dev/null | grep -q "idx_documents"; then
                print_pass "Database indexes created correctly"
            else
                print_fail "Database indexes not created"
            fi
        else
            print_fail "Database files not created"
        fi
    else
        print_fail "db_design.py execution failed"
    fi
    return 0
}

test_crud_api() {
    print_test "Testing crud_api.py (4-7: CRUD Operations)"

    if python -m Part1_Ch4.sqlite.crud_api > /dev/null 2>&1; then
        print_pass "CRUD API module works correctly"

        # Verify database has data
        COUNT=$(sqlite3 data/test_crud.db "SELECT COUNT(*) FROM documents;" 2>/dev/null || echo "0")
        if [ "$COUNT" -gt 0 ]; then
            print_pass "CRUD operations created documents (count: $COUNT)"
        else
            print_fail "No documents created by CRUD operations"
        fi
    else
        print_fail "crud_api.py execution failed"
    fi
    return 0
}

test_query_api() {
    print_test "Testing query_api.py (4-8: Query/Pagination/Sorting)"

    if python -m Part1_Ch4.sqlite.query_api > /dev/null 2>&1; then
        print_pass "Query API module works correctly"

        # Verify test database has data
        COUNT=$(sqlite3 data/test_query.db "SELECT COUNT(*) FROM documents;" 2>/dev/null || echo "0")
        if [ "$COUNT" -eq 25 ]; then
            print_pass "Query API created correct number of test documents (25)"
        else
            print_fail "Incorrect number of documents (expected 25, got $COUNT)"
        fi
    else
        print_fail "query_api.py execution failed"
    fi
    return 0
}

test_file_to_db_pipeline() {
    print_test "Testing file_to_db_pipeline.py (4-9: File→DB Pipeline)"

    if python -m Part1_Ch4.sqlite.file_to_db_pipeline > /dev/null 2>&1; then
        print_pass "File to DB pipeline module works correctly"

        # Verify pipeline database
        if [ -f "data/test_pipeline.db" ]; then
            COUNT=$(sqlite3 data/test_pipeline.db "SELECT COUNT(*) FROM documents;" 2>/dev/null || echo "0")
            if [ "$COUNT" -gt 0 ]; then
                print_pass "Pipeline loaded files into database (count: $COUNT)"
            else
                print_fail "Pipeline did not load any files"
            fi
        else
            print_fail "Pipeline database not created"
        fi
    else
        print_fail "file_to_db_pipeline.py execution failed"
    fi
    return 0
}

test_db_to_file_report() {
    print_test "Testing db_to_file_report.py (4-10: DB→File Report)"

    if python -m Part1_Ch4.sqlite.db_to_file_report > /dev/null 2>&1; then
        print_pass "DB to file report module works correctly"

        # Note: This test creates reports in a temp directory that gets cleaned up
        # Just verify the module runs without errors
    else
        print_fail "db_to_file_report.py execution failed"
    fi
    return 0
}

test_checklist() {
    print_test "Testing checklist.py (4-11: Comprehensive Checklist)"

    OUTPUT=$(python -m Part1_Ch4.sqlite.checklist 2>&1)
    EXIT_CODE=$?

    if [ $EXIT_CODE -eq 0 ]; then
        print_pass "Checklist module executed successfully"

        # Verify checklist result file
        if [ -f "checklist_result.json" ]; then
            print_pass "Checklist result file created"

            # Check success rate
            if command -v jq &> /dev/null; then
                SUCCESS_RATE=$(jq -r '.success_rate' checklist_result.json)
                # Use awk instead of bc for floating point comparison
                if awk "BEGIN {exit !($SUCCESS_RATE >= 90)}"; then
                    print_pass "Checklist success rate: ${SUCCESS_RATE}%"
                else
                    print_fail "Checklist success rate too low: ${SUCCESS_RATE}%"
                fi

                PASSED=$(jq -r '.passed' checklist_result.json)
                TOTAL=$(jq -r '.total' checklist_result.json)
                print_info "Checklist results: $PASSED/$TOTAL tests passed"
            else
                print_info "jq not installed, skipping JSON validation"
            fi
        else
            print_fail "Checklist result file not created"
        fi
    else
        print_fail "checklist.py execution failed"
    fi
    return 0
}

test_mcp_server() {
    print_test "Testing mcp_server.py (MCP Server Integration)"

    # First check if fastmcp is installed
    if ! python -c "import fastmcp" 2>/dev/null; then
        print_fail "MCP server failed to start (fastmcp not installed - run 'make up' to install dependencies)"
        return 0
    fi

    # Test if the server can start (we'll use a timeout)
    timeout 3 python -m Part1_Ch4.sqlite.mcp_server > /dev/null 2>&1 &
    SERVER_PID=$!
    sleep 1

    if ps -p $SERVER_PID > /dev/null 2>&1; then
        print_pass "MCP server starts without errors"
        kill $SERVER_PID 2>/dev/null || true
    else
        print_fail "MCP server failed to start"
    fi
    return 0
}

test_mcp_server_integration() {
    print_test "Testing test_mcp_server.py (MCP End-to-End Test)"

    # First check if fastmcp is installed
    if ! python -c "import fastmcp" 2>/dev/null; then
        print_fail "MCP server integration test failed (fastmcp not installed - run 'make up' to install dependencies)"
        return 0
    fi

    # Run the full MCP server test
    if python -m Part1_Ch4.sqlite.test_mcp_server > /dev/null 2>&1; then
        print_pass "MCP server integration test passed"
    else
        print_fail "MCP server integration test failed"
    fi
    return 0
}

test_imports() {
    print_test "Testing module imports"

    OUTPUT=$(python << 'EOF' 2>&1
import sys
try:
    from Part1_Ch4.sqlite.db_design import create_database, DatabaseDesign, DatabaseConfig
    from Part1_Ch4.sqlite.crud_api import CRUDOperations
    from Part1_Ch4.sqlite.query_api import QueryOperations, QueryFilter, SortParams, PaginationParams
    from Part1_Ch4.sqlite.file_to_db_pipeline import FileToDBPipeline
    from Part1_Ch4.sqlite.db_to_file_report import DBToFileReport
    from Part1_Ch4.sqlite.checklist import SQLiteChecklist
    print("All imports successful")
    sys.exit(0)
except Exception as e:
    print(f"Import failed: {e}")
    sys.exit(1)
EOF
)
    EXIT_CODE=$?
    echo "$OUTPUT"

    if [ $EXIT_CODE -eq 0 ]; then
        print_pass "All module imports successful"
        return 0
    else
        print_fail "Module import failed"
        return 1
    fi
}

test_error_handling() {
    print_test "Testing error handling"

    OUTPUT=$(python << 'EOF' 2>&1
import sys
from pathlib import Path
from Part1_Ch4.sqlite.db_design import create_database
from Part1_Ch4.sqlite.crud_api import CRUDOperations
from Part1_Ch4.sqlite.file_to_db_pipeline import FileToDBPipeline
from Part1_Ch4.sqlite.query_api import SortParams

db = create_database("test_errors")
crud = CRUDOperations(db)
pipeline = FileToDBPipeline(db)

errors_caught = 0

# Test 1: Non-existent document returns None
if crud.read(999) is None:
    errors_caught += 1

# Test 2: Delete non-existent document returns False
if not crud.delete(999):
    errors_caught += 1

# Test 3: Invalid file path raises FileNotFoundError
try:
    pipeline.load_file(Path("nonexistent_file.txt"))
except FileNotFoundError:
    errors_caught += 1

# Test 4: Invalid sort field raises ValueError
try:
    SortParams(field="invalid_field")
except ValueError:
    errors_caught += 1

if errors_caught == 4:
    print("All error handling tests passed")
    sys.exit(0)
else:
    print(f"Only {errors_caught}/4 error handling tests passed")
    sys.exit(1)
EOF
)
    EXIT_CODE=$?

    if [ $EXIT_CODE -eq 0 ]; then
        print_pass "Error handling works correctly"
    else
        print_fail "Error handling incomplete"
    fi
    return 0
}

test_multi_tenancy() {
    print_test "Testing multi-tenancy data isolation"

    OUTPUT=$(python << 'EOF' 2>&1
import sys
from Part1_Ch4.sqlite.db_design import create_database
from Part1_Ch4.sqlite.crud_api import CRUDOperations

# Create two tenant databases
db1 = create_database("tenant_test_1")
db2 = create_database("tenant_test_2")

crud1 = CRUDOperations(db1)
crud2 = CRUDOperations(db2)

# Add data to each tenant
crud1.create(filename="tenant1.txt", content="Tenant 1 data")
crud2.create(filename="tenant2.txt", content="Tenant 2 data")

# Verify isolation
doc1 = crud1.read(1)
doc2 = crud2.read(1)

if (doc1 and doc1['content'] == "Tenant 1 data" and
    doc2 and doc2['content'] == "Tenant 2 data" and
    crud1.count() == 1 and crud2.count() == 1):
    print("Multi-tenancy isolation verified")
    sys.exit(0)
else:
    print("Multi-tenancy isolation failed")
    sys.exit(1)
EOF
)
    EXIT_CODE=$?

    if [ $EXIT_CODE -eq 0 ]; then
        print_pass "Multi-tenancy data isolation works correctly"
    else
        print_fail "Multi-tenancy data isolation failed"
    fi
    return 0
}

################################################################################
# Main Test Execution
################################################################################

main() {
    print_header "SQLite Module Comprehensive Test Suite"

    # Setup
    setup_test_environment

    # Run all tests
    print_header "Module Tests"
    test_imports
    test_db_design
    test_crud_api
    test_query_api
    test_file_to_db_pipeline
    test_db_to_file_report
    test_checklist

    print_header "Integration Tests"
    test_mcp_server
    test_mcp_server_integration

    print_header "Special Tests"
    test_error_handling
    test_multi_tenancy

    # Cleanup
    cleanup

    # Print summary
    print_header "Test Summary"
    echo -e "Total Tests:  ${BLUE}${TOTAL_TESTS}${NC}"
    echo -e "Passed:       ${GREEN}${PASSED_TESTS}${NC}"
    echo -e "Failed:       ${RED}${FAILED_TESTS}${NC}"

    if [ $FAILED_TESTS -eq 0 ]; then
        echo ""
        echo -e "${GREEN}🎉 All tests passed! All Python files are implemented correctly.${NC}"
        echo ""
        exit 0
    else
        echo ""
        echo -e "${RED}❌ Some tests failed. Please review the implementation.${NC}"
        echo ""
        exit 1
    fi
}

# Run main function
main
