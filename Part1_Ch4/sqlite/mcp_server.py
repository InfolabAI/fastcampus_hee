"""
SQLite API MCP Server

SQLite 데이터베이스 기능을 MCP(Model Context Protocol) 도구로 제공하는 서버

제공 기능:
- 데이터베이스 생성 및 초기화
- CRUD 작업 (생성, 조회, 수정, 삭제)
- 쿼리/페이징/정렬
- 파일→SQLite 적재
- SQLite→파일 리포트 생성
- 데이터베이스 통계
"""

# asyncio: 비동기 프로그래밍을 위한 라이브러리입니다.
import asyncio
# pathlib.Path: 파일 시스템 경로를 객체 지향적으로 다루기 위한 클래스입니다.
import sys
from pathlib import Path
# typing: 타입 힌트를 지원하는 라이브러리입니다.
from typing import Optional, List, Dict, Any
# fastmcp.FastMCP: MCP 서버를 쉽게 생성하기 위한 클래스입니다.
from fastmcp import FastMCP

# 스크립트가 어디에서 실행되든 모듈을 찾을 수 있도록 프로젝트 루트를 경로에 추가합니다.
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# SQLite 관련 모듈들을 import 합니다.
# 이 모듈들은 데이터베이스 설계, CRUD, 쿼리, 파일 처리 등의 기능을 담당합니다.
from sqlite.db_design import create_database, DatabaseDesign, DatabaseConfig
from sqlite.crud_api import CRUDOperations
from sqlite.query_api import (
    QueryOperations,
    QueryFilter,
    PaginationParams,
    SortParams,
    SortOrder
)
from sqlite.file_to_db_pipeline import FileToDBPipeline
from sqlite.db_to_file_report import DBToFileReport

# "SQLiteAPIServer"라는 이름으로 FastMCP 서버 인스턴스를 생성합니다.
mcp = FastMCP("SQLiteAPIServer")

# 전역 변수로, 테넌트별 데이터베이스 인스턴스를 저장하는 딕셔너리입니다.
# key: 테넌트 ID (str), value: DatabaseDesign 인스턴스
_databases: Dict[str, DatabaseDesign] = {}


def _get_or_create_db(tenant_id: str, db_path: str = None) -> DatabaseDesign:
    """
    테넌트 ID에 해당하는 데이터베이스 인스턴스를 가져오거나, 없으면 새로 생성합니다.

    Args:
        tenant_id (str): 각 사용자를 구분하는 고유한 ID입니다.
        db_path (str, optional): 데이터베이스 파일의 경로입니다. 지정하지 않으면 기본 경로에 생성됩니다.

    Returns:
        DatabaseDesign: 해당 테넌트의 데이터베이스 인스턴스입니다.
    """
    # 만약 해당 tenant_id가 _databases 딕셔너리에 없다면,
    if tenant_id not in _databases:
        # db_path가 제공되면 해당 경로를 Path 객체로 만들고, 아니면 None으로 설정합니다.
        path = Path(db_path) if db_path else None
        # create_database 함수를 호출하여 새로운 데이터베이스를 생성하고,
        # _databases 딕셔너리에 저장합니다.
        _databases[tenant_id] = create_database(tenant_id, path)
    # _databases 딕셔너리에서 tenant_id에 해당하는 데이터베이스 인스턴스를 반환합니다.
    return _databases[tenant_id]


# ========================================
# 데이터베이스 관리 도구
# ========================================

@mcp.tool()
async def init_database(tenant_id: str, db_path: str = None) -> dict:
    """
    지정된 테넌트의 데이터베이스를 초기화하는 MCP 도구입니다. (4-6)

    Args:
        tenant_id (str): 테넌트 ID입니다.
        db_path (str, optional): 데이터베이스 파일 경로입니다.

    Returns:
        dict: 초기화 결과 (성공 여부, 테넌트 ID, DB 경로, 테이블 및 인덱스 수)를 담은 딕셔너리입니다.
    """
    # 현재 실행 중인 비동기 이벤트 루프를 가져옵니다.
    loop = asyncio.get_event_loop()

    def _init():
        """데이터베이스 초기화를 실제로 수행하는 내부 함수입니다."""
        # 데이터베이스 인스턴스를 가져오거나 생성합니다.
        db_design = _get_or_create_db(tenant_id, db_path)
        # 데이터베이스의 스키마 정보를 가져옵니다.
        schema_info = db_design.get_schema_info()
        # 초기화 결과를 딕셔너리 형태로 반환합니다.
        return {
            "status": "success",
            "tenant_id": tenant_id,
            "db_path": str(db_design.db_path),
            "tables": len(schema_info['tables']),
            "indexes": len(schema_info['indexes'])
        }

    # 동기 함수인 _init을 별도의 스레드에서 실행하여 비동기적으로 처리합니다.
    return await loop.run_in_executor(None, _init)


@mcp.tool()
async def get_schema_info(tenant_id: str) -> dict:
    """
    데이터베이스의 스키마 정보를 조회하는 MCP 도구입니다.

    Args:
        tenant_id (str): 테넌트 ID입니다.

    Returns:
        dict: 데이터베이스의 테이블, 인덱스 등 스키마 정보를 담은 딕셔너리입니다.
    """
    # 현재 실행 중인 비동기 이벤트 루프를 가져옵니다.
    loop = asyncio.get_event_loop()

    def _get_info():
        """스키마 정보 조회를 실제로 수행하는 내부 함수입니다."""
        # 데이터베이스 인스턴스를 가져옵니다.
        db_design = _get_or_create_db(tenant_id)
        # 스키마 정보를 반환합니다.
        return db_design.get_schema_info()

    # 동기 함수인 _get_info를 별도의 스레드에서 실행하여 비동기적으로 처리합니다.
    return await loop.run_in_executor(None, _get_info)


# ========================================
# CRUD 작업 도구 (4-7)
# ========================================

@mcp.tool()
async def create_document(
    tenant_id: str,
    filename: str,
    content: str,
    file_type: str = None,
    file_size: int = None,
    metadata: dict = None
) -> dict:
    """
    새로운 문서를 데이터베이스에 생성하는 MCP 도구입니다. (4-7: Create)

    Args:
        tenant_id (str): 테넌트 ID입니다.
        filename (str): 파일의 이름입니다.
        content (str): 파일의 내용입니다.
        file_type (str, optional): 파일의 종류 (e.g., 'text', 'image').
        file_size (int, optional): 파일의 크기 (bytes).
        metadata (dict, optional): 추가적인 메타데이터.

    Returns:
        dict: 생성 결과 (성공 여부, 문서 ID, 파일명)를 담은 딕셔너리입니다.
    """
    # 현재 실행 중인 비동기 이벤트 루프를 가져옵니다.
    loop = asyncio.get_event_loop()

    def _create():
        """문서 생성을 실제로 수행하는 내부 함수입니다."""
        # 데이터베이스 인스턴스를 가져옵니다.
        db_design = _get_or_create_db(tenant_id)
        # CRUD 작업을 위한 객체를 생성합니다.
        crud = CRUDOperations(db_design)
        # 문서를 생성하고 새로운 문서의 ID를 받습니다.
        doc_id = crud.create(filename, content, file_type, file_size, metadata)
        # 생성 결과를 딕셔너리 형태로 반환합니다.
        return {
            "status": "success",
            "document_id": doc_id,
            "filename": filename
        }

    # 동기 함수인 _create를 별도의 스레드에서 실행하여 비동기적으로 처리합니다.
    return await loop.run_in_executor(None, _create)


@mcp.tool()
async def read_document(tenant_id: str, document_id: int) -> dict:
    """
    특정 문서를 조회하는 MCP 도구입니다. (4-7: Read)

    Args:
        tenant_id (str): 테넌트 ID입니다.
        document_id (int): 조회할 문서의 ID입니다.

    Returns:
        dict: 조회 결과 (성공 여부, 문서 내용 또는 에러 메시지)를 담은 딕셔너리입니다.
    """
    # 현재 실행 중인 비동기 이벤트 루프를 가져옵니다.
    loop = asyncio.get_event_loop()

    def _read():
        """문서 조회를 실제로 수행하는 내부 함수입니다."""
        # 데이터베이스 인스턴스를 가져옵니다.
        db_design = _get_or_create_db(tenant_id)
        # CRUD 작업을 위한 객체를 생성합니다.
        crud = CRUDOperations(db_design)
        # 문서를 조회합니다.
        doc = crud.read(document_id)
        # 문서가 존재하면 성공 상태와 함께 문서 내용을 반환합니다.
        if doc:
            return {"status": "success", "document": doc}
        # 문서가 없으면 에러 상태와 메시지를 반환합니다.
        return {"status": "error", "message": "Document not found"}

    # 동기 함수인 _read를 별도의 스레드에서 실행하여 비동기적으로 처리합니다.
    return await loop.run_in_executor(None, _read)


@mcp.tool()
async def update_document(
    tenant_id: str,
    document_id: int,
    filename: str = None,
    content: str = None,
    file_type: str = None,
    file_size: int = None,
    metadata: dict = None
) -> dict:
    """
    특정 문서를 수정하는 MCP 도구입니다. (4-7: Update)

    Args:
        tenant_id (str): 테넌트 ID입니다.
        document_id (int): 수정할 문서의 ID입니다.
        filename (str, optional): 새로운 파일명.
        content (str, optional): 새로운 내용.
        file_type (str, optional): 새로운 파일 타입.
        file_size (int, optional): 새로운 파일 크기.
        metadata (dict, optional): 새로운 메타데이터.

    Returns:
        dict: 수정 결과 (성공 또는 에러 상태, 메시지)를 담은 딕셔너리입니다.
    """
    # 현재 실행 중인 비동기 이벤트 루프를 가져옵니다.
    loop = asyncio.get_event_loop()

    def _update():
        """문서 수정을 실제로 수행하는 내부 함수입니다."""
        # 데이터베이스 인스턴스를 가져옵니다.
        db_design = _get_or_create_db(tenant_id)
        # CRUD 작업을 위한 객체를 생성합니다.
        crud = CRUDOperations(db_design)
        # 문서를 수정하고 성공 여부를 받습니다.
        success = crud.update(document_id, filename, content, file_type, file_size, metadata)
        # 수정 결과에 따라 적절한 상태와 메시지를 반환합니다.
        return {
            "status": "success" if success else "error",
            "message": "Document updated" if success else "Update failed"
        }

    # 동기 함수인 _update를 별도의 스레드에서 실행하여 비동기적으로 처리합니다.
    return await loop.run_in_executor(None, _update)


@mcp.tool()
async def delete_document(tenant_id: str, document_id: int) -> dict:
    """
    특정 문서를 삭제하는 MCP 도구입니다. (4-7: Delete)

    Args:
        tenant_id (str): 테넌트 ID입니다.
        document_id (int): 삭제할 문서의 ID입니다.

    Returns:
        dict: 삭제 결과 (성공 또는 에러 상태, 메시지)를 담은 딕셔너리입니다.
    """
    # 현재 실행 중인 비동기 이벤트 루프를 가져옵니다.
    loop = asyncio.get_event_loop()

    def _delete():
        """문서 삭제를 실제로 수행하는 내부 함수입니다."""
        # 데이터베이스 인스턴스를 가져옵니다.
        db_design = _get_or_create_db(tenant_id)
        # CRUD 작업을 위한 객체를 생성합니다.
        crud = CRUDOperations(db_design)
        # 문서를 삭제하고 성공 여부를 받습니다.
        success = crud.delete(document_id)
        # 삭제 결과에 따라 적절한 상태와 메시지를 반환합니다.
        return {
            "status": "success" if success else "error",
            "message": "Document deleted" if success else "Delete failed"
        }

    # 동기 함수인 _delete를 별도의 스레드에서 실행하여 비동기적으로 처리합니다.
    return await loop.run_in_executor(None, _delete)


@mcp.tool()
async def list_documents(tenant_id: str) -> dict:
    """
    데이터베이스에 있는 모든 문서를 조회하는 MCP 도구입니다.

    Args:
        tenant_id (str): 테넌트 ID입니다.

    Returns:
        dict: 조회 결과 (성공 여부, 문서 개수, 문서 목록)를 담은 딕셔너리입니다.
    """
    # 현재 실행 중인 비동기 이벤트 루프를 가져옵니다.
    loop = asyncio.get_event_loop()

    def _list():
        """문서 목록 조회를 실제로 수행하는 내부 함수입니다."""
        # 데이터베이스 인스턴스를 가져옵니다.
        db_design = _get_or_create_db(tenant_id)
        # CRUD 작업을 위한 객체를 생성합니다.
        crud = CRUDOperations(db_design)
        # 모든 문서를 조회합니다.
        docs = crud.read_all()
        # 조회 결과를 딕셔너리 형태로 반환합니다.
        return {
            "status": "success",
            "count": len(docs),
            "documents": docs
        }

    # 동기 함수인 _list를 별도의 스레드에서 실행하여 비동기적으로 처리합니다.
    return await loop.run_in_executor(None, _list)


# ========================================
# 쿼리/페이징/정렬 도구 (4-8)
# ========================================

@mcp.tool()
async def query_documents(
    tenant_id: str,
    filename_filter: str = None,
    file_type_filter: str = None,
    content_filter: str = None,
    page: int = 1,
    page_size: int = 10,
    sort_field: str = "id",
    sort_order: str = "ASC"
) -> dict:
    """
    다양한 조건으로 문서를 쿼리하는 MCP 도구입니다. (4-8: 필터링, 페이징, 정렬)

    Args:
        tenant_id (str): 테넌트 ID입니다.
        filename_filter (str, optional): 파일명에 대한 필터 조건.
        file_type_filter (str, optional): 파일 타입에 대한 필터 조건.
        content_filter (str, optional): 내용에 대한 필터 조건.
        page (int, optional): 조회할 페이지 번호 (기본값 1).
        page_size (int, optional): 한 페이지에 보여줄 문서 수 (기본값 10).
        sort_field (str, optional): 정렬의 기준이 될 필드 (기본값 'id').
        sort_order (str, optional): 정렬 순서 ('ASC' 또는 'DESC', 기본값 'ASC').

    Returns:
        dict: 쿼리 결과 (페이지 정보, 전체 개수, 항목 목록 등)를 담은 딕셔너리입니다.
    """
    # 현재 실행 중인 비동기 이벤트 루프를 가져옵니다.
    loop = asyncio.get_event_loop()

    def _query():
        """문서 쿼리를 실제로 수행하는 내부 함수입니다."""
        # 데이터베이스 인스턴스를 가져옵니다.
        db_design = _get_or_create_db(tenant_id)
        # 쿼리 작업을 위한 객체를 생성합니다.
        query_ops = QueryOperations(db_design)

        # 전달된 필터 값들을 사용하여 QueryFilter 객체를 생성합니다.
        filter_params = QueryFilter(
            filename=filename_filter,
            file_type=file_type_filter,
            content=content_filter
        )

        # 정렬 필드와 순서를 사용하여 SortParams 객체를 생성합니다.
        sort_params = SortParams(
            field=sort_field,
            order=SortOrder.ASC if sort_order.upper() == "ASC" else SortOrder.DESC
        )

        # 페이지 번호와 페이지 크기를 사용하여 PaginationParams 객체를 생성합니다.
        pagination = PaginationParams(page=page, page_size=page_size)

        # 쿼리를 실행하고 결과를 받습니다.
        result = query_ops.query(filter_params, sort_params, pagination)

        # 쿼리 결과를 API 응답 형식에 맞게 딕셔너리로 구성하여 반환합니다.
        return {
            "status": "success",
            "page": result.page,
            "page_size": result.page_size,
            "total_count": result.total_count,
            "total_pages": result.total_pages,
            "has_next": result.has_next,
            "has_previous": result.has_previous,
            "items": result.items
        }

    # 동기 함수인 _query를 별도의 스레드에서 실행하여 비동기적으로 처리합니다.
    return await loop.run_in_executor(None, _query)


@mcp.tool()
async def search_documents(tenant_id: str, keyword: str, search_fields: List[str] = None) -> dict:
    """
    키워드를 사용하여 문서를 검색하는 MCP 도구입니다. (4-8)

    Args:
        tenant_id (str): 테넌트 ID입니다.
        keyword (str): 검색할 키워드입니다.
        search_fields (List[str], optional): 검색을 수행할 필드 목록입니다. (e.g., ['filename', 'content'])

    Returns:
        dict: 검색 결과 (성공 여부, 키워드, 결과 수, 결과 목록)를 담은 딕셔너리입니다.
    """
    # 현재 실행 중인 비동기 이벤트 루프를 가져옵니다.
    loop = asyncio.get_event_loop()

    def _search():
        """문서 검색을 실제로 수행하는 내부 함수입니다."""
        # 데이터베이스 인스턴스를 가져옵니다.
        db_design = _get_or_create_db(tenant_id)
        # 쿼리 작업을 위한 객체를 생성합니다.
        query_ops = QueryOperations(db_design)
        # 키워드와 검색 필드를 사용하여 검색을 수행합니다.
        results = query_ops.search(keyword, search_fields)
        # 검색 결과를 딕셔너리 형태로 반환합니다.
        return {
            "status": "success",
            "keyword": keyword,
            "count": len(results),
            "results": results
        }

    # 동기 함수인 _search를 별도의 스레드에서 실행하여 비동기적으로 처리합니다.
    return await loop.run_in_executor(None, _search)


@mcp.tool()
async def get_statistics(tenant_id: str) -> dict:
    """
    데이터베이스에 대한 통계 정보를 조회하는 MCP 도구입니다. (4-8)

    Args:
        tenant_id (str): 테넌트 ID입니다.

    Returns:
        dict: 통계 정보 (문서 수, 파일 타입별 분포 등)를 담은 딕셔너리입니다.
    """
    # 현재 실행 중인 비동기 이벤트 루프를 가져옵니다.
    loop = asyncio.get_event_loop()

    def _stats():
        """통계 조회를 실제로 수행하는 내부 함수입니다."""
        # 데이터베이스 인스턴스를 가져옵니다.
        db_design = _get_or_create_db(tenant_id)
        # 쿼리 작업을 위한 객체를 생성합니다.
        query_ops = QueryOperations(db_design)
        # 통계 정보를 가져옵니다.
        stats = query_ops.get_statistics()
        # 성공 상태와 함께 통계 정보를 반환합니다.
        return {"status": "success", **stats}

    # 동기 함수인 _stats를 별도의 스레드에서 실행하여 비동기적으로 처리합니다.
    return await loop.run_in_executor(None, _stats)


# ========================================
# 파일→SQLite 파이프라인 도구 (4-9)
# ========================================

@mcp.tool()
async def load_file_to_db(tenant_id: str, file_path: str, metadata: dict = None) -> dict:
    """
    단일 파일을 데이터베이스에 적재하는 MCP 도구입니다. (4-9)

    Args:
        tenant_id (str): 테넌트 ID입니다.
        file_path (str): 데이터베이스에 적재할 파일의 경로입니다.
        metadata (dict, optional): 파일과 함께 저장할 추가적인 메타데이터입니다.

    Returns:
        dict: 적재 결과 (성공 여부, 생성된 문서 ID, 파일 경로)를 담은 딕셔너리입니다.
    """
    # 현재 실행 중인 비동기 이벤트 루프를 가져옵니다.
    loop = asyncio.get_event_loop()

    def _load():
        """파일 적재를 실제로 수행하는 내부 함수입니다."""
        # 데이터베이스 인스턴스를 가져옵니다.
        db_design = _get_or_create_db(tenant_id)
        # 파일-DB 파이프라인 객체를 생성합니다.
        pipeline = FileToDBPipeline(db_design)
        # 파일을 데이터베이스에 로드하고 생성된 문서 ID를 받습니다.
        doc_id = pipeline.load_file(Path(file_path), metadata)
        # 적재 결과를 딕셔너리 형태로 반환합니다.
        return {
            "status": "success",
            "document_id": doc_id,
            "file_path": file_path
        }

    # 동기 함수인 _load를 별도의 스레드에서 실행하여 비동기적으로 처리합니다.
    return await loop.run_in_executor(None, _load)


@mcp.tool()
async def load_directory_to_db(
    tenant_id: str,
    directory_path: str,
    pattern: str = "*",
    recursive: bool = False,
    skip_existing: bool = True
) -> dict:
    """
    지정된 디렉토리의 파일들을 데이터베이스에 적재하는 MCP 도구입니다. (4-9)

    Args:
        tenant_id (str): 테넌트 ID입니다.
        directory_path (str): 파일들을 가져올 디렉토리의 경로입니다.
        pattern (str, optional): 찾을 파일의 패턴 (e.g., '*.txt'). 기본값은 모든 파일.
        recursive (bool, optional): 하위 디렉토리까지 재귀적으로 탐색할지 여부. 기본값은 False.
        skip_existing (bool, optional): 이미 데이터베이스에 있는 파일은 건너뛸지 여부. 기본값은 True.

    Returns:
        dict: 적재 결과에 대한 통계 (성공 여부, 총 파일 수, 성공/실패/건너뛴 파일 수)를 담은 딕셔너리입니다.
    """
    # 현재 실행 중인 비동기 이벤트 루프를 가져옵니다.
    loop = asyncio.get_event_loop()

    def _load():
        """디렉토리 적재를 실제로 수행하는 내부 함수입니다."""
        # 데이터베이스 인스턴스를 가져옵니다.
        db_design = _get_or_create_db(tenant_id)
        # 파일-DB 파이프라인 객체를 생성합니다.
        pipeline = FileToDBPipeline(db_design)
        # 디렉토리의 파일들을 데이터베이스에 로드하고 통계 정보를 받습니다.
        stats = pipeline.load_directory(
            Path(directory_path),
            pattern,
            recursive,
            skip_existing
        )
        # 성공 상태와 함께 통계 정보를 반환합니다.
        return {"status": "success", **stats}

    # 동기 함수인 _load를 별도의 스레드에서 실행하여 비동기적으로 처리합니다.
    return await loop.run_in_executor(None, _load)


# ========================================
# SQLite→파일 리포트 도구 (4-10)
# ========================================

@mcp.tool()
async def export_to_json(
    tenant_id: str,
    output_path: str,
    file_type_filter: str = None,
    pretty: bool = True
) -> dict:
    """
    데이터베이스의 내용을 JSON 파일로 내보내는 MCP 도구입니다. (4-10)

    Args:
        tenant_id (str): 테넌트 ID입니다.
        output_path (str): 결과 JSON 파일을 저장할 경로입니다.
        file_type_filter (str, optional): 특정 파일 타입의 문서만 내보내기 위한 필터.
        pretty (bool, optional): JSON 출력을 예쁘게 포맷할지 여부. 기본값은 True.

    Returns:
        dict: 내보내기 결과 (성공 여부, 출력 경로, 내보낸 항목 수)를 담은 딕셔너리입니다.
    """
    # 현재 실행 중인 비동기 이벤트 루프를 가져옵니다.
    loop = asyncio.get_event_loop()

    def _export():
        """JSON 내보내기를 실제로 수행하는 내부 함수입니다."""
        # 데이터베이스 인스턴스를 가져옵니다.
        db_design = _get_or_create_db(tenant_id)
        # DB-파일 리포트 객체를 생성합니다.
        report = DBToFileReport(db_design)
        # 파일 타입 필터가 있으면 QueryFilter 객체를 생성합니다.
        filter_params = QueryFilter(file_type=file_type_filter) if file_type_filter else None
        # JSON으로 내보내고 결과를 받습니다.
        result = report.export_to_json(Path(output_path), filter_params, pretty)
        # 성공 상태와 함께 결과를 반환합니다.
        return {"status": "success", **result}

    # 동기 함수인 _export를 별도의 스레드에서 실행하여 비동기적으로 처리합니다.
    return await loop.run_in_executor(None, _export)


@mcp.tool()
async def export_to_csv(
    tenant_id: str,
    output_path: str,
    file_type_filter: str = None,
    include_metadata: bool = False
) -> dict:
    """
    데이터베이스의 내용을 CSV 파일로 내보내는 MCP 도구입니다. (4-10)

    Args:
        tenant_id (str): 테넌트 ID입니다.
        output_path (str): 결과 CSV 파일을 저장할 경로입니다.
        file_type_filter (str, optional): 특정 파일 타입의 문서만 내보내기 위한 필터.
        include_metadata (bool, optional): CSV에 메타데이터를 포함할지 여부. 기본값은 False.

    Returns:
        dict: 내보내기 결과 (성공 여부, 출력 경로, 내보낸 행 수)를 담은 딕셔너리입니다.
    """
    # 현재 실행 중인 비동기 이벤트 루프를 가져옵니다.
    loop = asyncio.get_event_loop()

    def _export():
        """CSV 내보내기를 실제로 수행하는 내부 함수입니다."""
        # 데이터베이스 인스턴스를 가져옵니다.
        db_design = _get_or_create_db(tenant_id)
        # DB-파일 리포트 객체를 생성합니다.
        report = DBToFileReport(db_design)
        # 파일 타입 필터가 있으면 QueryFilter 객체를 생성합니다.
        filter_params = QueryFilter(file_type=file_type_filter) if file_type_filter else None
        # CSV로 내보내고 결과를 받습니다.
        result = report.export_to_csv(Path(output_path), filter_params, include_metadata)
        # 성공 상태와 함께 결과를 반환합니다.
        return {"status": "success", **result}

    # 동기 함수인 _export를 별도의 스레드에서 실행하여 비동기적으로 처리합니다.
    return await loop.run_in_executor(None, _export)


@mcp.tool()
async def export_to_markdown(
    tenant_id: str,
    output_path: str,
    file_type_filter: str = None,
    include_statistics: bool = True
) -> dict:
    """
    데이터베이스의 내용을 Markdown 파일로 내보내는 MCP 도구입니다. (4-10)

    Args:
        tenant_id (str): 테넌트 ID입니다.
        output_path (str): 결과 Markdown 파일을 저장할 경로입니다.
        file_type_filter (str, optional): 특정 파일 타입의 문서만 내보내기 위한 필터.
        include_statistics (bool, optional): 리포트에 통계 정보를 포함할지 여부. 기본값은 True.

    Returns:
        dict: 내보내기 결과 (성공 여부, 출력 경로, 내보낸 항목 수)를 담은 딕셔너리입니다.
    """
    # 현재 실행 중인 비동기 이벤트 루프를 가져옵니다.
    loop = asyncio.get_event_loop()

    def _export():
        """Markdown 내보내기를 실제로 수행하는 내부 함수입니다."""
        # 데이터베이스 인스턴스를 가져옵니다.
        db_design = _get_or_create_db(tenant_id)
        # DB-파일 리포트 객체를 생성합니다.
        report = DBToFileReport(db_design)
        # 파일 타입 필터가 있으면 QueryFilter 객체를 생성합니다.
        filter_params = QueryFilter(file_type=file_type_filter) if file_type_filter else None
        # Markdown으로 내보내고 결과를 받습니다.
        result = report.export_to_markdown(Path(output_path), filter_params, include_statistics)
        # 성공 상태와 함께 결과를 반환합니다.
        return {"status": "success", **result}

    # 동기 함수인 _export를 별도의 스레드에서 실행하여 비동기적으로 처리합니다.
    return await loop.run_in_executor(None, _export)


# 이 스크립트가 직접 실행될 때,
if __name__ == "__main__":
    # MCP 서버를 실행합니다.
    mcp.run()
