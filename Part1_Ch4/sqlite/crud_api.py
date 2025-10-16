"""
4-7. SQLite API 구현: CRUD
데이터를 추가, 조회, 수정, 삭제하는 기능 만들기

Create, Read, Update, Delete 기능 구현
"""

# sqlite3: 파이썬 표준 라이브러리로, SQLite 데이터베이스와의 상호작용을 지원합니다.
import sqlite3
# typing: 타입 힌트를 지원하는 라이브러리입니다.
from typing import Optional, List, Dict, Any
# pathlib.Path: 파일 시스템 경로를 객체 지향적으로 다루기 위한 클래스입니다.
from pathlib import Path
# datetime: 날짜와 시간을 다루는 모듈입니다.
from datetime import datetime
# json: JSON 데이터를 다루기 위한 모듈입니다.
import json

# .db_design 모듈에서 DatabaseDesign, DatabaseConfig 클래스를 임포트합니다.
from .db_design import DatabaseDesign, DatabaseConfig


class CRUDOperations:
    """
    SQLite 데이터베이스에 대한 기본적인 CRUD(Create, Read, Update, Delete) 작업을
    수행하는 메서드를 제공하는 클래스입니다.
    """

    def __init__(self, db_design: DatabaseDesign):
        """
        CRUDOperations 클래스의 인스턴스를 초기화합니다.

        Args:
            db_design (DatabaseDesign): 데이터베이스 연결 및 스키마 정보를 담고 있는
                                       DatabaseDesign 객체입니다.
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
        'documents' 테이블에 새로운 레코드(문서)를 생성합니다.

        Args:
            filename (str): 파일의 이름.
            content (str): 파일의 내용.
            file_type (Optional[str]): 파일의 종류 (e.g., 'text', 'json').
            file_size (Optional[int]): 파일의 크기 (bytes).
            metadata (Optional[Dict[str, Any]]): JSON으로 저장될 추가적인 메타데이터.

        Returns:
            int: 데이터베이스에 성공적으로 삽입된 새 문서의 ID.
        """
        # 데이터베이스 연결을 가져옵니다.
        conn = self.db_design.get_connection()
        try:
            cursor = conn.cursor()

            # metadata 딕셔너리가 있으면 JSON 문자열로 변환합니다.
            metadata_json = json.dumps(metadata) if metadata else None

            # SQL INSERT 문을 실행하여 새 문서를 추가합니다.
            cursor.execute("""
                INSERT INTO documents
                    (filename, content, file_type, file_size, metadata)
                VALUES (?, ?, ?, ?, ?)
            """, (filename, content, file_type, file_size, metadata_json))

            # 변경사항을 데이터베이스에 커밋(저장)합니다.
            conn.commit()
            # 마지막으로 삽입된 행의 ID를 반환합니다.
            return cursor.lastrowid
        finally:
            # 작업이 끝나면 데이터베이스 연결을 닫습니다.
            conn.close()

    def read(self, doc_id: int) -> Optional[Dict[str, Any]]:
        """
        주어진 ID를 가진 문서를 데이터베이스에서 조회합니다.

        Args:
            doc_id (int): 조회할 문서의 ID.

        Returns:
            Optional[Dict[str, Any]]: 조회된 문서의 정보를 담은 딕셔너리.
                                      문서가 없으면 None을 반환합니다.
        """
        conn = self.db_design.get_connection()
        try:
            cursor = conn.cursor()
            # SQL SELECT 문을 실행하여 특정 ID의 문서를 조회합니다.
            cursor.execute("""
                SELECT * FROM documents WHERE id = ?
            """, (doc_id,))

            row = cursor.fetchone()
            if row:
                # 조회된 결과를 딕셔너리 형태로 변환합니다.
                doc = dict(row)
                # metadata 필드가 존재하면 JSON 문자열을 파이썬 딕셔너리로 변환합니다.
                if doc.get('metadata'):
                    doc['metadata'] = json.loads(doc['metadata'])
                return doc
            return None
        finally:
            conn.close()

    def read_all(self) -> List[Dict[str, Any]]:
        """
        'documents' 테이블의 모든 문서를 조회합니다.

        Returns:
            List[Dict[str, Any]]: 모든 문서의 정보를 담은 딕셔너리 리스트.
        """
        conn = self.db_design.get_connection()
        try:
            cursor = conn.cursor()
            # SQL SELECT 문을 실행하여 모든 문서를 ID 순서로 정렬하여 조회합니다.
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
        주어진 ID를 가진 문서를 수정합니다. 제공된 필드만 업데이트됩니다.

        Args:
            doc_id (int): 수정할 문서의 ID.
            filename (Optional[str]): 새로 변경할 파일 이름.
            content (Optional[str]): 새로 변경할 파일 내용.
            file_type (Optional[str]): 새로 변경할 파일 타입.
            file_size (Optional[int]): 새로 변경할 파일 크기.
            metadata (Optional[Dict[str, Any]]): 새로 변경할 메타데이터.

        Returns:
            bool: 업데이트가 성공적으로 이루어졌으면 True, 아니면 False.
        """
        # 업데이트할 필드와 파라미터를 동적으로 구성합니다.
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

        # 업데이트할 내용이 없으면 False를 반환하고 함수를 종료합니다.
        if not updates:
            return False

        params.append(doc_id)

        conn = self.db_design.get_connection()
        try:
            cursor = conn.cursor()
            # 동적으로 생성된 SET 절을 포함하는 SQL UPDATE 문을 구성합니다.
            query = f"UPDATE documents SET {', '.join(updates)} WHERE id = ?"
            cursor.execute(query, params)
            conn.commit()

            # 실제로 변경된 행이 있는지 여부를 반환합니다.
            return cursor.rowcount > 0
        finally:
            conn.close()

    def delete(self, doc_id: int) -> bool:
        """
        주어진 ID를 가진 문서를 데이터베이스에서 삭제합니다.

        Args:
            doc_id (int): 삭제할 문서의 ID.

        Returns:
            bool: 삭제가 성공적으로 이루어졌으면 True, 아니면 False.
        """
        conn = self.db_design.get_connection()
        try:
            cursor = conn.cursor()
            # SQL DELETE 문을 실행하여 특정 ID의 문서를 삭제합니다.
            cursor.execute("DELETE FROM documents WHERE id = ?", (doc_id,))
            conn.commit()

            # 실제로 삭제된 행이 있는지 여부를 반환합니다.
            return cursor.rowcount > 0
        finally:
            conn.close()

    def delete_all(self) -> int:
        """
        'documents' 테이블의 모든 문서를 삭제합니다.

        Returns:
            int: 삭제된 문서의 총 개수.
        """
        conn = self.db_design.get_connection()
        try:
            cursor = conn.cursor()
            # SQL DELETE 문을 실행하여 모든 문서를 삭제합니다.
            cursor.execute("DELETE FROM documents")
            conn.commit()

            # 삭제된 행의 수를 반환합니다.
            return cursor.rowcount
        finally:
            conn.close()

    def count(self) -> int:
        """
        'documents' 테이블의 총 문서 개수를 반환합니다.

        Returns:
            int: 문서의 총 개수.
        """
        conn = self.db_design.get_connection()
        try:
            cursor = conn.cursor()
            # SQL SELECT COUNT(*) 문을 실행하여 문서의 총 개수를 조회합니다.
            cursor.execute("SELECT COUNT(*) FROM documents")
            # 조회 결과의 첫 번째 값을 반환합니다.
            return cursor.fetchone()[0]
        finally:
            conn.close()

    def exists(self, doc_id: int) -> bool:
        """
        주어진 ID를 가진 문서가 존재하는지 확인합니다.

        Args:
            doc_id (int): 확인할 문서의 ID.

        Returns:
            bool: 문서가 존재하면 True, 아니면 False.
        """
        conn = self.db_design.get_connection()
        try:
            cursor = conn.cursor()
            # 특정 ID의 문서가 존재하는지 확인하는 SQL 쿼리를 실행합니다.
            # LIMIT 1을 사용하여 효율성을 높입니다.
            cursor.execute(
                "SELECT 1 FROM documents WHERE id = ? LIMIT 1",
                (doc_id,)
            )
            # fetchone() 결과가 None이 아니면 문서가 존재하는 것입니다.
            return cursor.fetchone() is not None
        finally:
            conn.close()


# 이 스크립트가 직접 실행될 때, 아래의 예제 코드를 실행합니다.
if __name__ == "__main__":
    # 사용 예제
    from .db_design import create_database

    print("=== SQLite CRUD 작업 예제 ===\n")

    # 'test_crud' 테넌트용 데이터베이스를 생성합니다.
    db_design = create_database("test_crud")
    crud = CRUDOperations(db_design)

    # 1. Create - 새로운 문서들을 생성합니다.
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

    # 2. Read - 생성된 문서를 조회합니다.
    print("\n2. 문서 조회")
    doc = crud.read(doc1_id)
    print(f"   문서 {doc1_id}: {doc['filename']} - {doc['content'][:20]}...")

    # 3. Read All - 모든 문서를 조회합니다.
    print("\n3. 전체 문서 조회")
    all_docs = crud.read_all()
    print(f"   전체 문서 수: {len(all_docs)}")
    for doc in all_docs:
        print(f"   - ID {doc['id']}: {doc['filename']}")

    # 4. Update - 문서를 수정합니다.
    print("\n4. 문서 수정")
    success = crud.update(
        doc1_id,
        content="Updated content!",
        metadata={"author": "Bob", "updated": True}
    )
    print(f"   수정 성공: {success}")

    updated_doc = crud.read(doc1_id)
    print(f"   수정된 내용: {updated_doc['content']}")

    # 5. Count - 전체 문서 개수를 확인합니다.
    print("\n5. 문서 개수")
    count = crud.count()
    print(f"   총 문서 수: {count}")

    # 6. Exists - 특정 문서의 존재 여부를 확인합니다.
    print("\n6. 문서 존재 확인")
    print(f"   문서 {doc1_id} 존재: {crud.exists(doc1_id)}")
    print(f"   문서 999 존재: {crud.exists(999)}")

    # 7. Delete - 문서를 삭제합니다.
    print("\n7. 문서 삭제")
    success = crud.delete(doc2_id)
    print(f"   삭제 성공: {success}")
    print(f"   남은 문서 수: {crud.count()}")
