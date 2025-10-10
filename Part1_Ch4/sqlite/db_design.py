"""
4-6. SQLite API 설계
데이터를 저장하는 작은 데이터베이스 설계하기

멀티테넌시를 고려한 SQLite 데이터베이스 설계 모듈
각 테넌트별로 독립된 데이터베이스를 사용할 수 있도록 구조화
"""

import sqlite3
from pathlib import Path
from typing import Optional
from dataclasses import dataclass
from datetime import datetime


@dataclass
class DatabaseConfig:
    """데이터베이스 설정 클래스"""
    tenant_id: str
    db_path: Optional[Path] = None

    def __post_init__(self):
        if self.db_path is None:
            # 기본 데이터베이스 경로: data/{tenant_id}.db
            self.db_path = Path("data") / f"{self.tenant_id}.db"


class DatabaseDesign:
    """
    SQLite 데이터베이스 스키마 설계 및 초기화 클래스

    멀티테넌시 지원:
    - 각 테넌트별로 독립된 데이터베이스 파일 사용
    - tenant_id를 기반으로 데이터베이스 경로 자동 생성
    """

    # 기본 테이블 스키마
    SCHEMA = """
    -- 문서 메타데이터 테이블
    CREATE TABLE IF NOT EXISTS documents (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        filename TEXT NOT NULL,
        content TEXT NOT NULL,
        file_type TEXT,
        file_size INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        metadata TEXT  -- JSON 형식의 추가 메타데이터
    );

    -- 인덱스 생성 (검색 성능 향상)
    CREATE INDEX IF NOT EXISTS idx_documents_filename
        ON documents(filename);

    CREATE INDEX IF NOT EXISTS idx_documents_created_at
        ON documents(created_at);

    -- 트리거: 업데이트 시 updated_at 자동 갱신
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
        Args:
            config: 데이터베이스 설정 객체
        """
        self.config = config
        self.db_path = config.db_path

    def initialize(self) -> None:
        """
        데이터베이스 초기화
        - 데이터베이스 파일 디렉토리 생성
        - 스키마 적용
        """
        # 데이터베이스 디렉토리 생성
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        # 스키마 적용
        conn = self.get_connection()
        try:
            conn.executescript(self.SCHEMA)
            conn.commit()
        finally:
            conn.close()

    def get_connection(self) -> sqlite3.Connection:
        """
        데이터베이스 연결 반환

        Returns:
            sqlite3.Connection: 데이터베이스 연결 객체
        """
        conn = sqlite3.connect(str(self.db_path))
        # Row factory 설정으로 딕셔너리 형태로 결과 반환
        conn.row_factory = sqlite3.Row
        return conn

    def get_schema_info(self) -> dict:
        """
        데이터베이스 스키마 정보 반환

        Returns:
            dict: 테이블 및 인덱스 정보
        """
        conn = self.get_connection()
        try:
            cursor = conn.cursor()

            # 테이블 목록
            cursor.execute("""
                SELECT name, sql
                FROM sqlite_master
                WHERE type='table' AND name NOT LIKE 'sqlite_%'
            """)
            tables = [dict(row) for row in cursor.fetchall()]

            # 인덱스 목록
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


# 헬퍼 함수
def create_database(tenant_id: str, db_path: Optional[Path] = None) -> DatabaseDesign:
    """
    데이터베이스 생성 헬퍼 함수

    Args:
        tenant_id: 테넌트 ID
        db_path: 데이터베이스 경로 (선택사항)

    Returns:
        DatabaseDesign: 초기화된 데이터베이스 설계 객체
    """
    config = DatabaseConfig(tenant_id=tenant_id, db_path=db_path)
    db_design = DatabaseDesign(config)
    db_design.initialize()
    return db_design


if __name__ == "__main__":
    # 사용 예제
    print("=== SQLite 데이터베이스 설계 예제 ===\n")

    # 테넌트별 데이터베이스 생성
    tenant1_db = create_database("tenant1")
    print(f"테넌트1 데이터베이스 생성: {tenant1_db.db_path}")

    tenant2_db = create_database("tenant2")
    print(f"테넌트2 데이터베이스 생성: {tenant2_db.db_path}")

    # 스키마 정보 출력
    print(f"\n테넌트1 스키마 정보:")
    schema_info = tenant1_db.get_schema_info()
    print(f"테이블 수: {len(schema_info['tables'])}")
    print(f"인덱스 수: {len(schema_info['indexes'])}")
