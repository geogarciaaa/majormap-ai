"""Wiring tests for the sections API — run without a real PostgreSQL.

Substitutes a fake connection so we can verify: SQL parameterization, the
loose term filter, Decimal->float conversion, and the response envelope.

    python3 test_api.py
"""

from decimal import Decimal

import main
from fastapi.testclient import TestClient


class FakeCursor:
    def __init__(self, rows):
        self.rows = rows
        self.executed = []

    def execute(self, query, params=None):
        self.executed.append((" ".join(query.split()), params))
        self.last_query = query

    def fetchone(self):
        if "metadata" in self.last_query:
            return {"value": "Fall 2026"}
        return {"n": len(self.rows)}

    def fetchall(self):
        return self.rows

    def close(self):
        pass


class FakeConn:
    def __init__(self, rows):
        self.cur = FakeCursor(rows)

    def cursor(self, cursor_factory=None):
        return self.cur

    def close(self):
        pass


ROWS = [
    {
        "subject_code": "CS", "course_number": "171", "title": "Computer Programming I",
        "credits": "3.0", "crn": 12345, "section": "A", "instruction_type": "Lecture",
        "instruction_method": "Face To Face", "prereqs": "", "max_enroll": "30",
        "enroll": "12", "days": ["Monday", "Wednesday"], "start_time": "10:00",
        "end_time": "11:50", "building": None, "room": None,
        "instructor_name": "Ada Lovelace", "rating": Decimal("4.5"),
        "difficulty": Decimal("2.5"), "num_ratings": 42, "rmp_id": 999,
    }
]


def run():
    conn_holder = {}

    def fake_get_conn():
        conn_holder["conn"] = FakeConn(list(ROWS))
        return conn_holder["conn"]

    main.get_db_connection = fake_get_conn
    client = TestClient(main.app)

    # 1) plain fetch returns envelope + term + float rating
    r = client.get("/api/sections").json()
    assert r["status"] == "success" and r["count"] == 1, r
    assert r["term"] == "Fall 2026"
    assert isinstance(r["data"][0]["rating"], float) and r["data"][0]["rating"] == 4.5
    assert r["data"][0]["days"] == ["Monday", "Wednesday"]

    # 2) filters are parameterized (no string interpolation)
    client.get("/api/sections", params={"subject": "CS", "course_number": "171"})
    q, params = conn_holder["conn"].cur.executed[-1]
    assert "ILIKE %s" in q and params == ("CS", "171"), (q, params)
    assert "'CS'" not in q, "subject must not be interpolated into SQL"

    # 3) loose term matching: substring, case-insensitive — opaque to format
    assert client.get("/api/sections", params={"term": "fall"}).json()["count"] == 1
    assert client.get("/api/sections", params={"term": "2026"}).json()["count"] == 1
    r = client.get("/api/sections", params={"term": "Winter 2027"}).json()
    assert r["count"] == 0 and "Fall 2026" in r["detail"]

    # 4) health endpoint
    h = client.get("/api/health").json()
    assert h["status"] == "ok" and h["term"] == "Fall 2026" and h["sections"] == 1

    print("ALL BACKEND TESTS PASSED")


if __name__ == "__main__":
    run()
