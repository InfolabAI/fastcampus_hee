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

# 각 모듈에서 필요한 클래스와 함수들을 가져옵니다.
# 이를 통해 `sqlite` 패키지 사용자는 각 하위 모듈을 직접 임포트할 필요 없이
# `from sqlite import DatabaseConfig` 와 같은 형태로 바로 사용할 수 있습니다.

# 4-6: 데이터베이스 설계 관련 기능을 임포트합니다.
from .db_design import (
    DatabaseConfig,    # 데이터베이스 설정을 위한 데이터 클래스
    DatabaseDesign,    # 데이터베이스 스키마 및 연결을 관리하는 클래스
    create_database    # DatabaseDesign 인스턴스를 생성하는 팩토리 함수
)

# 4-7: CRUD (Create, Read, Update, Delete) 작업 관련 기능을 임포트합니다.
from .crud_api import CRUDOperations  # CRUD 작업을 수행하는 메서드를 제공하는 클래스

# 4-8: 데이터 쿼리, 페이징, 정렬 관련 기능을 임포트합니다.
from .query_api import (
    QueryOperations,   # 복잡한 쿼리 및 검색 기능을 제공하는 클래스
    QueryFilter,       # 쿼리 시 사용할 필터 조건을 정의하는 데이터 클래스
    PaginationParams,  # 페이징 처리를 위한 파라미터(페이지 번호, 페이지 크기)를 담는 데이터 클래스
    SortParams,        # 정렬 기준(필드, 순서)을 정의하는 데이터 클래스
    SortOrder,         # 정렬 순서(오름차순, 내림차순)를 나타내는 열거형
    PagedResult        # 페이징된 쿼리 결과를 담는 데이터 클래스
)

# 4-9: 파일 시스템의 파일을 데이터베이스로 적재하는 파이프라인 기능을 임포트합니다.
from .file_to_db_pipeline import FileToDBPipeline  # 파일/디렉토리에서 데이터를 읽어 DB에 저장하는 클래스

# 4-10: 데이터베이스의 데이터를 파일 리포트(JSON, CSV 등)로 생성하는 기능을 임포트합니다.
from .db_to_file_report import DBToFileReport  # DB 데이터를 다양한 포맷의 파일로 내보내는 클래스

# 4-11: 구현된 기능들을 종합적으로 점검하는 체크리스트 기능을 임포트합니다.
from .checklist import SQLiteChecklist  # 전체 기능의 정상 동작을 확인하는 테스트 및 검증 클래스

# `from sqlite import *` 구문을 사용할 때 임포트될 객체들의 목록을 정의합니다.
# 각 커리큘럼 단계별로 관련된 클래스와 함수들을 명시적으로 나열하여
# 패키지의 공개 API를 명확하게 합니다.
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

# 이 패키지의 버전을 정의합니다.
__version__ = "1.0.0"
