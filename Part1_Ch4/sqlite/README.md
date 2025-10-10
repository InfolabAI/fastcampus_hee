# Part1 Ch4 - SQLite API 구현

멀티테넌시를 지원하는 SQLite 데이터베이스 API 모듈입니다.

## 📚 커리큘럼 구조

| 번호 | 파일명 | 설명 | 시간 |
|------|--------|------|------|
| 4-6 | `db_design.py` | 데이터를 저장하는 작은 데이터베이스 설계하기 | 7분 |
| 4-7 | `crud_api.py` | 데이터를 추가, 조회, 수정, 삭제하는 기능 만들기 | 8분 |
| 4-8 | `query_api.py` | 원하는 데이터만 골라보고 나눠보는 기능 만들기 | 8분 |
| 4-9 | `file_to_db_pipeline.py` | 파일 내용을 데이터베이스에 자동으로 옮겨 담기 | 10분 |
| 4-10 | `db_to_file_report.py` | 데이터베이스 내용을 파일로 깔끔하게 정리하기 | 7분 |
| 4-11 | `checklist.py` | 지금까지 만든 모든 기능이 잘 작동하는지 확인하기 | 2분 |

## 📦 파일 구조 및 설명

### 1. `db_design.py` - 데이터베이스 설계 (4-6)

**의미**: SQLite 데이터베이스의 기본 구조와 스키마를 설계합니다.

**주요 기능**:
- `DatabaseConfig`: 데이터베이스 설정 클래스
- `DatabaseDesign`: 스키마 정의 및 초기화
- `create_database()`: 데이터베이스 생성 헬퍼 함수

**실행 예제**:
```bash
cd Part1_Ch4/sqlite
python db_design.py
```

**실행 의미**:
- 테넌트별로 독립된 데이터베이스 파일 생성
- 문서 저장을 위한 테이블 및 인덱스 생성
- 스키마 정보 확인

**커리큘럼 활용법**:
- 데이터베이스 설계의 기본 개념 학습
- 멀티테넌시 아키텍처 이해
- SQLite 스키마 작성법 실습

---

### 2. `crud_api.py` - CRUD 작업 (4-7)

**의미**: Create, Read, Update, Delete의 기본적인 데이터 조작 기능을 구현합니다.

**주요 기능**:
- `create()`: 문서 생성
- `read()`: 문서 조회
- `update()`: 문서 수정
- `delete()`: 문서 삭제
- `read_all()`: 전체 문서 조회

**실행 예제**:
```bash
python crud_api.py
```

**실행 의미**:
- 문서를 데이터베이스에 추가
- 저장된 문서 내용 조회
- 문서 정보 업데이트
- 불필요한 문서 삭제

**커리큘럼 활용법**:
- 데이터베이스의 기본 CRUD 작업 학습
- SQL 쿼리 작성법 이해
- 트랜잭션 처리 실습

---

### 3. `query_api.py` - 쿼리/페이징/정렬 (4-8)

**의미**: 데이터를 효율적으로 검색하고 정렬하는 고급 쿼리 기능을 구현합니다.

**주요 기능**:
- `QueryFilter`: 필터링 조건 정의
- `PaginationParams`: 페이지네이션 설정
- `SortParams`: 정렬 파라미터
- `query()`: 필터링, 정렬, 페이징을 적용한 쿼리
- `search()`: 키워드 검색
- `get_statistics()`: 통계 정보 조회

**실행 예제**:
```bash
python query_api.py
```

**실행 의미**:
- 대량의 데이터를 페이지 단위로 나눠서 조회
- 특정 조건에 맞는 데이터만 필터링
- 원하는 기준으로 데이터 정렬
- 데이터베이스 통계 확인

**커리큘럼 활용법**:
- WHERE, ORDER BY, LIMIT 쿼리 학습
- 페이지네이션 구현 방법 이해
- 데이터 집계 및 통계 처리 실습

---

### 4. `file_to_db_pipeline.py` - 파일→SQLite 파이프라인 (4-9)

**의미**: 파일 시스템의 파일들을 자동으로 데이터베이스에 적재하는 파이프라인을 구현합니다.

**주요 기능**:
- `load_file()`: 단일 파일 적재
- `load_directory()`: 디렉토리 일괄 적재
- `load_files()`: 여러 파일 적재
- `update_file()`: 파일 내용으로 문서 업데이트

**실행 예제**:
```bash
python file_to_db_pipeline.py
```

**실행 의미**:
- 로컬 파일을 데이터베이스에 자동 저장
- 디렉토리의 모든 파일을 일괄 처리
- 파일 메타데이터 자동 추출
- 중복 파일 처리

**커리큘럼 활용법**:
- ETL (Extract, Transform, Load) 파이프라인 개념 학습
- 파일 I/O와 데이터베이스 연동
- 대량 데이터 처리 방법 실습

---

### 5. `db_to_file_report.py` - SQLite→파일 리포트 (4-10)

**의미**: 데이터베이스의 내용을 다양한 형식의 파일로 출력하여 리포트를 생성합니다.

**주요 기능**:
- `export_to_json()`: JSON 형식 출력
- `export_to_csv()`: CSV 형식 출력
- `export_to_markdown()`: Markdown 형식 출력
- `export_to_text()`: 텍스트 형식 출력

**실행 예제**:
```bash
python db_to_file_report.py
```

**실행 의미**:
- 데이터베이스 내용을 JSON으로 내보내기
- CSV로 변환하여 엑셀에서 분석 가능
- Markdown으로 읽기 쉬운 리포트 생성
- 통계 정보 포함 리포트 작성

**커리큘럼 활용법**:
- 데이터 내보내기 (Export) 기능 학습
- 다양한 파일 형식 처리 방법 이해
- 리포트 자동화 실습

---

### 6. `checklist.py` - 종합 점검 체크리스트 (4-11)

**의미**: 모든 기능이 정상적으로 작동하는지 자동으로 테스트합니다.

**주요 기능**:
- `SQLiteChecklist`: 전체 기능 테스트 클래스
- `run_all_checks()`: 모든 체크리스트 실행
- 각 모듈별 통합 테스트

**실행 예제**:
```bash
python checklist.py
```

**실행 의미**:
- 데이터베이스 설계부터 리포트 생성까지 전 과정 테스트
- 각 기능의 정상 작동 여부 확인
- 테스트 결과를 JSON 파일로 저장
- 성공/실패 통계 제공

**커리큘럼 활용법**:
- 자동화된 테스트 작성 방법 학습
- 통합 테스트 개념 이해
- 품질 보증(QA) 프로세스 실습

---

## 🚀 MCP 서버 구현

### `mcp_server.py` - MCP 서버

**의미**: 모든 SQLite 기능을 MCP(Model Context Protocol) 도구로 제공하는 서버입니다.

**주요 도구**:
- **데이터베이스 관리**: `init_database`, `get_schema_info`
- **CRUD 작업**: `create_document`, `read_document`, `update_document`, `delete_document`, `list_documents`
- **쿼리**: `query_documents`, `search_documents`, `get_statistics`
- **파일 적재**: `load_file_to_db`, `load_directory_to_db`
- **리포트 생성**: `export_to_json`, `export_to_csv`, `export_to_markdown`

**실행 방법**:
```bash
python -m Part1_Ch4.sqlite.mcp_server
```

**실행 의미**:
- FastMCP 프레임워크를 사용한 MCP 서버 시작
- AI 에이전트가 SQLite 기능을 도구로 사용 가능
- 표준 입출력(stdio)을 통한 통신

**커리큘럼 활용법**:
- MCP 프로토콜의 이해
- AI와 데이터베이스 연동 방법 학습
- 비동기 프로그래밍 실습

---

### `test_mcp_server.py` - MCP 서버 테스트

**의미**: MCP 서버의 모든 도구를 실제로 호출하여 테스트합니다.

**테스트 항목**:
1. 데이터베이스 초기화 및 스키마 조회
2. CRUD 작업 (생성, 조회, 수정, 삭제)
3. 쿼리/페이징/정렬/검색/통계
4. 파일→SQLite 파이프라인
5. SQLite→파일 리포트
6. 멀티테넌시 격리 확인

**실행 방법**:
```bash
python test_mcp_server.py
```

**실행 의미**:
- MCP 클라이언트로 서버 연결
- 모든 도구 순차적으로 테스트
- 각 기능의 정상 작동 확인
- 테스트 워크스페이스 자동 정리

**커리큘럼 활용법**:
- MCP 클라이언트 사용법 학습
- E2E(End-to-End) 테스트 작성
- 실제 사용 시나리오 시뮬레이션

---

## 🎯 커리큘럼 활용 가이드

### 기본 학습 순서

1. **기초 단계** (4-6 ~ 4-7)
   - `db_design.py`로 데이터베이스 설계 개념 학습
   - `crud_api.py`로 기본 CRUD 작업 실습

2. **중급 단계** (4-8 ~ 4-9)
   - `query_api.py`로 고급 쿼리 기법 학습
   - `file_to_db_pipeline.py`로 데이터 파이프라인 구축

3. **고급 단계** (4-10 ~ 4-11)
   - `db_to_file_report.py`로 리포트 생성 자동화
   - `checklist.py`로 전체 시스템 검증

4. **실전 단계** (MCP 서버)
   - `mcp_server.py`로 MCP 서버 구축
   - `test_mcp_server.py`로 실전 테스트

### 실습 시나리오

#### 시나리오 1: 문서 관리 시스템 구축
```bash
# 1. 데이터베이스 생성
python db_design.py

# 2. 문서 추가/조회/수정
python crud_api.py

# 3. 문서 검색 및 정렬
python query_api.py
```

#### 시나리오 2: 파일 백업 시스템
```bash
# 1. 로컬 파일들을 데이터베이스에 백업
python file_to_db_pipeline.py

# 2. 백업된 데이터를 다양한 형식으로 리포트 생성
python db_to_file_report.py
```

#### 시나리오 3: AI 에이전트 연동
```bash
# 1. MCP 서버 실행
python -m Part1_Ch4.sqlite.mcp_server

# 2. 테스트 클라이언트 실행 (다른 터미널)
python test_mcp_server.py
```

---

## 🔑 핵심 개념

### 멀티테넌시 (Multi-tenancy)
- 각 테넌트(tenant)별로 독립된 데이터베이스 파일 사용
- `tenant_id`를 기반으로 데이터 격리
- 확장 가능한 아키텍처 설계

### 모듈화 설계
- 각 기능을 독립된 모듈로 분리
- MCP 서버에서 쉽게 import하여 사용
- 재사용성과 유지보수성 향상

### 비동기 처리
- FastMCP의 비동기 도구 활용
- `asyncio.run_in_executor()`로 동기 함수를 비동기로 래핑
- 효율적인 I/O 처리

---

## 📊 실행 결과 예시

### CRUD 작업 결과
```
=== SQLite CRUD 작업 예제 ===

1. 문서 생성
   생성된 문서 ID: 1
   생성된 문서 ID: 2

2. 문서 조회
   문서 1: example.txt - Hello, World!...

3. 전체 문서 조회
   전체 문서 수: 2
   - ID 1: example.txt
   - ID 2: data.json
```

### 쿼리/페이징 결과
```
=== SQLite 쿼리/페이징/정렬 예제 ===

2. 페이지네이션 (페이지 1, 크기 10)
   전체 25개 중 10개 표시
   전체 페이지: 3
   다음 페이지 존재: True
```

### MCP 테스트 결과
```
================================================================================
SQLite API MCP Server Test Started
================================================================================

[1] 데이터베이스 초기화 (4-6)
   Status: success
   DB Path: /path/to/test.db
   Tables: 1

[2] CRUD 작업 (4-7)
   2-1. Create - 문서 생성
      Created document ID: 1
      Created 4 more documents
   ...
```

---

## 🛠️ 기술 스택

- **Python 3.8+**: 기본 언어
- **SQLite3**: 내장 데이터베이스
- **FastMCP**: MCP 서버 프레임워크
- **asyncio**: 비동기 처리
- **pathlib**: 파일 경로 처리
- **json/csv**: 데이터 포맷 처리

---

## 📝 추가 학습 자료

### SQLite 심화
- [SQLite 공식 문서](https://www.sqlite.org/docs.html)
- 트랜잭션 처리
- 인덱스 최적화
- Full-Text Search

### MCP 프로토콜
- [Model Context Protocol 사양](https://modelcontextprotocol.io)
- 도구(Tool) 설계 패턴
- 클라이언트-서버 통신

### 확장 가능성
- PostgreSQL/MySQL 등 다른 데이터베이스로 확장
- 벡터 데이터베이스 연동
- 분산 데이터베이스 시스템

---

## ⚠️ 주의사항

1. **데이터베이스 파일 경로**: 상대 경로 사용 시 작업 디렉토리 확인 필요
2. **멀티테넌시**: 프로덕션 환경에서는 추가 보안 고려 필요
3. **동시성**: SQLite는 쓰기 동시성이 제한적 (필요시 다른 DB 고려)
4. **백업**: 중요 데이터는 정기적인 백업 필요

---

## 🐛 트러블슈팅 가이드

### 문제 1: MCP 서버 실행 시 "ModuleNotFoundError: No module named 'Part1_Ch4'" 발생

**문제 상황**:
```bash
python test_mcp_server.py
# 에러: ModuleNotFoundError: No module named 'Part1_Ch4'
```

**원인**:
- Python이 프로젝트 루트 디렉토리를 모듈 경로로 인식하지 못함
- `Part1_Ch4.sqlite.mcp_server` 모듈을 찾을 수 없음

**해결 방법**:
`test_mcp_server.py`가 자동으로 PYTHONPATH를 설정하도록 수정되었습니다:
```python
import sys
import pathlib

# PYTHONPATH 설정 - 프로젝트 루트를 추가
project_root = pathlib.Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
```

서브프로세스(MCP 서버)에도 PYTHONPATH를 전달:
```python
env = os.environ.copy()
env['PYTHONPATH'] = str(project_root)

transport = StdioTransport(
    command="python",
    args=["-m", "Part1_Ch4.sqlite.mcp_server"],
    env=env
)
```

**검증 방법**:
```bash
cd Part1_Ch4/sqlite
python test_mcp_server.py  # 정상 실행되어야 함
```

---

### 문제 2: MCP 서버 통신 중 "Failed to parse JSONRPC message from server" 에러

**문제 상황**:
```bash
python test_mcp_server.py

# 에러 메시지:
Failed to parse JSONRPC message from server
Traceback (most recent call last):
  ...
pydantic_core._pydantic_core.ValidationError: 1 validation error for JSONRPCMessage
  Invalid JSON: expected value at line 1 column 1
  input_value='Starting SQLite API MCP Server...'
```

**원인**:
- MCP는 stdio(표준 입출력)를 사용하여 JSONRPC 프로토콜로 통신
- `mcp_server.py`에 있던 `print()` 문들이 stdout으로 출력됨
- 이 출력이 JSONRPC 메시지와 섞여서 프로토콜 파싱 실패
- 예시: `print(f"Initializing database for tenant: {tenant_id}")` 같은 디버그 메시지들

**해결 방법**:
`mcp_server.py`에서 모든 `print()` 문 제거:
```python
# 제거 전 (잘못된 코드):
@mcp.tool()
async def init_database(tenant_id: str, db_path: str = None) -> dict:
    print(f"Initializing database for tenant: {tenant_id}")  # ❌ 제거해야 함
    ...

# 제거 후 (올바른 코드):
@mcp.tool()
async def init_database(tenant_id: str, db_path: str = None) -> dict:
    # print 문 없음 ✅
    loop = asyncio.get_event_loop()
    ...
```

**제거된 print 문 목록** (총 15개):
1. `print("Starting SQLite API MCP Server...")`
2. `print(f"Initializing database for tenant: {tenant_id}")`
3. `print(f"Getting schema info for tenant: {tenant_id}")`
4. `print(f"Creating document: {filename} for tenant: {tenant_id}")`
5. `print(f"Reading document {document_id} for tenant: {tenant_id}")`
6. `print(f"Updating document {document_id} for tenant: {tenant_id}")`
7. `print(f"Deleting document {document_id} for tenant: {tenant_id}")`
8. `print(f"Listing all documents for tenant: {tenant_id}")`
9. `print(f"Querying documents for tenant: {tenant_id}")`
10. `print(f"Searching documents for '{keyword}' in tenant: {tenant_id}")`
11. `print(f"Getting statistics for tenant: {tenant_id}")`
12. `print(f"Loading file {file_path} to database for tenant: {tenant_id}")`
13. `print(f"Loading directory {directory_path} to database for tenant: {tenant_id}")`
14. `print(f"Exporting to JSON: {output_path} for tenant: {tenant_id}")`
15. `print(f"Exporting to CSV: {output_path} for tenant: {tenant_id}")`
16. `print(f"Exporting to Markdown: {output_path} for tenant: {tenant_id}")`

**검증 방법**:
```bash
cd Part1_Ch4/sqlite
python test_mcp_server.py

# 에러 없이 정상 실행되어야 함:
# ================================================================================
# SQLite API MCP Server Test Started
# ================================================================================
# [1] 데이터베이스 초기화 (4-6)
#    Status: success
#    ...
```

**중요 원칙**:
- MCP 서버에서는 **절대 stdout에 print 하지 말 것**
- 디버깅이 필요하면 stderr 또는 로그 파일 사용:
  ```python
  import sys
  print("Debug message", file=sys.stderr)  # stderr로 출력

  # 또는 logging 사용
  import logging
  logging.basicConfig(filename='mcp_server.log')
  logging.info("Debug message")
  ```

---

### 문제 3: Docker 컨테이너 내에서 Conda 환경 충돌

**문제 상황**:
```bash
(base) vscode@container:/workspaces/fastcampus/Part1_Ch4/sqlite$ python test_mcp_server.py
ModuleNotFoundError: No module named 'fastmcp'
```

**원인**:
- `docker-compose.yaml`에서 호스트의 `$HOME` 디렉토리를 컨테이너에 마운트
- 호스트의 conda 환경 설정이 컨테이너로 복사됨
- 컨테이너의 시스템 Python 대신 conda의 Python이 활성화됨
- Conda 환경에는 필요한 패키지가 설치되어 있지 않음

**해결 방법**:
`docker-compose.yaml` 수정:
```yaml
# 수정 전 (문제 있는 설정):
volumes:
  - ${HOME}:${HOME}  # ❌ 호스트 홈 디렉토리 마운트
  - .:/workspaces/fastcampus

environment:
  - HOME=${HOME}  # ❌ 호스트 홈 경로 사용

# 수정 후 (올바른 설정):
volumes:
  - .:/workspaces/fastcampus  # ✅ 프로젝트 디렉토리만 마운트

environment:
  - HOME=/home/vscode  # ✅ 컨테이너 내부 홈 경로 사용
```

**적용 방법**:
```bash
# 컨테이너에서 나가기
exit

# Docker 재시작
make down
make up
make exec

# conda 환경 확인
echo $HOME  # /home/vscode 이어야 함
which python  # /usr/local/bin/python 이어야 함 (conda 아님)
```

**검증 방법**:
```bash
cd Part1_Ch4/sqlite
python test_mcp_server.py  # 정상 작동해야 함
```

---

### 문제 4: 테스트 스크립트 조기 종료

**문제 상황**:
```bash
bash test_all.sh
# 첫 번째 테스트 후 스크립트가 종료됨
```

**원인 1**: `trap cleanup EXIT` 사용
- EXIT 트랩이 모든 명령 실행 후 cleanup 호출
- 첫 번째 테스트 후 바로 종료됨

**원인 2**: `set -e` 플래그
- 테스트 중 하나라도 실패하면 스크립트 전체 종료
- 일부 테스트 실패를 허용하고 계속 진행하지 못함

**해결 방법**:
```bash
# 수정 전:
set -e  # ❌ 에러 시 즉시 종료
trap cleanup EXIT  # ❌ 모든 명령 후 cleanup 실행

# 수정 후:
# set -e  # ✅ 주석처리하여 비활성화

# 각 테스트 함수에서 명시적으로 return 0
test_db_design() {
    # ... 테스트 코드 ...
    return 0  # ✅ 항상 성공 반환
}

# main 함수에서만 cleanup 호출
main() {
    # ... 모든 테스트 실행 ...
    cleanup  # ✅ 마지막에만 정리
}
```

---

### 문제 5: `bc` 명령어를 찾을 수 없음

**문제 상황**:
```bash
bash test_all.sh
# test_all.sh: line 221: bc: command not found
```

**원인**:
- `bc` 계산기 유틸리티가 컨테이너에 설치되어 있지 않음
- 체크리스트 성공률 계산에 사용되었음

**해결 방법**:
`bc` 대신 `awk` 사용 (기본 설치됨):
```bash
# 수정 전:
if (( $(echo "$SUCCESS_RATE >= 90" | bc -l) )); then
    print_pass "Checklist success rate: ${SUCCESS_RATE}%"
fi

# 수정 후:
if awk "BEGIN {exit !($SUCCESS_RATE >= 90)}"; then
    print_pass "Checklist success rate: ${SUCCESS_RATE}%"
fi
```

---

### 문제 6: SQLite CLI 도구 누락으로 스키마 검증 실패

**문제 상황**:
```bash
bash test_all.sh
# [FAIL] Database schema not created
# [FAIL] Database indexes not created
# [FAIL] No documents created by CRUD operations
```

**원인**:
- `sqlite3` CLI 도구가 Docker 이미지에 설치되어 있지 않음
- 테스트 스크립트가 `sqlite3 data/tenant1.db ".schema documents"` 명령으로 스키마 검증
- 명령어 실패로 모든 데이터베이스 관련 테스트 실패

**해결 방법**:
`.devcontainer/Dockerfile.integrated` 수정:
```dockerfile
RUN sudo apt-get update && export DEBIAN_FRONTEND=noninteractive \
    && sudo apt-get -y install --no-install-recommends \
    git docker.io \
    curl jq \
    nmap \
    sqlite3 \  # ✅ SQLite CLI 도구 추가
    && sudo usermod -aG docker vscode \
```

**적용 방법**:
```bash
# 컨테이너 재빌드
exit
make down
make up
make exec

# 확인
which sqlite3  # /usr/bin/sqlite3 출력되어야 함
sqlite3 --version  # 버전 정보 출력되어야 함
```

---

### 테스트 자동화 스크립트 (`test_all.sh`)

**목적**: 모든 SQLite 모듈의 올바른 구현 검증

**테스트 항목**:
1. 모듈 import 테스트
2. 데이터베이스 설계 (db_design.py)
3. CRUD 작업 (crud_api.py)
4. 쿼리/페이징/정렬 (query_api.py)
5. 파일→DB 파이프라인 (file_to_db_pipeline.py)
6. DB→파일 리포트 (db_to_file_report.py)
7. 체크리스트 검증 (checklist.py)
8. MCP 서버 (mcp_server.py)
9. 에러 처리 및 멀티테넌시

**실행 방법**:
```bash
cd Part1_Ch4/sqlite
bash test_all.sh
```

**결과 로그 저장**:
```bash
bash test_all.sh 2>&1 | tee test_results.log
```

---

## 📞 문의 및 피드백

커리큘럼 관련 문의사항이나 개선 제안은 이슈를 통해 제출해주세요.
