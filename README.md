# MajorMap AI

**A high-speed course search and degree-planning app for the Philadelphia
college ecosystem.** Open it and you're instantly in a searchable database of
course sections — ratings, seat availability, meeting times — and one click
adds any section to a visual, conflict-checked degree timeline.

- **Live site:** https://majormapai.com (see [Deployment](#deployment-github-pages--custom-domain))
- **Landing page:** `index.html` · **The app:** `app.html`

---

## 1. Overview & Features

### Course Database (home screen)
- **Database-first UX** — no onboarding wizard; the app opens directly into the
  section table with an always-visible filter bar (search, Term, Subject,
  Course Number, "on my map") plus an **Advanced Filters** drawer (min
  instructor rating, max difficulty, start/end time window, prerequisites,
  open seats only, blank ratings).
- **Sortable tables** — click any column header (Course, Title, Sec, CRN,
  Instructor ★, Seats, Cr) to sort; click again to reverse. Ratings and Seats
  default to high→low.
- **Dynamic data source toggling** — on load the app probes the local FastAPI
  backend (`/api/health`). If it answers, the table switches to **live
  PostgreSQL data** (green `live API` pill) and filters become server-side
  queries. If not, it falls back to the bundled **sample term** (labeled
  `sample data`) so the hosted/offline prototype always works. A third path,
  **📂 Import**, loads a `data.json` produced by the scraper directly.

### Scheduling
- **CRN / section locking** — the ＋ button on each row adds that *exact
  section* (CRN) to your schedule; clicking ＋ on a different section of the
  same course swaps the locked CRN. The row's ✓ removes it again.
- **Real-time time-conflict detection** — sections in the same term that share
  a meeting day with overlapping times are flagged instantly: red chips, a
  "⚠ Time conflict: ENGL 101 ↔ BLAW 201" note, plan health flips to **Clash**,
  and the AI Advisor raises a ⏰ error. `TBD / async` sections are excluded.
- **Weekly calendar grid view** — the schedule drawer renders locked sections
  as positioned Mon–Fri time blocks; overlapping blocks pulse red, and
  async/TBD courses are listed separately below the grid.
- **Responsive drawer UI** — the right-hand **My Schedule** drawer *pushes* the
  table aside on wide screens (no covered columns) and overlays on small
  screens; the table stays interactive behind it so you can keep adding.

### Degree planning
- **Dynamic academic timelines** — semester schools (Penn, Temple, Saint
  Joseph's, Thomas Jefferson, La Salle) render a 4-year Fall/Spring grid;
  **Drexel** renders a 5-year **quarter** grid (Fall/Winter/Spring/Summer) with
  built-in full-time **co-op blocks** and Philly role suggestions by major.
  Switching schools animates the grid between layouts.
- **Guided planner (opt-in)** — "✨ Auto-build" runs a 5-step wizard to generate
  a full prerequisite-aware plan for a major; "⤢ Full planner" opens the
  workspace with the live **AI Advisor** (prereq violations, overloaded /
  reading-heavy terms, career tips) and one-click **Auto-Optimize**.
- **Light & dark mode** — follows the system preference, with a sun/moon
  header toggle that overrides it and persists to `localStorage`.
- **Save / Export** — save to the browser, export JSON, print to PDF.

---

## 2. Architecture

```
┌────────────────────────┐     fetch /api/sections      ┌───────────────────┐
│  Frontend SPA          │ ───────────────────────────▶ │  FastAPI backend  │
│  app.html              │ ◀─────────────────────────── │  backend/main.py  │
│  vanilla HTML/CSS/JS   │     flat JSON rows           │  psycopg2         │
│  (zero build step,     │                              └─────────┬─────────┘
│   zero dependencies)   │        falls back to                   │ SQL
│                        │        embedded sample data   ┌────────▼──────────┐
└────────────────────────┘        when API unreachable   │  PostgreSQL       │
                                                         │  `schedulerdb`    │
                                                         │  populated by the │
                                                         │  drexel-scraper   │
                                                         │  (terms + cached  │
                                                         │   RMP ratings)    │
                                                         └───────────────────┘
```

| Layer | Tech | Notes |
|-------|------|-------|
| Frontend | Vanilla HTML/CSS/JS, single file (`app.html`) | Self-contained: no CDN, no build step, works from `file://`, static hosts, and GitHub Pages. Token-based light/dark theming. |
| API | **FastAPI** + `psycopg2` (`RealDictCursor`), CORS enabled | `backend/main.py`. Parameterized SQL only. |
| Database | **PostgreSQL** (`schedulerdb`) | Populated by the community [drexel-scraper](https://github.com/Zohair-coder/drexel-scraper) (Term Master Schedule + cached RateMyProfessors ratings). |

Schema notes (matches the scraper's actual `create_tables.sql`): each `courses`
row **is** one section, keyed by `crn`; `course_instructor` is the junction to
`instructors` (which carry cached `avg_rating` / `avg_difficulty`); the current
term lives in `metadata.current_term`. Term values are treated as **opaque
strings** end-to-end (loose, case-insensitive matching), so Drexel's expected
quarter→semester transition in August 2027 requires no code changes.
`building` / `room` are returned as `NULL` placeholders until the scraper
collects them.

---

## 3. Getting Started & Setup

### Prerequisites
- Python 3.10+ (backend)
- PostgreSQL with the `schedulerdb` database populated by the
  [drexel-scraper](https://github.com/Zohair-coder/drexel-scraper) (`--db` mode).
  The scraper needs *your own* Drexel login + MFA — credentials never touch this app.

### 3.1 Configure the database connection

The backend reads standard environment variables (defaults match the scraper's
Docker setup):

```bash
export DB_HOST=localhost          # PostgreSQL host
export DB_NAME=schedulerdb        # database created by the scraper
export DB_USER=postgres
export DB_PASSWORD=super-secret-password
export DB_PORT=5432
```

### 3.2 Run the backend

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```

- Interactive API docs: http://localhost:8000/docs
- Wiring tests (no PostgreSQL needed — fakes the connection):
  `python3 backend/test_api.py`

### 3.3 Launch the frontend

```bash
# from the repo root — any static server works
python3 -m http.server 3000
# visit http://localhost:3000/app.html   (index.html is the landing page)
```

Or simply double-click `app.html` — it also runs straight from disk. On load it
probes `http://localhost:8000/api/health`: with the backend up you'll see the
green **live API** pill and server-side filtering; without it, the labeled
sample term loads automatically.

---

## 4. API Endpoints

### `GET /api/sections`

Returns course sections as a flat JSON array — one row per
(section, instructor) pair; the frontend groups rows by CRN into sections with
an `instructors[]` array.

| Query param | Example | Behavior |
|-------------|---------|----------|
| `term` | `Fall 2026`, `fall`, `2026` | Loose, case-insensitive substring match against the DB's current term. Opaque string — format-agnostic (survives the 2027 semester-code change). |
| `subject` | `CS` | Case-insensitive match on subject code (`ILIKE`). |
| `course_number` | `171` | Case-insensitive match on course number (`ILIKE`). |

Response envelope:

```json
{
  "status": "success",
  "count": 128,
  "term": "Fall 2026",
  "data": [
    {
      "subject_code": "CS", "course_number": "171",
      "title": "Computer Programming I", "credits": "3.0",
      "crn": 12345, "section": "A",
      "instruction_type": "Lecture", "instruction_method": "Face To Face",
      "prereqs": "", "max_enroll": "30", "enroll": "12",
      "days": ["Monday", "Wednesday"], "start_time": "10:00", "end_time": "11:50",
      "building": null, "room": null,
      "instructor_name": "Ada Lovelace",
      "rating": 4.5, "difficulty": 2.5, "num_ratings": 42, "rmp_id": 999
    }
  ]
}
```

### `GET /api/health`

Cheap liveness probe used by the frontend to choose live-vs-sample mode:

```json
{ "status": "ok", "term": "Fall 2026", "sections": 4210 }
```

Returns `{"status": "degraded", "database": "unreachable"}` if PostgreSQL is down.

> **Ratings disclaimer:** instructor ★ ratings served by the API come from the
> scraper's *cached* RateMyProfessors database and can lag live RMP values; in
> sample mode they are placeholder demo values. The UI labels the active source
> next to the term badge.

---

## Deployment (GitHub Pages + custom domain)

The frontend is fully static, so the repo deploys directly to **GitHub Pages**;
the backend deploys separately to a cloud host (below). The live site probes
the deployed API on load and only falls back to sample data if it's unreachable.

### Deploying the backend (Render — one click)

A [`render.yaml`](./render.yaml) Blueprint provisions both the API and a
managed PostgreSQL:

1. Render dashboard → **New → Blueprint** → select this repo → Apply. This
   creates the `majormap-api` web service (with `ALLOWED_ORIGINS` preset to
   `https://majormapai.com` / `https://www.majormapai.com`) and the
   `majormap-db` PostgreSQL, wired together via `DATABASE_URL`.
2. Check the service URL Render assigned. The frontend expects
   `https://majormap-api.onrender.com` — if Render appended a suffix (name
   collision), update the single `API_BASE_PROD` constant near the top of
   `app.html`'s script and push.
3. **Load data** — the new database starts empty. From your own machine, run
   the [drexel-scraper](https://github.com/Zohair-coder/drexel-scraper) in
   `--db` mode pointed at Render's *External Database URL* (dashboard →
   majormap-db → Connect): set the scraper's DB env vars to that host, user,
   password, and database (`schedulerdb`). Re-run it whenever you want fresh
   seat counts — the API serves whatever is in the DB.
4. Verify: `https://<your-service>.onrender.com/api/health` should return
   `{"status":"ok", "term": …}` — then majormapai.com will show the green
   **live API** pill on next load.

> Free-tier note: Render free services sleep when idle and cold-start in
> ~30–60 s. The frontend paints the sample table instantly and keeps probing
> for up to 45 s, swapping to live data when the API wakes.

**Alternative hosts** (same code, pick one):
- **Railway** — the root [`Procfile`](./Procfile) is picked up automatically;
  add a Railway PostgreSQL plugin (it injects `DATABASE_URL`) and set
  `ALLOWED_ORIGINS`.
- **Fly.io** — `cd backend && fly launch` (uses [`backend/Dockerfile`](./backend/Dockerfile));
  attach Fly Postgres and set the same env vars.

CORS is env-driven: `ALLOWED_ORIGINS` (comma-separated) defaults to the
production domains + local dev origins; only `GET` is allowed.

### One-time repo setup

1. GitHub → **Settings → Pages** → Source: *Deploy from a branch* →
   Branch: `main` / `/ (root)` → Save.
2. In the same Pages screen, enter the custom domain `majormapai.com` and save.
3. After DNS propagates (below), tick **Enforce HTTPS**.

A [`CNAME`](./CNAME) file containing `majormapai.com` is committed at the repo
root — GitHub Pages requires it for custom-domain validation, and committing it
prevents the domain setting from being wiped on future deploys.

### DNS records to add in the Wix Domain Manager

`majormapai.com` is registered through Wix, so configure these in
**Wix → Domains → majormapai.com → Advanced / DNS records** (remove any default
Wix A/CNAME records for `@` and `www` that point at Wix hosting first):

| Type | Host / Name | Value | TTL |
|------|-------------|-------|-----|
| A | `@` | `185.199.108.153` | default |
| A | `@` | `185.199.109.153` | default |
| A | `@` | `185.199.110.153` | default |
| A | `@` | `185.199.111.153` | default |
| CNAME | `www` | `geogarciaaa.github.io` | default |

> ⚠️ **Note on the `www` record:** a DNS CNAME must point to a *hostname*, so
> the correct target is `geogarciaaa.github.io` — **not**
> `geogarciaaa.github.io/majormap-ai` (paths are not valid in DNS). GitHub
> routes the request to this repository via the committed `CNAME` file and the
> Pages custom-domain setting.

Optional IPv6 (AAAA) records for `@`: `2606:50c0:8000::153`,
`2606:50c0:8001::153`, `2606:50c0:8002::153`, `2606:50c0:8003::153`.

Verify propagation with `dig majormapai.com +noall +answer` (expect the four A
records) and `dig www.majormapai.com +noall +answer` (expect the CNAME). GitHub
then provisions the TLS certificate automatically — allow up to ~24 h on first
setup.

---

## Repo layout

| Path | What it is |
|------|-----------|
| `index.html` | Marketing landing page |
| `app.html` | **The app** — course database + degree planner (single file) |
| `backend/main.py` | FastAPI API over the scraper's PostgreSQL |
| `backend/test_api.py` | Backend wiring tests (no DB required) |
| `data/sample-drexel-data.json` | Scraper-shaped sample term (fallback dataset) |
| `CNAME` | GitHub Pages custom-domain file (`majormapai.com`) |
| `demo.html` | Earlier single-screen demo (kept for reference) |

> The drexel-scraper is a separate, community-built tool and is not officially
> supported by Drexel University. MajorMap AI only reads its output — your
> Drexel credentials never touch this app.
