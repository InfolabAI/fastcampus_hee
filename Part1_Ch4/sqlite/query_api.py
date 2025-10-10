"""
4-8. SQLite API 구현: 쿼리/페이징/정렬
원하는 데이터만 골라보고 나눠보는 기능 만들기

필터링, 페이지네이션, 정렬 기능 구현
"""

import sqlite3
from typing import List, Dict, Any, Optional, Tuple
from enum import Enum
from dataclasses import dataclass

from .db_design import DatabaseDesign


class SortOrder(Enum):
    """정렬 순서"""
    ASC = "ASC"
    DESC = "DESC"


@dataclass
class QueryFilter:
    """쿼리 필터 조건"""
    filename: Optional[str] = None  # 파일명 검색 (LIKE)
    file_type: Optional[str] = None  # 파일 타입
    content: Optional[str] = None  # 내용 검색 (LIKE)
    created_after: Optional[str] = None  # 생성일 이후
    created_before: Optional[str] = None  # 생성일 이전


@dataclass
class PaginationParams:
    """페이지네이션 파라미터"""
    page: int = 1  # 페이지 번호 (1부터 시작)
    page_size: int = 10  # 페이지당 항목 수

    @property
    def offset(self) -> int:
        """OFFSET 계산"""
        return (self.page - 1) * self.page_size

    @property
    def limit(self) -> int:
        """LIMIT 값 반환"""
        return self.page_size


@dataclass
class SortParams:
    """정렬 파라미터"""
    field: str = "id"  # 정렬 필드
    order: SortOrder = SortOrder.ASC  # 정렬 순서

    # 허용된 정렬 필드
    ALLOWED_FIELDS = ["id", "filename", "file_type", "file_size", "created_at", "updated_at"]

    def __post_init__(self):
        if self.field not in self.ALLOWED_FIELDS:
            raise ValueError(f"Invalid sort field: {self.field}. Allowed: {self.ALLOWED_FIELDS}")


@dataclass
class PagedResult:
    """페이지네이션 결과"""
    items: List[Dict[str, Any]]  # 결과 항목
    total_count: int  # 전체 항목 수
    page: int  # 현재 페이지
    page_size: int  # 페이지 크기
    total_pages: int  # 전체 페이지 수

    @property
    def has_next(self) -> bool:
        """다음 페이지 존재 여부"""
        return self.page < self.total_pages

    @property
    def has_previous(self) -> bool:
        """이전 페이지 존재 여부"""
        return self.page > 1


class QueryOperations:
    """
    SQLite 쿼리 작업 클래스

    필터링, 페이지네이션, 정렬 기능 제공
    """

    def __init__(self, db_design: DatabaseDesign):
        """
        Args:
            db_design: DatabaseDesign 인스턴스
        """
        self.db_design = db_design

    def _build_where_clause(
        self,
        filter_params: Optional[QueryFilter]
    ) -> Tuple[str, List[Any]]:
        """
        WHERE 절 생성

        Args:
            filter_params: 필터 파라미터

        Returns:
            Tuple[str, List[Any]]: WHERE 절 문자열과 바인딩 파라미터
        """
        if not filter_params:
            return "", []

        conditions = []
        params = []

        if filter_params.filename:
            conditions.append("filename LIKE ?")
            params.append(f"%{filter_params.filename}%")

        if filter_params.file_type:
            conditions.append("file_type = ?")
            params.append(filter_params.file_type)

        if filter_params.content:
            conditions.append("content LIKE ?")
            params.append(f"%{filter_params.content}%")

        if filter_params.created_after:
            conditions.append("created_at >= ?")
            params.append(filter_params.created_after)

        if filter_params.created_before:
            conditions.append("created_at <= ?")
            params.append(filter_params.created_before)

        if conditions:
            where_clause = "WHERE " + " AND ".join(conditions)
            return where_clause, params

        return "", []

    def query(
        self,
        filter_params: Optional[QueryFilter] = None,
        sort_params: Optional[SortParams] = None,
        pagination: Optional[PaginationParams] = None
    ) -> PagedResult:
        """
        필터링, 정렬, 페이지네이션을 적용한 쿼리

        Args:
            filter_params: 필터 조건
            sort_params: 정렬 조건
            pagination: 페이지네이션 조건

        Returns:
            PagedResult: 페이지네이션된 결과
        """
        # 기본값 설정
        sort_params = sort_params or SortParams()
        pagination = pagination or PaginationParams()

        # WHERE 절 생성
        where_clause, where_params = self._build_where_clause(filter_params)

        conn = self.db_design.get_connection()
        try:
            cursor = conn.cursor()

            # 전체 개수 조회
            count_query = f"SELECT COUNT(*) FROM documents {where_clause}"
            cursor.execute(count_query, where_params)
            total_count = cursor.fetchone()[0]

            # 전체 페이지 수 계산
            total_pages = (total_count + pagination.page_size - 1) // pagination.page_size

            # 데이터 조회
            data_query = f"""
                SELECT * FROM documents
                {where_clause}
                ORDER BY {sort_params.field} {sort_params.order.value}
                LIMIT ? OFFSET ?
            """
            query_params = where_params + [pagination.limit, pagination.offset]
            cursor.execute(data_query, query_params)

            items = [dict(row) for row in cursor.fetchall()]

            return PagedResult(
                items=items,
                total_count=total_count,
                page=pagination.page,
                page_size=pagination.page_size,
                total_pages=total_pages
            )
        finally:
            conn.close()

    def search(
        self,
        keyword: str,
        search_fields: List[str] = None
    ) -> List[Dict[str, Any]]:
        """
        키워드 검색

        Args:
            keyword: 검색 키워드
            search_fields: 검색할 필드 리스트 (기본: filename, content)

        Returns:
            List[Dict[str, Any]]: 검색 결과
        """
        search_fields = search_fields or ["filename", "content"]

        # 각 필드에 대한 LIKE 조건 생성
        conditions = [f"{field} LIKE ?" for field in search_fields]
        where_clause = "WHERE " + " OR ".join(conditions)

        # 각 필드마다 같은 키워드 파라미터 바인딩
        params = [f"%{keyword}%"] * len(search_fields)

        conn = self.db_design.get_connection()
        try:
            cursor = conn.cursor()
            query = f"SELECT * FROM documents {where_clause} ORDER BY id"
            cursor.execute(query, params)

            return [dict(row) for row in cursor.fetchall()]
        finally:
            conn.close()

    def get_statistics(self) -> Dict[str, Any]:
        """
        데이터베이스 통계 정보

        Returns:
            Dict[str, Any]: 통계 정보
        """
        conn = self.db_design.get_connection()
        try:
            cursor = conn.cursor()

            # 전체 문서 수
            cursor.execute("SELECT COUNT(*) FROM documents")
            total_count = cursor.fetchone()[0]

            # 파일 타입별 개수
            cursor.execute("""
                SELECT file_type, COUNT(*) as count
                FROM documents
                GROUP BY file_type
                ORDER BY count DESC
            """)
            type_distribution = [dict(row) for row in cursor.fetchall()]

            # 전체 파일 크기
            cursor.execute("SELECT SUM(file_size) FROM documents")
            total_size = cursor.fetchone()[0] or 0

            # 평균 파일 크기
            cursor.execute("SELECT AVG(file_size) FROM documents")
            avg_size = cursor.fetchone()[0] or 0

            return {
                "total_count": total_count,
                "total_size": total_size,
                "average_size": round(avg_size, 2),
                "type_distribution": type_distribution
            }
        finally:
            conn.close()


if __name__ == "__main__":
    # 사용 예제
    from .db_design import create_database
    from .crud_api import CRUDOperations

    print("=== SQLite 쿼리/페이징/정렬 예제 ===\n")

    # 데이터베이스 생성 및 샘플 데이터 추가
    db_design = create_database("test_query")
    crud = CRUDOperations(db_design)
    query_ops = QueryOperations(db_design)

    # 샘플 데이터 생성
    print("1. 샘플 데이터 생성")
    for i in range(25):
        crud.create(
            filename=f"file_{i+1}.txt",
            content=f"Content of file {i+1}",
            file_type="text" if i % 2 == 0 else "json",
            file_size=100 + i * 10
        )
    print(f"   {crud.count()}개 문서 생성 완료")

    # 2. 페이지네이션
    print("\n2. 페이지네이션 (페이지 1, 크기 10)")
    result = query_ops.query(
        pagination=PaginationParams(page=1, page_size=10)
    )
    print(f"   전체 {result.total_count}개 중 {len(result.items)}개 표시")
    print(f"   전체 페이지: {result.total_pages}")
    print(f"   다음 페이지 존재: {result.has_next}")

    # 3. 정렬
    print("\n3. 정렬 (파일명 내림차순)")
    result = query_ops.query(
        sort_params=SortParams(field="filename", order=SortOrder.DESC),
        pagination=PaginationParams(page=1, page_size=5)
    )
    for item in result.items:
        print(f"   - {item['filename']}")

    # 4. 필터링
    print("\n4. 필터링 (파일 타입: text)")
    result = query_ops.query(
        filter_params=QueryFilter(file_type="text"),
        pagination=PaginationParams(page=1, page_size=5)
    )
    print(f"   text 타입 문서: {result.total_count}개")

    # 5. 검색
    print("\n5. 검색 (키워드: 'file_1')")
    results = query_ops.search(keyword="file_1")
    print(f"   검색 결과: {len(results)}개")
    for item in results[:3]:
        print(f"   - {item['filename']}")

    # 6. 통계
    print("\n6. 통계 정보")
    stats = query_ops.get_statistics()
    print(f"   전체 문서 수: {stats['total_count']}")
    print(f"   전체 크기: {stats['total_size']} bytes")
    print(f"   평균 크기: {stats['average_size']} bytes")
    print("   타입별 분포:")
    for dist in stats['type_distribution']:
        print(f"      - {dist['file_type']}: {dist['count']}개")
