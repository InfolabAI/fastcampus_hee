"""
4-7. SQLite API 구현: CRUD
데이터를 추가, 조회, 수정, 삭제하는 기능 만들기

Create, Read, Update, Delete 기능 구현
"""

import sqlite3
from typing import Optional, List, Dict, Any
from pathlib import Path
from datetime import datetime
import json

from .db_design import DatabaseDesign, DatabaseConfig


class CRUDOperations:
    """
    SQLite CRUD 작업 클래스

    데이터베이스에 대한 기본적인 생성, 읽기, 수정, 삭제 작업 제공
    """

    def __init__(self, db_design: DatabaseDesign):
        """
        Args:
            db_design: DatabaseDesign 인스턴스
        """
        self.db_design = db_design

    def create(
        self,
        filename: str,
        content: str,
        file_type: Optional[str] = None,
        file_size: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        새 문서 생성

        Args:
            filename: 파일명
            content: 파일 내용
            file_type: 파일 타입
            file_size: 파일 크기
            metadata: 추가 메타데이터 (딕셔너리)

        Returns:
            int: 생성된 문서의 ID
        """
        conn = self.db_design.get_connection()
        try:
            cursor = conn.cursor()

            # 메타데이터를 JSON 문자열로 변환
            metadata_json = json.dumps(metadata) if metadata else None

            cursor.execute("""
                INSERT INTO documents
                    (filename, content, file_type, file_size, metadata)
                VALUES (?, ?, ?, ?, ?)
            """, (filename, content, file_type, file_size, metadata_json))

            conn.commit()
            return cursor.lastrowid
        finally:
            conn.close()

    def read(self, doc_id: int) -> Optional[Dict[str, Any]]:
        """
        문서 조회

        Args:
            doc_id: 문서 ID

        Returns:
            Optional[Dict[str, Any]]: 문서 정보 (없으면 None)
        """
        conn = self.db_design.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM documents WHERE id = ?
            """, (doc_id,))

            row = cursor.fetchone()
            if row:
                doc = dict(row)
                # JSON 문자열을 딕셔너리로 변환
                if doc.get('metadata'):
                    doc['metadata'] = json.loads(doc['metadata'])
                return doc
            return None
        finally:
            conn.close()

    def read_all(self) -> List[Dict[str, Any]]:
        """
        모든 문서 조회

        Returns:
            List[Dict[str, Any]]: 모든 문서 목록
        """
        conn = self.db_design.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM documents ORDER BY id")

            docs = []
            for row in cursor.fetchall():
                doc = dict(row)
                if doc.get('metadata'):
                    doc['metadata'] = json.loads(doc['metadata'])
                docs.append(doc)
            return docs
        finally:
            conn.close()

    def update(
        self,
        doc_id: int,
        filename: Optional[str] = None,
        content: Optional[str] = None,
        file_type: Optional[str] = None,
        file_size: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        문서 수정

        Args:
            doc_id: 문서 ID
            filename: 파일명 (선택)
            content: 파일 내용 (선택)
            file_type: 파일 타입 (선택)
            file_size: 파일 크기 (선택)
            metadata: 추가 메타데이터 (선택)

        Returns:
            bool: 수정 성공 여부
        """
        # 업데이트할 필드 동적 생성
        updates = []
        params = []

        if filename is not None:
            updates.append("filename = ?")
            params.append(filename)

        if content is not None:
            updates.append("content = ?")
            params.append(content)

        if file_type is not None:
            updates.append("file_type = ?")
            params.append(file_type)

        if file_size is not None:
            updates.append("file_size = ?")
            params.append(file_size)

        if metadata is not None:
            updates.append("metadata = ?")
            params.append(json.dumps(metadata))

        if not updates:
            return False  # 업데이트할 내용이 없음

        params.append(doc_id)

        conn = self.db_design.get_connection()
        try:
            cursor = conn.cursor()
            query = f"UPDATE documents SET {', '.join(updates)} WHERE id = ?"
            cursor.execute(query, params)
            conn.commit()

            return cursor.rowcount > 0
        finally:
            conn.close()

    def delete(self, doc_id: int) -> bool:
        """
        문서 삭제

        Args:
            doc_id: 문서 ID

        Returns:
            bool: 삭제 성공 여부
        """
        conn = self.db_design.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM documents WHERE id = ?", (doc_id,))
            conn.commit()

            return cursor.rowcount > 0
        finally:
            conn.close()

    def delete_all(self) -> int:
        """
        모든 문서 삭제

        Returns:
            int: 삭제된 문서 수
        """
        conn = self.db_design.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM documents")
            conn.commit()

            return cursor.rowcount
        finally:
            conn.close()

    def count(self) -> int:
        """
        문서 총 개수 반환

        Returns:
            int: 문서 개수
        """
        conn = self.db_design.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM documents")
            return cursor.fetchone()[0]
        finally:
            conn.close()

    def exists(self, doc_id: int) -> bool:
        """
        문서 존재 여부 확인

        Args:
            doc_id: 문서 ID

        Returns:
            bool: 존재 여부
        """
        conn = self.db_design.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT 1 FROM documents WHERE id = ? LIMIT 1",
                (doc_id,)
            )
            return cursor.fetchone() is not None
        finally:
            conn.close()


if __name__ == "__main__":
    # 사용 예제
    from .db_design import create_database

    print("=== SQLite CRUD 작업 예제 ===\n")

    # 데이터베이스 생성
    db_design = create_database("test_crud")
    crud = CRUDOperations(db_design)

    # 1. Create - 문서 생성
    print("1. 문서 생성")
    doc1_id = crud.create(
        filename="example.txt",
        content="Hello, World!",
        file_type="text",
        file_size=13,
        metadata={"author": "Alice", "tags": ["test", "example"]}
    )
    print(f"   생성된 문서 ID: {doc1_id}")

    doc2_id = crud.create(
        filename="data.json",
        content='{"key": "value"}',
        file_type="json",
        file_size=16
    )
    print(f"   생성된 문서 ID: {doc2_id}")

    # 2. Read - 문서 조회
    print("\n2. 문서 조회")
    doc = crud.read(doc1_id)
    print(f"   문서 {doc1_id}: {doc['filename']} - {doc['content'][:20]}...")

    # 3. Read All - 전체 문서 조회
    print("\n3. 전체 문서 조회")
    all_docs = crud.read_all()
    print(f"   전체 문서 수: {len(all_docs)}")
    for doc in all_docs:
        print(f"   - ID {doc['id']}: {doc['filename']}")

    # 4. Update - 문서 수정
    print("\n4. 문서 수정")
    success = crud.update(
        doc1_id,
        content="Updated content!",
        metadata={"author": "Bob", "updated": True}
    )
    print(f"   수정 성공: {success}")

    updated_doc = crud.read(doc1_id)
    print(f"   수정된 내용: {updated_doc['content']}")

    # 5. Count - 문서 개수
    print("\n5. 문서 개수")
    count = crud.count()
    print(f"   총 문서 수: {count}")

    # 6. Exists - 문서 존재 확인
    print("\n6. 문서 존재 확인")
    print(f"   문서 {doc1_id} 존재: {crud.exists(doc1_id)}")
    print(f"   문서 999 존재: {crud.exists(999)}")

    # 7. Delete - 문서 삭제
    print("\n7. 문서 삭제")
    success = crud.delete(doc2_id)
    print(f"   삭제 성공: {success}")
    print(f"   남은 문서 수: {crud.count()}")
