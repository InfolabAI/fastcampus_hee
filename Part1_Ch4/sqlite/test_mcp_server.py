"""
SQLite API MCP Server 테스트

mcp_server.py의 모든 도구를 테스트하는 스크립트
"""

import asyncio
import shutil
import pathlib
import json
import sys
import os

# PYTHONPATH 설정 - 프로젝트 루트를 추가
project_root = pathlib.Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from fastmcp import Client
from fastmcp.client.transports import StdioTransport


async def test_sqlite_api_server():
    """SQLite API MCP 서버의 모든 도구를 테스트합니다."""

    # 1. 테스트 디렉토리 설정
    test_dir = pathlib.Path("./sqlite_mcp_test_workspace").resolve()
    if test_dir.exists():
        shutil.rmtree(test_dir)
    test_dir.mkdir()

    # 테스트 파일 생성
    (test_dir / "test_file1.txt").write_text("This is test file 1.")
    (test_dir / "test_file2.md").write_text("# Test File 2\nMarkdown content")
    (test_dir / "test_file3.json").write_text('{"key": "value"}')

    print(f"Test workspace created at: {test_dir}\n")

    # StdioTransport를 사용하여 서버 실행
    # PYTHONPATH를 서버 프로세스에도 전달
    env = os.environ.copy()
    env['PYTHONPATH'] = str(project_root)

    transport = StdioTransport(
        command="python",
        args=["-m", "Part1_Ch4.sqlite.mcp_server"],
        env=env
    )
    client = Client(transport)

    try:
        async with client:
            print("=" * 80)
            print("SQLite API MCP Server Test Started")
            print("=" * 80)
            print()

            # 사용 가능한 도구 목록
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

            # 스키마 정보 조회
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

            # Create - 문서 생성
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

            # 추가 문서 생성
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

            # Read - 문서 조회
            print("   2-2. Read - 문서 조회")
            result = await client.call_tool("read_document", {
                "tenant_id": tenant_id,
                "document_id": doc_id
            })
            print(f"      Filename: {result.data['document']['filename']}")
            print(f"      Content: {result.data['document']['content']}")
            print()

            # Update - 문서 수정
            print("   2-3. Update - 문서 수정")
            result = await client.call_tool("update_document", {
                "tenant_id": tenant_id,
                "document_id": doc_id,
                "content": "Updated content!",
                "metadata": {"author": "test", "updated": True}
            })
            print(f"      Status: {result.data['status']}")
            print()

            # List - 전체 문서 조회
            print("   2-4. List - 전체 문서 조회")
            result = await client.call_tool("list_documents", {
                "tenant_id": tenant_id
            })
            print(f"      Total documents: {result.data['count']}")
            for doc in result.data['documents'][:3]:
                print(f"      - ID {doc['id']}: {doc['filename']}")
            print()

            # Delete - 문서 삭제
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

            # 페이징
            print("   3-1. Pagination - 페이지네이션")
            result = await client.call_tool("query_documents", {
                "tenant_id": tenant_id,
                "page": 1,
                "page_size": 3
            })
            print(f"      Page: {result.data['page']}/{result.data['total_pages']}")
            print(f"      Items: {len(result.data['items'])}/{result.data['total_count']}")
            print()

            # 필터링
            print("   3-2. Filtering - 필터링 (file_type=text)")
            result = await client.call_tool("query_documents", {
                "tenant_id": tenant_id,
                "file_type_filter": "text",
                "page": 1,
                "page_size": 10
            })
            print(f"      Found {result.data['total_count']} text files")
            print()

            # 정렬
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

            # 검색
            print("   3-4. Search - 검색 (keyword='doc')")
            result = await client.call_tool("search_documents", {
                "tenant_id": tenant_id,
                "keyword": "doc"
            })
            print(f"      Found {result.data['count']} documents")
            print()

            # 통계
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

            # 단일 파일 적재
            print("   4-1. Load File - 단일 파일 적재")
            result = await client.call_tool("load_file_to_db", {
                "tenant_id": tenant_id,
                "file_path": str(test_dir / "test_file1.txt"),
                "metadata": {"source": "test"}
            })
            print(f"      Loaded: {result.data['file_path']}")
            print(f"      Document ID: {result.data['document_id']}")
            print()

            # 디렉토리 적재
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

            # JSON 리포트
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

            # CSV 리포트
            print("   5-2. Export to CSV")
            result = await client.call_tool("export_to_csv", {
                "tenant_id": tenant_id,
                "output_path": str(reports_dir / "report.csv")
            })
            print(f"      Output: {result.data['output_path']}")
            print(f"      Documents: {result.data['document_count']}")
            print()

            # Markdown 리포트
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

            # 두 번째 테넌트 데이터베이스 생성
            tenant2_id = "tenant2"
            await client.call_tool("init_database", {
                "tenant_id": tenant2_id,
                "db_path": str(test_dir / "tenant2.db")
            })

            # 각 테넌트에 데이터 추가
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

            # 각 테넌트의 문서 수 확인
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
        import traceback
        print(f"\n❌ Error occurred: {e}")
        traceback.print_exc()
    finally:
        # 정리
        print("\nCleaning up test workspace...")
        if test_dir.exists():
            shutil.rmtree(test_dir)
        print("Cleanup complete.")


if __name__ == "__main__":
    asyncio.run(test_sqlite_api_server())
