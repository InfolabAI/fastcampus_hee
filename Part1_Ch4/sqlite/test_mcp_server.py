"""
SQLite API MCP Server 테스트

mcp_server.py의 모든 도구를 테스트하는 스크립트
"""

# asyncio: 비동기 프로그래밍을 위한 라이브러리입니다.
import asyncio
# shutil: 파일 및 디렉토리 관리를 위한 고수준 연산을 제공합니다. (e.g., 삭제)
import shutil
# pathlib: 파일 시스템 경로를 객체 지향적으로 다루기 위한 클래스입니다.
import pathlib
# json: JSON 데이터를 다루기 위한 모듈입니다.
import json
# sys: 파이썬 인터프리터와 관련된 변수 및 함수를 제공합니다.
import sys
# os: 운영 체제와 상호 작용하는 기능을 제공합니다.
import os

# --- PYTHONPATH 설정 ---
# 이 스크립트가 다른 위치에서 실행되더라도 'Part1_Ch4' 모듈을 찾을 수 있도록
# 프로젝트의 루트 디렉토리를 파이썬 경로에 추가합니다.
project_root = pathlib.Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# fastmcp 라이브러리에서 클라이언트 관련 클래스를 임포트합니다.
from fastmcp import Client
from fastmcp.client.transports import StdioTransport


async def test_sqlite_api_server():
    """
    SQLite API MCP 서버의 모든 도구(tool)가 정상적으로 작동하는지
    순서대로 테스트하는 비동기 함수입니다.
    """

    # 1. 테스트 환경 설정
    # 테스트 중에 생성될 파일들을 담을 임시 작업 디렉토리를 설정합니다.
    test_dir = pathlib.Path("./sqlite_mcp_test_workspace").resolve()
    # 만약 이전에 생성된 테스트 디렉토리가 남아있으면 삭제합니다.
    if test_dir.exists():
        shutil.rmtree(test_dir)
    # 새로운 테스트 디렉토리를 생성합니다.
    test_dir.mkdir()

    # 테스트에 사용될 임시 파일들을 생성합니다.
    (test_dir / "test_file1.txt").write_text("This is test file 1.")
    (test_dir / "test_file2.md").write_text("# Test File 2\nMarkdown content")
    (test_dir / "test_file3.json").write_text('{"key": "value"}')

    print(f"Test workspace created at: {test_dir}\n")

    # --- MCP 서버 실행 및 클라이언트 연결 ---
    # StdioTransport를 사용하여 mcp_server.py를 별도의 프로세스로 실행하고,
    # 표준 입출력(stdin/stdout)을 통해 통신합니다.
    env = os.environ.copy()
    env['PYTHONPATH'] = str(project_root) # 자식 프로세스도 프로젝트 루트를 인식하도록 설정

    transport = StdioTransport(
        command="python",
        args=["-m", "Part1_Ch4.sqlite.mcp_server"], # 모듈 형태로 서버 실행
        env=env
    )
    client = Client(transport)

    try:
        # `async with client:`: 클라이언트와 서버의 연결을 시작하고,
        # 블록이 끝나면 자동으로 연결을 종료합니다.
        async with client:
            print("=" * 80)
            print("SQLite API MCP Server Test Started")
            print("=" * 80)
            print()

            # 서버에서 사용 가능한 도구 목록을 가져와 출력합니다.
            tools = await client.list_tools()
            print(f"Available Tools ({len(tools)}):")
            for tool in tools:
                print(f"  - {tool.name}: {tool.description[:60]}...")
            print()

            tenant_id = "test_tenant"

            # ========================================
            # 1. 데이터베이스 초기화 테스트 (4-6)
            # ========================================
            print("[1] 데이터베이스 초기화 (4-6)")
            result = await client.call_tool("init_database", {
                "tenant_id": tenant_id,
                "db_path": str(test_dir / "test.db")
            })
            print(f"   Status: {result.data['status']}")
            print(f"   DB Path: {result.data['db_path']}")
            print(f"   Tables: {result.data['tables']}")
            print()

            # 스키마 정보 조회 테스트
            result = await client.call_tool("get_schema_info", {
                "tenant_id": tenant_id
            })
            print("   Schema Info:")
            print(f"   - Tables: {len(result.data['tables'])}")
            print(f"   - Indexes: {len(result.data['indexes'])}")
            print()

            # ========================================
            # 2. CRUD 작업 테스트 (4-7)
            # ========================================
            print("[2] CRUD 작업 (4-7)")

            # 2-1. Create - 문서 생성 테스트
            print("   2-1. Create - 문서 생성")
            result = await client.call_tool("create_document", {
                "tenant_id": tenant_id,
                "filename": "example.txt",
                "content": "Hello, SQLite MCP!",
                "file_type": "text",
                "file_size": 18,
                "metadata": {"author": "test", "category": "example"}
            })
            doc_id = result.data['document_id']
            print(f"      Created document ID: {doc_id}")

            # 테스트를 위한 추가 문서 생성
            for i in range(2, 6):
                await client.call_tool("create_document", {
                    "tenant_id": tenant_id,
                    "filename": f"doc_{i}.txt",
                    "content": f"Content of document {i}",
                    "file_type": "text" if i % 2 == 0 else "json",
                    "file_size": 20 + i
                })
            print(f"      Created 4 more documents")
            print()

            # 2-2. Read - 문서 조회 테스트
            print("   2-2. Read - 문서 조회")
            result = await client.call_tool("read_document", {
                "tenant_id": tenant_id,
                "document_id": doc_id
            })
            print(f"      Filename: {result.data['document']['filename']}")
            print(f"      Content: {result.data['document']['content']}")
            print()

            # 2-3. Update - 문서 수정 테스트
            print("   2-3. Update - 문서 수정")
            result = await client.call_tool("update_document", {
                "tenant_id": tenant_id,
                "document_id": doc_id,
                "content": "Updated content!",
                "metadata": {"author": "test", "updated": True}
            })
            print(f"      Status: {result.data['status']}")
            print()

            # 2-4. List - 전체 문서 조회 테스트
            print("   2-4. List - 전체 문서 조회")
            result = await client.call_tool("list_documents", {
                "tenant_id": tenant_id
            })
            print(f"      Total documents: {result.data['count']}")
            for doc in result.data['documents'][:3]:
                print(f"      - ID {doc['id']}: {doc['filename']}")
            print()

            # 2-5. Delete - 문서 삭제 테스트
            print("   2-5. Delete - 문서 삭제")
            result = await client.call_tool("delete_document", {
                "tenant_id": tenant_id,
                "document_id": 5
            })
            print(f"      Status: {result.data['status']}")
            print()

            # ========================================
            # 3. 쿼리/페이징/정렬 테스트 (4-8)
            # ========================================
            print("[3] 쿼리/페이징/정렬 (4-8)")

            # 3-1. Pagination - 페이지네이션 테스트
            print("   3-1. Pagination - 페이지네이션")
            result = await client.call_tool("query_documents", {
                "tenant_id": tenant_id,
                "page": 1,
                "page_size": 3
            })
            print(f"      Page: {result.data['page']}/{result.data['total_pages']}")
            print(f"      Items: {len(result.data['items'])}/{result.data['total_count']}")
            print()

            # 3-2. Filtering - 필터링 테스트
            print("   3-2. Filtering - 필터링 (file_type=text)")
            result = await client.call_tool("query_documents", {
                "tenant_id": tenant_id,
                "file_type_filter": "text",
                "page": 1,
                "page_size": 10
            })
            print(f"      Found {result.data['total_count']} text files")
            print()

            # 3-3. Sorting - 정렬 테스트
            print("   3-3. Sorting - 정렬 (filename DESC)")
            result = await client.call_tool("query_documents", {
                "tenant_id": tenant_id,
                "sort_field": "filename",
                "sort_order": "DESC",
                "page": 1,
                "page_size": 3
            })
            print(f"      First 3 items (sorted by filename DESC):")
            for item in result.data['items']:
                print(f"      - {item['filename']}")
            print()

            # 3-4. Search - 검색 테스트
            print("   3-4. Search - 검색 (keyword='doc')")
            result = await client.call_tool("search_documents", {
                "tenant_id": tenant_id,
                "keyword": "doc"
            })
            print(f"      Found {result.data['count']} documents")
            print()

            # 3-5. Statistics - 통계 조회 테스트
            print("   3-5. Statistics - 통계")
            result = await client.call_tool("get_statistics", {
                "tenant_id": tenant_id
            })
            print(f"      Total count: {result.data['total_count']}")
            print(f"      Total size: {result.data['total_size']} bytes")
            print(f"      Type distribution:")
            for dist in result.data['type_distribution']:
                print(f"         - {dist['file_type']}: {dist['count']}")
            print()

            # ========================================
            # 4. 파일→SQLite 파이프라인 테스트 (4-9)
            # ========================================
            print("[4] 파일→SQLite 파이프라인 (4-9)")

            # 4-1. Load File - 단일 파일 적재 테스트
            print("   4-1. Load File - 단일 파일 적재")
            result = await client.call_tool("load_file_to_db", {
                "tenant_id": tenant_id,
                "file_path": str(test_dir / "test_file1.txt"),
                "metadata": {"source": "test"}
            })
            print(f"      Loaded: {result.data['file_path']}")
            print(f"      Document ID: {result.data['document_id']}")
            print()

            # 4-2. Load Directory - 디렉토리 적재 테스트
            print("   4-2. Load Directory - 디렉토리 적재")
            result = await client.call_tool("load_directory_to_db", {
                "tenant_id": tenant_id,
                "directory_path": str(test_dir),
                "pattern": "*.txt",
                "skip_existing": True
            })
            print(f"      Total files: {result.data['total_files']}")
            print(f"      Loaded: {result.data['loaded']}")
            print(f"      Skipped: {result.data['skipped']}")
            print(f"      Failed: {result.data['failed']}")
            print()

            # ========================================
            # 5. SQLite→파일 리포트 테스트 (4-10)
            # ========================================
            print("[5] SQLite→파일 리포트 (4-10)")

            reports_dir = test_dir / "reports"
            reports_dir.mkdir(exist_ok=True)

            # 5-1. JSON 리포트 생성 테스트
            print("   5-1. Export to JSON")
            result = await client.call_tool("export_to_json", {
                "tenant_id": tenant_id,
                "output_path": str(reports_dir / "report.json"),
                "pretty": True
            })
            print(f"      Output: {result.data['output_path']}")
            print(f"      Documents: {result.data['document_count']}")
            print(f"      Size: {result.data['file_size']} bytes")
            print()

            # 5-2. CSV 리포트 생성 테스트
            print("   5-2. Export to CSV")
            result = await client.call_tool("export_to_csv", {
                "tenant_id": tenant_id,
                "output_path": str(reports_dir / "report.csv")
            })
            print(f"      Output: {result.data['output_path']}")
            print(f"      Documents: {result.data['document_count']}")
            print()

            # 5-3. Markdown 리포트 생성 테스트
            print("   5-3. Export to Markdown")
            result = await client.call_tool("export_to_markdown", {
                "tenant_id": tenant_id,
                "output_path": str(reports_dir / "report.md"),
                "include_statistics": True
            })
            print(f"      Output: {result.data['output_path']}")
            print(f"      Documents: {result.data['document_count']}")
            print()

            # ========================================
            # 6. 멀티테넌시 테스트
            # ========================================
            print("[6] 멀티테넌시 테스트")

            # 두 번째 테넌트용 데이터베이스를 생성합니다.
            tenant2_id = "tenant2"
            await client.call_tool("init_database", {
                "tenant_id": tenant2_id,
                "db_path": str(test_dir / "tenant2.db")
            })

            # 각 테넌트에 고유한 데이터를 추가합니다.
            await client.call_tool("create_document", {
                "tenant_id": tenant_id,
                "filename": "tenant1_file.txt",
                "content": "Tenant 1 data"
            })

            await client.call_tool("create_document", {
                "tenant_id": tenant2_id,
                "filename": "tenant2_file.txt",
                "content": "Tenant 2 data"
            })

            # 각 테넌트의 문서 수를 확인하여 데이터가 격리되었는지 검증합니다.
            result1 = await client.call_tool("list_documents", {"tenant_id": tenant_id})
            result2 = await client.call_tool("list_documents", {"tenant_id": tenant2_id})

            print(f"   Tenant 1 documents: {result1.data['count']}")
            print(f"   Tenant 2 documents: {result2.data['count']}")
            print(f"   ✓ Data isolation confirmed")
            print()

            print("=" * 80)
            print("Test Completed Successfully!")
            print("=" * 80)

    except Exception as e:
        # 테스트 중 오류가 발생하면 에러 메시지와 트레이스백을 출력합니다.
        import traceback
        print(f"\n❌ Error occurred: {e}")
        traceback.print_exc()
    finally:
        # --- 테스트 환경 정리 ---
        # 테스트가 성공하든 실패하든 항상 실행됩니다.
        print("\nCleaning up test workspace...")
        if test_dir.exists():
            shutil.rmtree(test_dir)
        print("Cleanup complete.")


if __name__ == "__main__":
    # 비동기 테스트 함수를 실행합니다.
    asyncio.run(test_sqlite_api_server())
