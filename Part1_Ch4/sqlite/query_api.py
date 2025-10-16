"""
4-8. SQLite API 구현: 쿼리/페이징/정렬
원하는 데이터만 골라보고 나눠보는 기능 만들기

필터링, 페이지네이션, 정렬 기능 구현
"""

# sqlite3: 파이썬 표준 라이브러리로, SQLite 데이터베이스와의 상호작용을 지원합니다.
import sqlite3
# typing: 타입 힌트를 지원하는 라이브러리입니다.
from typing import List, Dict, Any, Optional, Tuple
# enum.Enum: 열거형(Enumeration)을 만들기 위한 기본 클래스입니다.
from enum import Enum
# dataclasses.dataclass: 데이터 저장을 위한 클래스를 쉽게 만들 수 있는 데코레이터입니다.
from dataclasses import dataclass

# .db_design 모듈에서 DatabaseDesign 클래스를 임포트합니다.
from .db_design import DatabaseDesign


class SortOrder(Enum):
    """정렬 순서를 나타내는 열거형입니다."""
    ASC = "ASC"  # 오름차순
    DESC = "DESC"  # 내림차순


@dataclass
class QueryFilter:
    """
    데이터 조회 시 사용할 필터 조건들을 정의하는 데이터 클래스입니다.
    각 필드는 선택적으로 사용될 수 있습니다.
    """
    filename: Optional[str] = None      # 파일명으로 검색 (LIKE '%...%')
    file_type: Optional[str] = None     # 특정 파일 타입과 일치
    content: Optional[str] = None       # 내용으로 검색 (LIKE '%...%')
    created_after: Optional[str] = None  # 특정 날짜/시간 이후에 생성된 문서
    created_before: Optional[str] = None  # 특정 날짜/시간 이전에 생성된 문서


@dataclass
class PaginationParams:
    """
    페이지네이션(Paging)에 필요한 파라미터들을 정의하는 데이터 클래스입니다.
    """
    page: int = 1       # 조회할 페이지 번호 (1부터 시작)
    page_size: int = 10  # 한 페이지에 보여줄 항목의 수

    @property
    def offset(self) -> int:
        """SQL 쿼리의 OFFSET 값을 계산하여 반환합니다."""
        return (self.page - 1) * self.page_size

    @property
    def limit(self) -> int:
        """SQL 쿼리의 LIMIT 값을 반환합니다."""
        return self.page_size


@dataclass
class SortParams:
    """
    정렬에 필요한 파라미터(정렬 기준 필드, 정렬 순서)를 정의하는 데이터 클래스입니다.
    """
    field: str = "id"               # 정렬의 기준이 될 필드명
    order: SortOrder = SortOrder.ASC  # 정렬 순서 (오름차순/내림차순)

    # 정렬에 허용되는 필드들을 정의한 클래스 변수입니다.
    # SQL 인젝션 공격을 방지하기 위해, 허용된 필드명만 정렬에 사용하도록 제한합니다.
    ALLOWED_FIELDS = ["id", "filename", "file_type",
                      "file_size", "created_at", "updated_at"]

    def __post_init__(self):
        """객체 초기화 후 실행되어 정렬 필드가 유효한지 검사합니다."""
        if self.field not in self.ALLOWED_FIELDS:
            raise ValueError(
                f"Invalid sort field: {self.field}. Allowed: {self.ALLOWED_FIELDS}")


@dataclass
class PagedResult:
    """
    페이지네이션된 쿼리 결과를 담는 데이터 클래스입니다.
    """
    items: List[Dict[str, Any]]  # 현재 페이지의 항목 리스트
    total_count: int            # 전체 항목 수
    page: int                   # 현재 페이지 번호
    page_size: int              # 페이지당 항목 수
    total_pages: int            # 전체 페이지 수

    @property
    def has_next(self) -> bool:
        """다음 페이지가 존재하는지 여부를 반환합니다."""
        return self.page < self.total_pages

    @property
    def has_previous(self) -> bool:
        """이전 페이지가 존재하는지 여부를 반환합니다."""
        return self.page > 1


class QueryOperations:
    """
    SQLite 데이터베이스에 대해 복잡한 쿼리(필터링, 정렬, 페이지네이션) 및
    통계 조회를 수행하는 메서드를 제공하는 클래스입니다.
    """

    def __init__(self, db_design: DatabaseDesign):
        """
        QueryOperations 클래스의 인스턴스를 초기화합니다.

        Args:
            db_design (DatabaseDesign): 데이터베이스 연결 및 스키마 정보를 담고 있는 객체.
        """
        self.db_design = db_design

    def _build_where_clause(
        self,
        filter_params: Optional[QueryFilter]
    ) -> Tuple[str, List[Any]]:
        """
        필터 조건(QueryFilter)을 기반으로 SQL의 WHERE 절을 동적으로 생성합니다.

        Args:
            filter_params (Optional[QueryFilter]): 필터링 조건을 담은 객체.

        Returns:
            Tuple[str, List[Any]]: 생성된 WHERE 절 문자열과, SQL 쿼리에 바인딩될 파라미터 리스트.
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
        필터링, 정렬, 페이지네이션을 적용하여 데이터베이스를 쿼리합니다.

        Args:
            filter_params (Optional[QueryFilter]): 필터 조건.
            sort_params (Optional[SortParams]): 정렬 조건.
            pagination (Optional[PaginationParams]): 페이지네이션 조건.

        Returns:
            PagedResult: 쿼리 결과를 담은 페이지네이션 객체.
        """
        # 파라미터가 제공되지 않은 경우 기본값을 사용합니다.
        sort_params = sort_params or SortParams()
        pagination = pagination or PaginationParams()

        # WHERE 절과 파라미터를 생성합니다.
        where_clause, where_params = self._build_where_clause(filter_params)

        conn = self.db_design.get_connection()
        try:
            cursor = conn.cursor()

            # 1. 필터 조건에 맞는 전체 항목 수를 조회합니다.
            count_query = f"SELECT COUNT(*) FROM documents {where_clause}"
            cursor.execute(count_query, where_params)
            total_count = cursor.fetchone()[0]

            # 2. 전체 페이지 수를 계산합니다.
            total_pages = (total_count + pagination.page_size -
                           1) // pagination.page_size

            # 3. 실제 데이터를 조회합니다 (정렬, 페이징 적용).
            data_query = f"""
                SELECT * FROM documents
                {where_clause}
                ORDER BY {sort_params.field} {sort_params.order.value}
                LIMIT ? OFFSET ?
            """
            query_params = where_params + [pagination.limit, pagination.offset]
            cursor.execute(data_query, query_params)

            items = [dict(row) for row in cursor.fetchall()]

            # PagedResult 객체로 결과를 포장하여 반환합니다.
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
        지정된 필드들에서 키워드를 사용하여 문서를 검색합니다.

        Args:
            keyword (str): 검색할 키워드.
            search_fields (List[str], optional): 검색을 수행할 필드 목록.
                                                 기본값은 ['filename', 'content'].

        Returns:
            List[Dict[str, Any]]: 검색된 문서들의 리스트.
        """
        search_fields = search_fields or ["filename", "content"]

        # 각 검색 필드에 대해 'LIKE ?' 조건을 생성합니다.
        conditions = [f"{field} LIKE ?" for field in search_fields]
        # OR로 조건들을 연결하여 어느 한 필드라도 일치하면 검색되도록 합니다.
        where_clause = "WHERE " + " OR ".join(conditions)

        # 각 조건에 동일한 키워드 파라미터를 바인딩합니다.
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
        데이터베이스에 대한 다양한 통계 정보를 조회합니다.

        Returns:
            Dict[str, Any]: 통계 정보(총 문서 수, 총 파일 크기, 평균 파일 크기,
                              파일 타입별 분포)를 담은 딕셔너리.
        """
        conn = self.db_design.get_connection()
        try:
            cursor = conn.cursor()

            # 전체 문서 수를 조회합니다.
            cursor.execute("SELECT COUNT(*) FROM documents")
            total_count = cursor.fetchone()[0]

            # 파일 타입별 문서 수를 조회합니다.
            cursor.execute("""
                SELECT file_type, COUNT(*) as count
                FROM documents
                GROUP BY file_type
                ORDER BY count DESC
            """)
            type_distribution = [dict(row) for row in cursor.fetchall()]

            # 모든 문서의 파일 크기 합계를 조회합니다.
            cursor.execute("SELECT SUM(file_size) FROM documents")
            total_size = cursor.fetchone()[0] or 0

            # 평균 파일 크기를 조회합니다.
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


# 이 스크립트가 직접 실행될 때, 아래의 예제 코드를 실행합니다.
if __name__ == "__main__":
    from .db_design import create_database
    from .crud_api import CRUDOperations

    print("=== SQLite 쿼리/페이징/정렬 예제 ===\n")

    # 'test_query' 테넌트용 데이터베이스를 생성하고 샘플 데이터를 추가합니다.
    db_design = create_database("test_query")
    crud = CRUDOperations(db_design)
    query_ops = QueryOperations(db_design)

    print("1. 샘플 데이터 생성")
    for i in range(25):
        crud.create(
            filename=f"file_{i+1}.txt",
            content=f"Content of file {i+1}",
            file_type="text" if i % 2 == 0 else "json",
            file_size=100 + i * 10
        )
    print(f"   {crud.count()}개 문서 생성 완료")

    print("\n2. 페이지네이션 (페이지 1, 크기 10)")
    result = query_ops.query(
        pagination=PaginationParams(page=1, page_size=10)
    )
    print(f"   전체 {result.total_count}개 중 {len(result.items)}개 표시")
    print(f"   전체 페이지: {result.total_pages}")
    print(f"   다음 페이지 존재: {result.has_next}")

    print("\n3. 정렬 (파일명 내림차순)")
    result = query_ops.query(
        sort_params=SortParams(field="filename", order=SortOrder.DESC),
        pagination=PaginationParams(page=1, page_size=5)
    )
    for item in result.items:
        print(f"   - {item['filename']}")

    print("\n4. 필터링 (파일 타입: text)")
    result = query_ops.query(
        filter_params=QueryFilter(file_type="text"),
        pagination=PaginationParams(page=1, page_size=5)
    )
    print(f"   text 타입 문서: {result.total_count}개")

    print("\n5. 검색 (키워드: 'file_1')")
    results = query_ops.search(keyword="file_1")
    print(f"   검색 결과: {len(results)}개")
    for item in results:
        print(f"   - {item['filename']}")

    print("\n6. 통계 정보")
    stats = query_ops.get_statistics()
    print(f"   전체 문서 수: {stats['total_count']}")
    print(f"   전체 크기: {stats['total_size']} bytes")
    print(f"   평균 크기: {stats['average_size']} bytes")
    print("   타입별 분포:")
    for dist in stats['type_distribution']:
        print(f"      - {dist['file_type']}: {dist['count']}개")
