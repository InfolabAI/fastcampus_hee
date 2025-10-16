"""
4-6. SQLite API 설계
데이터를 저장하는 작은 데이터베이스 설계하기

멀티테넌시를 고려한 SQLite 데이터베이스 설계 모듈
각 테넌트별로 독립된 데이터베이스를 사용할 수 있도록 구조화
"""

# sqlite3: 파이썬 표준 라이브러리로, SQLite 데이터베이스와의 상호작용을 지원합니다.
import sqlite3
# pathlib.Path: 파일 시스템 경로를 객체 지향적으로 다루기 위한 클래스입니다.
from pathlib import Path
# typing: 타입 힌트를 지원하는 라이브러리입니다.
from typing import Optional
# dataclasses.dataclass: 데이터 저장을 위한 클래스를 쉽게 만들 수 있는 데코레이터입니다.
from dataclasses import dataclass
# datetime: 날짜와 시간을 다루는 모듈입니다.
from datetime import datetime


@dataclass
class DatabaseConfig:
    """
    데이터베이스 설정을 저장하는 데이터 클래스입니다.
    테넌트 ID와 데이터베이스 파일 경로를 속성으로 가집니다.
    """
    tenant_id: str  # 각 사용자를 구분하는 고유한 ID
    db_path: Optional[Path] = None  # 데이터베이스 파일의 경로, 지정하지 않으면 기본 경로 사용

    def __post_init__(self):
        """
        객체 초기화 후 실행되는 메서드입니다.
        db_path가 지정되지 않은 경우, 기본 경로를 설정합니다.
        """
        if self.db_path is None:
            # 기본 데이터베이스 경로는 'data/' 디렉토리 아래에 '테넌트ID.db' 파일로 설정됩니다.
            self.db_path = Path("data") / f"{self.tenant_id}.db"


class DatabaseDesign:
    """
    SQLite 데이터베이스의 스키마를 설계하고 초기화하는 클래스입니다.
    멀티테넌시를 지원하여 각 테넌트가 독립된 데이터베이스 파일을 갖도록 합니다.
    """

    # 데이터베이스의 기본 테이블 스키마를 정의하는 SQL 문자열입니다.
    SCHEMA = """
    -- 'documents' 테이블: 문서의 메타데이터와 내용을 저장합니다.
    -- IF NOT EXISTS: 테이블이 이미 존재하면 새로 만들지 않습니다.
    CREATE TABLE IF NOT EXISTS documents (
        id INTEGER PRIMARY KEY AUTOINCREMENT, -- 각 문서를 고유하게 식별하는 ID
        filename TEXT NOT NULL,               -- 파일 이름
        content TEXT NOT NULL,                -- 파일의 전체 내용
        file_type TEXT,                       -- 파일의 종류 (e.g., 'text', 'image')
        file_size INTEGER,                    -- 파일 크기 (bytes)
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, -- 문서 생성 시각
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, -- 문서 마지막 수정 시각
        metadata TEXT                         -- JSON 형식의 추가 메타데이터
    );

    -- 'idx_documents_filename' 인덱스: filename을 기준으로 한 검색 성능을 향상시킵니다.
    CREATE INDEX IF NOT EXISTS idx_documents_filename
        ON documents(filename);

    -- 'idx_documents_created_at' 인덱스: 생성 시각을 기준으로 한 정렬 및 검색 성능을 향상시킵니다.
    CREATE INDEX IF NOT EXISTS idx_documents_created_at
        ON documents(created_at);

    -- 'update_documents_timestamp' 트리거: 'documents' 테이블의 행이 업데이트될 때마다
    -- 'updated_at' 필드를 현재 시각으로 자동 갱신합니다.
    CREATE TRIGGER IF NOT EXISTS update_documents_timestamp
        AFTER UPDATE ON documents
    BEGIN
        UPDATE documents
        SET updated_at = CURRENT_TIMESTAMP
        WHERE id = NEW.id;
    END;
    """

    def __init__(self, config: DatabaseConfig):
        """
        DatabaseDesign 클래스의 인스턴스를 초기화합니다.

        Args:
            config (DatabaseConfig): 데이터베이스 설정을 담고 있는 객체입니다.
        """
        self.config = config
        self.db_path = config.db_path

    def initialize(self) -> None:
        """
        데이터베이스를 초기화합니다.
        - 데이터베이스 파일이 저장될 디렉토리를 생성합니다.
        - 정의된 스키마(SCHEMA)를 데이터베이스에 적용합니다.
        """
        # 데이터베이스 파일이 위치할 부모 디렉토리를 생성합니다.
        # parents=True: 필요한 모든 상위 디렉토리를 생성합니다.
        # exist_ok=True: 디렉토리가 이미 존재해도 오류를 발생시키지 않습니다.
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        # 데이터베이스 연결을 얻어 스키마를 실행합니다.
        conn = self.get_connection()
        try:
            # executescript는 여러 SQL 문장을 한 번에 실행할 수 있습니다.
            conn.executescript(self.SCHEMA)
            # 변경사항을 데이터베이스에 최종 저장(커밋)합니다.
            conn.commit()
        finally:
            # 작업이 끝나면 항상 데이터베이스 연결을 닫습니다.
            conn.close()

    def get_connection(self) -> sqlite3.Connection:
        """
        데이터베이스에 대한 새로운 연결 객체를 생성하고 반환합니다.

        Returns:
            sqlite3.Connection: SQLite 데이터베이스 연결 객체.
        """
        conn = sqlite3.connect(str(self.db_path))
        # row_factory를 sqlite3.Row로 설정하면, 쿼리 결과를
        # 컬럼 이름으로 접근할 수 있는 딕셔너리 유사 객체로 받을 수 있습니다.
        conn.row_factory = sqlite3.Row
        return conn

    def get_schema_info(self) -> dict:
        """
        현재 데이터베이스의 스키마 정보를 조회하여 반환합니다.

        Returns:
            dict: 테넌트 ID, DB 경로, 테이블 및 인덱스 목록을 포함하는 딕셔너리.
        """
        conn = self.get_connection()
        try:
            cursor = conn.cursor()

            # 'sqlite_master' 테이블에서 사용자 정의 테이블 목록을 조회합니다.
            # 'sqlite_%'로 시작하는 시스템 테이블은 제외합니다.
            cursor.execute("""
                SELECT name, sql
                FROM sqlite_master
                WHERE type='table' AND name NOT LIKE 'sqlite_%'
            """)
            tables = [dict(row) for row in cursor.fetchall()]

            # 'sqlite_master' 테이블에서 인덱스 목록을 조회합니다.
            cursor.execute("""
                SELECT name, sql
                FROM sqlite_master
                WHERE type='index' AND name NOT LIKE 'sqlite_%'
            """)
            indexes = [dict(row) for row in cursor.fetchall()]

            return {
                "tenant_id": self.config.tenant_id,
                "db_path": str(self.db_path),
                "tables": tables,
                "indexes": indexes
            }
        finally:
            conn.close()


# 팩토리 함수(Helper Function)
def create_database(tenant_id: str, db_path: Optional[Path] = None) -> DatabaseDesign:
    """
    DatabaseDesign 객체를 생성하고 초기화하는 헬퍼 함수입니다.
    이 함수를 사용하면 데이터베이스 생성 과정을 단순화할 수 있습니다.

    Args:
        tenant_id (str): 생성할 데이터베이스의 테넌트 ID.
        db_path (Optional[Path]): 데이터베이스 파일 경로 (지정하지 않으면 기본값 사용).

    Returns:
        DatabaseDesign: 모든 초기화가 완료된 데이터베이스 설계 객체.
    """
    # 1. 설정 객체 생성
    config = DatabaseConfig(tenant_id=tenant_id, db_path=db_path)
    # 2. 데이터베이스 설계 객체 생성
    db_design = DatabaseDesign(config)
    # 3. 데이터베이스 초기화 (파일 및 스키마 생성)
    db_design.initialize()
    # 4. 초기화된 객체 반환
    return db_design


# 이 스크립트가 직접 실행될 때, 아래의 예제 코드를 실행합니다.
if __name__ == "__main__":
    print("=== SQLite 데이터베이스 설계 예제 ===\n")

    # 'tenant1'과 'tenant2'라는 두 개의 다른 테넌트에 대한 데이터베이스를 생성합니다.
    # 각 테넌트는 별도의 데이터베이스 파일(tenant1.db, tenant2.db)을 갖게 됩니다.
    tenant1_db = create_database("tenant1")
    print(f"테넌트1 데이터베이스 생성: {tenant1_db.db_path}")

    tenant2_db = create_database("tenant2")
    print(f"테넌트2 데이터베이스 생성: {tenant2_db.db_path}")

    # 'tenant1' 데이터베이스의 스키마 정보를 조회하고 출력합니다.
    print(f"\n테넌트1 스키마 정보:")
    schema_info = tenant1_db.get_schema_info()
    print(f"테이블 수: {len(schema_info['tables'])}")
    print(f"인덱스 수: {len(schema_info['indexes'])}")
