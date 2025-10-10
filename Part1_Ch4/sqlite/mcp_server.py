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

import asyncio
from pathlib import Path
from typing import Optional, List, Dict, Any
from fastmcp import FastMCP

# SQLite 모듈 import
from .db_design import create_database, DatabaseDesign, DatabaseConfig
from .crud_api import CRUDOperations
from .query_api import (
    QueryOperations,
    QueryFilter,
    PaginationParams,
    SortParams,
    SortOrder
)
from .file_to_db_pipeline import FileToDBPipeline
from .db_to_file_report import DBToFileReport

# FastMCP 서버 인스턴스 생성
mcp = FastMCP("SQLiteAPIServer")

# 전역 데이터베이스 인스턴스 저장소
_databases: Dict[str, DatabaseDesign] = {}


def _get_or_create_db(tenant_id: str, db_path: str = None) -> DatabaseDesign:
    """
    데이터베이스 인스턴스 가져오기 또는 생성

    Args:
        tenant_id: 테넌트 ID
        db_path: 데이터베이스 경로 (선택)

    Returns:
        DatabaseDesign: 데이터베이스 인스턴스
    """
    if tenant_id not in _databases:
        path = Path(db_path) if db_path else None
        _databases[tenant_id] = create_database(tenant_id, path)
    return _databases[tenant_id]


# ========================================
# 데이터베이스 관리 도구
# ========================================

@mcp.tool()
async def init_database(tenant_id: str, db_path: str = None) -> dict:
    """
    데이터베이스 초기화 (4-6)

    Args:
        tenant_id: 테넌트 ID
        db_path: 데이터베이스 파일 경로 (선택)

    Returns:
        dict: 초기화 결과
    """
    loop = asyncio.get_event_loop()

    def _init():
        db_design = _get_or_create_db(tenant_id, db_path)
        schema_info = db_design.get_schema_info()
        return {
            "status": "success",
            "tenant_id": tenant_id,
            "db_path": str(db_design.db_path),
            "tables": len(schema_info['tables']),
            "indexes": len(schema_info['indexes'])
        }

    return await loop.run_in_executor(None, _init)


@mcp.tool()
async def get_schema_info(tenant_id: str) -> dict:
    """
    데이터베이스 스키마 정보 조회

    Args:
        tenant_id: 테넌트 ID

    Returns:
        dict: 스키마 정보
    """
    loop = asyncio.get_event_loop()

    def _get_info():
        db_design = _get_or_create_db(tenant_id)
        return db_design.get_schema_info()

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
    새 문서 생성 (4-7: Create)

    Args:
        tenant_id: 테넌트 ID
        filename: 파일명
        content: 내용
        file_type: 파일 타입
        file_size: 파일 크기
        metadata: 메타데이터

    Returns:
        dict: 생성 결과
    """
    loop = asyncio.get_event_loop()

    def _create():
        db_design = _get_or_create_db(tenant_id)
        crud = CRUDOperations(db_design)
        doc_id = crud.create(filename, content, file_type, file_size, metadata)
        return {
            "status": "success",
            "document_id": doc_id,
            "filename": filename
        }

    return await loop.run_in_executor(None, _create)


@mcp.tool()
async def read_document(tenant_id: str, document_id: int) -> dict:
    """
    문서 조회 (4-7: Read)

    Args:
        tenant_id: 테넌트 ID
        document_id: 문서 ID

    Returns:
        dict: 문서 내용
    """
    loop = asyncio.get_event_loop()

    def _read():
        db_design = _get_or_create_db(tenant_id)
        crud = CRUDOperations(db_design)
        doc = crud.read(document_id)
        if doc:
            return {"status": "success", "document": doc}
        return {"status": "error", "message": "Document not found"}

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
    문서 수정 (4-7: Update)

    Args:
        tenant_id: 테넌트 ID
        document_id: 문서 ID
        filename: 파일명 (선택)
        content: 내용 (선택)
        file_type: 파일 타입 (선택)
        file_size: 파일 크기 (선택)
        metadata: 메타데이터 (선택)

    Returns:
        dict: 수정 결과
    """
    loop = asyncio.get_event_loop()

    def _update():
        db_design = _get_or_create_db(tenant_id)
        crud = CRUDOperations(db_design)
        success = crud.update(document_id, filename, content, file_type, file_size, metadata)
        return {
            "status": "success" if success else "error",
            "message": "Document updated" if success else "Update failed"
        }

    return await loop.run_in_executor(None, _update)


@mcp.tool()
async def delete_document(tenant_id: str, document_id: int) -> dict:
    """
    문서 삭제 (4-7: Delete)

    Args:
        tenant_id: 테넌트 ID
        document_id: 문서 ID

    Returns:
        dict: 삭제 결과
    """
    loop = asyncio.get_event_loop()

    def _delete():
        db_design = _get_or_create_db(tenant_id)
        crud = CRUDOperations(db_design)
        success = crud.delete(document_id)
        return {
            "status": "success" if success else "error",
            "message": "Document deleted" if success else "Delete failed"
        }

    return await loop.run_in_executor(None, _delete)


@mcp.tool()
async def list_documents(tenant_id: str) -> dict:
    """
    전체 문서 조회

    Args:
        tenant_id: 테넌트 ID

    Returns:
        dict: 문서 목록
    """
    loop = asyncio.get_event_loop()

    def _list():
        db_design = _get_or_create_db(tenant_id)
        crud = CRUDOperations(db_design)
        docs = crud.read_all()
        return {
            "status": "success",
            "count": len(docs),
            "documents": docs
        }

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
    문서 쿼리 (4-8: 필터링, 페이징, 정렬)

    Args:
        tenant_id: 테넌트 ID
        filename_filter: 파일명 필터
        file_type_filter: 파일 타입 필터
        content_filter: 내용 필터
        page: 페이지 번호
        page_size: 페이지 크기
        sort_field: 정렬 필드
        sort_order: 정렬 순서 (ASC/DESC)

    Returns:
        dict: 쿼리 결과
    """
    loop = asyncio.get_event_loop()

    def _query():
        db_design = _get_or_create_db(tenant_id)
        query_ops = QueryOperations(db_design)

        # 필터 생성
        filter_params = QueryFilter(
            filename=filename_filter,
            file_type=file_type_filter,
            content=content_filter
        )

        # 정렬 파라미터
        sort_params = SortParams(
            field=sort_field,
            order=SortOrder.ASC if sort_order.upper() == "ASC" else SortOrder.DESC
        )

        # 페이지네이션
        pagination = PaginationParams(page=page, page_size=page_size)

        result = query_ops.query(filter_params, sort_params, pagination)

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

    return await loop.run_in_executor(None, _query)


@mcp.tool()
async def search_documents(tenant_id: str, keyword: str, search_fields: List[str] = None) -> dict:
    """
    문서 검색 (4-8)

    Args:
        tenant_id: 테넌트 ID
        keyword: 검색 키워드
        search_fields: 검색할 필드 목록

    Returns:
        dict: 검색 결과
    """
    loop = asyncio.get_event_loop()

    def _search():
        db_design = _get_or_create_db(tenant_id)
        query_ops = QueryOperations(db_design)
        results = query_ops.search(keyword, search_fields)
        return {
            "status": "success",
            "keyword": keyword,
            "count": len(results),
            "results": results
        }

    return await loop.run_in_executor(None, _search)


@mcp.tool()
async def get_statistics(tenant_id: str) -> dict:
    """
    데이터베이스 통계 (4-8)

    Args:
        tenant_id: 테넌트 ID

    Returns:
        dict: 통계 정보
    """
    loop = asyncio.get_event_loop()

    def _stats():
        db_design = _get_or_create_db(tenant_id)
        query_ops = QueryOperations(db_design)
        stats = query_ops.get_statistics()
        return {"status": "success", **stats}

    return await loop.run_in_executor(None, _stats)


# ========================================
# 파일→SQLite 파이프라인 도구 (4-9)
# ========================================

@mcp.tool()
async def load_file_to_db(tenant_id: str, file_path: str, metadata: dict = None) -> dict:
    """
    파일을 데이터베이스에 적재 (4-9)

    Args:
        tenant_id: 테넌트 ID
        file_path: 파일 경로
        metadata: 추가 메타데이터

    Returns:
        dict: 적재 결과
    """
    loop = asyncio.get_event_loop()

    def _load():
        db_design = _get_or_create_db(tenant_id)
        pipeline = FileToDBPipeline(db_design)
        doc_id = pipeline.load_file(Path(file_path), metadata)
        return {
            "status": "success",
            "document_id": doc_id,
            "file_path": file_path
        }

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
    디렉토리의 파일들을 데이터베이스에 적재 (4-9)

    Args:
        tenant_id: 테넌트 ID
        directory_path: 디렉토리 경로
        pattern: 파일 패턴
        recursive: 하위 디렉토리 포함 여부
        skip_existing: 기존 파일 건너뛰기

    Returns:
        dict: 적재 통계
    """
    loop = asyncio.get_event_loop()

    def _load():
        db_design = _get_or_create_db(tenant_id)
        pipeline = FileToDBPipeline(db_design)
        stats = pipeline.load_directory(
            Path(directory_path),
            pattern,
            recursive,
            skip_existing
        )
        return {"status": "success", **stats}

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
    JSON 파일로 리포트 생성 (4-10)

    Args:
        tenant_id: 테넌트 ID
        output_path: 출력 파일 경로
        file_type_filter: 파일 타입 필터
        pretty: 들여쓰기 여부

    Returns:
        dict: 출력 결과
    """
    loop = asyncio.get_event_loop()

    def _export():
        db_design = _get_or_create_db(tenant_id)
        report = DBToFileReport(db_design)
        filter_params = QueryFilter(file_type=file_type_filter) if file_type_filter else None
        result = report.export_to_json(Path(output_path), filter_params, pretty)
        return {"status": "success", **result}

    return await loop.run_in_executor(None, _export)


@mcp.tool()
async def export_to_csv(
    tenant_id: str,
    output_path: str,
    file_type_filter: str = None,
    include_metadata: bool = False
) -> dict:
    """
    CSV 파일로 리포트 생성 (4-10)

    Args:
        tenant_id: 테넌트 ID
        output_path: 출력 파일 경로
        file_type_filter: 파일 타입 필터
        include_metadata: 메타데이터 포함 여부

    Returns:
        dict: 출력 결과
    """
    loop = asyncio.get_event_loop()

    def _export():
        db_design = _get_or_create_db(tenant_id)
        report = DBToFileReport(db_design)
        filter_params = QueryFilter(file_type=file_type_filter) if file_type_filter else None
        result = report.export_to_csv(Path(output_path), filter_params, include_metadata)
        return {"status": "success", **result}

    return await loop.run_in_executor(None, _export)


@mcp.tool()
async def export_to_markdown(
    tenant_id: str,
    output_path: str,
    file_type_filter: str = None,
    include_statistics: bool = True
) -> dict:
    """
    Markdown 파일로 리포트 생성 (4-10)

    Args:
        tenant_id: 테넌트 ID
        output_path: 출력 파일 경로
        file_type_filter: 파일 타입 필터
        include_statistics: 통계 포함 여부

    Returns:
        dict: 출력 결과
    """
    loop = asyncio.get_event_loop()

    def _export():
        db_design = _get_or_create_db(tenant_id)
        report = DBToFileReport(db_design)
        filter_params = QueryFilter(file_type=file_type_filter) if file_type_filter else None
        result = report.export_to_markdown(Path(output_path), filter_params, include_statistics)
        return {"status": "success", **result}

    return await loop.run_in_executor(None, _export)


if __name__ == "__main__":
    mcp.run()
