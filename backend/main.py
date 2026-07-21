"""MajorMap AI — Live Data API.

A lightweight FastAPI layer that serves Drexel Term Master Schedule data out of
the PostgreSQL database (`schedulerdb`) populated by the community
drexel-scraper (https://github.com/Zohair-coder/drexel-scraper).

Run it with:
    pip install -r requirements.txt
    uvicorn main:app --reload

Interactive docs: http://localhost:8000/docs

NOTE ON SCHEMA — this is written against the scraper's *actual* schema
(src/create_tables.sql in the scraper repo), which differs from a classic
courses/sections split:
  * there is no `sections` table — each row of `courses` IS one section,
    keyed by `crn` (INTEGER PRIMARY KEY);
  * the junction table is `course_instructor(course_id -> courses.crn,
    instructor_id -> instructors.id)`;
  * instructor ratings are cached RateMyProfessors values on `instructors`
    (`avg_rating`, `avg_difficulty`, `num_ratings`, `rmp_id`);
  * the term is not a column — the scraper stores one term per scrape in the
    `metadata` table (`current_term`, e.g. "Fall 2026");
  * `building` / `room` are not scraped (yet) — returned as NULL so the
    response shape is stable for when they land.

NOTE ON TERMS — Drexel is expected to transition from quarters to semesters
in August 2027, so term codes will change format. Term values are therefore
treated as opaque strings end-to-end: no parsing, no format assumptions —
filtering is a case-insensitive substring match against the stored term.
"""

import os

import psycopg2
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from psycopg2.extras import RealDictCursor

app = FastAPI(title="MajorMap AI Live Data API")

# CORS: locked to the production site plus local development origins.
# Override/extend with a comma-separated ALLOWED_ORIGINS env var.
# ("null" is the Origin browsers send when app.html is opened from file://.)
DEFAULT_ORIGINS = (
    "https://majormapai.com,https://www.majormapai.com,"
    "https://geogarciaaa.github.io,"
    "http://localhost:3000,http://127.0.0.1:3000,"
    "http://localhost:8000,http://127.0.0.1:8000,null"
)
ALLOWED_ORIGINS = [
    o.strip() for o in os.getenv("ALLOWED_ORIGINS", DEFAULT_ORIGINS).split(",") if o.strip()
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_methods=["GET"],
    allow_headers=["*"],
)


def get_db_connection():
    """Connect to the scraper's PostgreSQL database.

    Two configuration styles are supported:
      * DATABASE_URL — the single connection string that managed hosts
        (Render, Railway, Fly, Heroku) inject automatically; takes precedence.
      * discrete DB_HOST / DB_NAME / DB_USER / DB_PASSWORD / DB_PORT vars,
        with defaults mirroring the scraper's local Docker setup.
    """
    try:
        dsn = os.getenv("DATABASE_URL")
        if dsn:
            return psycopg2.connect(dsn)
        return psycopg2.connect(
            host=os.getenv("DB_HOST", "localhost"),
            database=os.getenv("DB_NAME", "schedulerdb"),
            user=os.getenv("DB_USER", "postgres"),
            password=os.getenv("DB_PASSWORD", "super-secret-password"),
            port=os.getenv("DB_PORT", "5432"),
        )
    except Exception as e:  # pragma: no cover - depends on local environment
        print(f"Database connection error: {e}")
        return None


def get_current_term(cursor) -> str | None:
    """Read the term of the data currently in the DB (one term per scrape)."""
    cursor.execute("SELECT value FROM metadata WHERE key = 'current_term'")
    row = cursor.fetchone()
    return row["value"] if row else None


@app.get("/api/health")
def health():
    """Cheap liveness probe the frontend uses to decide live-vs-sample mode."""
    conn = get_db_connection()
    if not conn:
        return {"status": "degraded", "database": "unreachable"}
    try:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        term = get_current_term(cursor)
        cursor.execute("SELECT COUNT(*) AS n FROM courses")
        n = cursor.fetchone()["n"]
        return {"status": "ok", "term": term, "sections": n}
    finally:
        conn.close()


@app.get("/api/sections")
def get_sections(
    term: str = Query(None, description="Term filter, matched loosely (e.g. 'Fall 2026', '2026', 'fall'). Opaque string — format-agnostic to survive the 2027 semester transition."),
    subject: str = Query(None, description="Subject code (e.g. 'CS')"),
    course_number: str = Query(None, description="Course number (e.g. '171')"),
):
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")

    try:
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        current_term = get_current_term(cursor)

        # Term filter: the DB holds exactly one term at a time, so filtering is
        # a loose, case-insensitive substring match against that stored term.
        # Treating it as an opaque string means quarter codes today and
        # semester codes after Aug 2027 both work with zero code changes.
        if term and current_term and term.lower() not in current_term.lower():
            return {
                "status": "success",
                "count": 0,
                "term": current_term,
                "detail": f"No data for term filter '{term}' — database currently holds '{current_term}'.",
                "data": [],
            }

        # One row per (section, instructor). The frontend groups rows by CRN
        # back into a single section with an instructors array.
        # building/room are not in the scraper schema yet — NULL placeholders
        # keep the response shape stable for when they are.
        query = """
            SELECT c.subject_code,
                   c.course_number,
                   c.course_title      AS title,
                   c.credits,
                   c.crn,
                   c.section,
                   c.instruction_type,
                   c.instruction_method,
                   c.prereqs,
                   c.max_enroll,
                   c.enroll,
                   c.days,
                   to_char(c.start_time, 'HH24:MI') AS start_time,
                   to_char(c.end_time,   'HH24:MI') AS end_time,
                   NULL                AS building,
                   NULL                AS room,
                   i.name              AS instructor_name,
                   i.avg_rating        AS rating,
                   i.avg_difficulty    AS difficulty,
                   i.num_ratings,
                   i.rmp_id
            FROM courses c
            LEFT JOIN course_instructor ci ON c.crn = ci.course_id
            LEFT JOIN instructors i        ON ci.instructor_id = i.id
            WHERE 1=1
        """
        params: list[str] = []

        if subject:
            query += " AND c.subject_code ILIKE %s"
            params.append(subject)
        if course_number:
            query += " AND c.course_number ILIKE %s"
            params.append(course_number)

        query += " ORDER BY c.subject_code, c.course_number, c.section, i.name"

        cursor.execute(query, tuple(params))
        results = cursor.fetchall()

        # NUMERIC columns arrive as Decimal — make them JSON-friendly floats.
        for row in results:
            for key in ("rating", "difficulty"):
                if row.get(key) is not None:
                    row[key] = float(row[key])

        return {
            "status": "success",
            "count": len(results),
            "term": current_term,
            "data": results,
        }
    finally:
        conn.close()
