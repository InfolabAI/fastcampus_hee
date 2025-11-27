#!/usr/bin/env python3
"""Backend Server for Tenant B - SQLite WAL mode"""
import sqlite3, json, sys, os
from pathlib import Path

DB_PATH = os.getenv("DB_PATH", str(Path(__file__).parent.parent / "data" / "tenant_b.db"))

def init_db():
    Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("CREATE TABLE IF NOT EXISTS items (id INTEGER PRIMARY KEY, name TEXT, value TEXT)")
    conn.commit()
    conn.close()

def handle(req):
    method, params = req.get("method", ""), req.get("params", {})
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL")
    cur = conn.cursor()
    try:
        if method == "insert":
            cur.execute("INSERT INTO items (name, value) VALUES (?, ?)", (params.get("name"), params.get("value")))
            conn.commit()
            return {"result": {"status": "inserted", "id": cur.lastrowid}}
        elif method == "update":
            cur.execute("UPDATE items SET value=? WHERE id=?", (params.get("value"), params.get("id")))
            conn.commit()
            return {"result": {"status": "updated", "rows": cur.rowcount}}
        elif method == "select":
            cur.execute("SELECT id, name, value FROM items")
            return {"result": [{"id": r[0], "name": r[1], "value": r[2]} for r in cur.fetchall()]}
        return {"error": f"Unknown method: {method}"}
    except Exception as e:
        return {"error": str(e)}
    finally:
        conn.close()

if __name__ == "__main__":
    init_db()
    for line in sys.stdin:
        try:
            req = json.loads(line.strip())
            resp = handle(req)
            resp.update({"jsonrpc": "2.0", "id": req.get("id", 1)})
            print(json.dumps(resp), flush=True)
        except Exception as e:
            print(json.dumps({"jsonrpc": "2.0", "error": str(e), "id": 1}), flush=True)
