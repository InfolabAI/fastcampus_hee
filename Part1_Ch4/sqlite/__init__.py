"""
Part1_Ch4 SQLite 모듈

멀티테넌시를 지원하는 SQLite 데이터베이스 API 모듈
각 커리큘럼 항목별로 구현된 기능을 제공합니다.

모듈 구조:
- db_design: 데이터베이스 설계 및 초기화 (4-6)
- crud_api: CRUD 작업 (4-7)
- query_api: 쿼리/페이징/정렬 (4-8)
- file_to_db_pipeline: 파일→SQLite 적재 파이프라인 (4-9)
- db_to_file_report: SQLite→파일 리포트 생성 (4-10)
- checklist: 종합 점검 체크리스트 (4-11)
"""

# 데이터베이스 설계 (4-6)
from .db_design import (
    DatabaseConfig,
    DatabaseDesign,
    create_database
)

# CRUD 작업 (4-7)
from .crud_api import CRUDOperations

# 쿼리/페이징/정렬 (4-8)
from .query_api import (
    QueryOperations,
    QueryFilter,
    PaginationParams,
    SortParams,
    SortOrder,
    PagedResult
)

# 파일→SQLite 파이프라인 (4-9)
from .file_to_db_pipeline import FileToDBPipeline

# SQLite→파일 리포트 (4-10)
from .db_to_file_report import DBToFileReport

# 종합 점검 (4-11)
from .checklist import SQLiteChecklist

__all__ = [
    # 4-6: 데이터베이스 설계
    "DatabaseConfig",
    "DatabaseDesign",
    "create_database",

    # 4-7: CRUD 작업
    "CRUDOperations",

    # 4-8: 쿼리/페이징/정렬
    "QueryOperations",
    "QueryFilter",
    "PaginationParams",
    "SortParams",
    "SortOrder",
    "PagedResult",

    # 4-9: 파일→SQLite 파이프라인
    "FileToDBPipeline",

    # 4-10: SQLite→파일 리포트
    "DBToFileReport",

    # 4-11: 종합 점검
    "SQLiteChecklist",
]

__version__ = "1.0.0"
