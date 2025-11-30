#!/usr/bin/env python3
"""Backend Server for Tenant B - SQLite WAL mode"""
# =============================================================================
# Backend B - 테넌트 B 전용 백엔드 서버
# =============================================================================
# 역할: SQLite DB를 사용하여 CRUD 작업 수행
# 통신: stdin/stdout으로 JSON-RPC 메시지 수신/응답
# 보안: Proxy Server에서만 호출됨 (직접 외부 접근 불가)
# =============================================================================

import sqlite3, json, sys, os  # sqlite3: DB, json: 메시지 파싱, sys: stdin/stdout, os: 환경변수
from pathlib import Path  # 파일 경로 처리

# DB 파일 경로 - 환경변수 또는 기본값 사용
DB_PATH = os.getenv("DB_PATH", str(Path(__file__).parent.parent / "data" / "tenant_b.db"))

def init_db():
    """DB 초기화 함수 - 테이블 생성"""
    Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)  # 상위 디렉토리 생성
    conn = sqlite3.connect(DB_PATH)  # DB 연결
    conn.execute("PRAGMA journal_mode=WAL")  # WAL 모드: 동시 읽기/쓰기 성능 향상
    conn.execute("CREATE TABLE IF NOT EXISTS items (id INTEGER PRIMARY KEY, name TEXT, value TEXT)")  # 테이블 생성
    conn.commit()  # 변경사항 저장
    conn.close()  # 연결 종료

def handle(req):
    """요청 처리 함수 - method에 따라 CRUD 수행"""
    method, params = req.get("method", ""), req.get("params", {})  # 요청에서 메서드와 파라미터 추출
    conn = sqlite3.connect(DB_PATH)  # DB 연결
    conn.execute("PRAGMA journal_mode=WAL")  # WAL 모드 활성화
    cur = conn.cursor()  # 커서 생성
    try:
        if method == "insert":  # INSERT 요청
            cur.execute("INSERT INTO items (name, value) VALUES (?, ?)", (params.get("name"), params.get("value")))  # ? = 파라미터 바인딩 (SQL Injection 방지)
            conn.commit()
            return {"result": {"status": "inserted", "id": cur.lastrowid}}  # 삽입된 ID 반환
        elif method == "update":  # UPDATE 요청
            cur.execute("UPDATE items SET value=? WHERE id=?", (params.get("value"), params.get("id")))
            conn.commit()
            return {"result": {"status": "updated", "rows": cur.rowcount}}  # 수정된 행 수 반환
        elif method == "select":  # SELECT 요청
            cur.execute("SELECT id, name, value FROM items")
            return {"result": [{"id": r[0], "name": r[1], "value": r[2]} for r in cur.fetchall()]}  # 리스트 컴프리헨션으로 결과 변환
        return {"error": f"Unknown method: {method}"}  # 알 수 없는 메서드
    except Exception as e:
        return {"error": str(e)}  # 예외 발생 시 에러 반환
    finally:
        conn.close()  # 항상 연결 종료

# =============================================================================
# 메인 실행부 - stdin에서 JSON-RPC 요청을 읽고 stdout으로 응답
# =============================================================================
if __name__ == "__main__":
    init_db()  # DB 초기화
    for line in sys.stdin:  # stdin에서 한 줄씩 읽기 (Proxy Server에서 전송)
        try:
            req = json.loads(line.strip())  # JSON 파싱
            resp = handle(req)  # 요청 처리
            resp.update({"jsonrpc": "2.0", "id": req.get("id", 1)})  # JSON-RPC 형식으로 응답 구성
            print(json.dumps(resp), flush=True)  # stdout으로 응답 (flush=True: 즉시 전송)
        except Exception as e:
            print(json.dumps({"jsonrpc": "2.0", "error": str(e), "id": 1}), flush=True)  # 에러 응답
