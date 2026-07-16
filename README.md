# MajorMap AI

Plan the right classes, avoid bad advising, and graduate on time — with a
semester-by-semester degree map and a live AI advisor. Everything runs
client-side; there is no backend to set up.

## Open the site

All three pages are plain static HTML — just open them in a browser, or serve
the folder.

| File | What it is |
|------|-----------|
| `index.html` | Marketing landing page |
| `app.html` | **The interactive degree planner** (the main app) |
| `demo.html` | Earlier single-screen demo |

**Fastest way to open it:**

```bash
# from the repo root
python3 -m http.server 8000
# then visit http://localhost:8000/app.html
```

Or just double-click `app.html` — it's fully self-contained (no CDN, no network
needed) and works straight from disk.

## The app (`app.html`)

**Database-first.** The app opens straight into the **Course Database** — a
premium, searchable table of every section (ratings, seats, times) with an
always-visible filter bar. No onboarding required.

- **Course Database home** — instant load, sticky filter bar (search + term +
  subject + course number + "on my map") and an Advanced Filters drawer. Every
  row has a **＋ Add to schedule** button.
- **Slide-out schedule** — clicking ＋ locks in that exact **section/CRN** and
  slots it into your timeline, sliding out a right-hand **My Schedule** drawer
  (which *pushes* the table aside so no columns get covered); tap any highlighted
  term or drag to move it. Click a row's ✓ again to remove it.
- **Time-conflict detection** — the drawer flags overlapping sections in the same
  term (e.g. "ENGL 101 ↔ BLAW 201") and marks health "Clash". `TBD / async`
  sections are ignored.
- **Sortable table** — click any header (Course, Title, CRN, **Instructor ★**,
  **Seats**, Cr) to sort; click again to reverse.
- **Guided planner (opt-in)** — "✨ Auto-build" runs a 5-step wizard (school,
  major, year, career goal, workload, prior credits) to generate a full,
  prerequisite-aware plan; "⤢ Full planner" opens the advisor/auto-optimize view.
- **Light & dark mode** — follows your system preference, with a sun/moon toggle
  in the header that overrides it and remembers your choice (`localStorage`).
- **Philadelphia universities** — Drexel, Penn, Temple, Saint Joseph's, Thomas
  Jefferson, and La Salle. The timeline adapts to each school's calendar.
- **Dynamic timeline** — semester schools render a 4-year Fall/Spring grid;
  **Drexel** renders a **5-year quarter** grid (Fall/Winter/Spring/Summer) with
  built-in **full-time co-op blocks**. Switch schools from the header dropdown and
  the grid animates between layouts.
- **Co-op / Pathfinder** — for Drexel's co-op terms the AI Advisor suggests real
  Philly roles by major (e.g. Financial Associate at Vanguard, Software
  Engineering co-op at Comcast).
- **Interactive map** — drag courses between terms; co-op/break terms are locked.
- **Click any course** — prerequisites, what it unlocks, a description, and
  *why the AI placed it there* for your career goal.
- **Live AI Advisor** — flags prerequisite conflicts, overloaded / reading-heavy
  terms, co-op planning, and career tips; re-analyzes on every change.
- **Auto-Optimize** — one click re-sequences courses to respect prerequisites and
  rebalances load.
- **Save / Export** — save to the browser, export JSON, or print to PDF.

Majors included: Computer Science, Business Administration, Accounting & Economics.

## Live Drexel data (optional)

The planner can overlay **real Drexel Term Master Schedule** data — actual
sections, meeting times, instructors (with RateMyProfessor ratings), and open
seats — on top of your map.

> ⚠️ **Prototype data:** without a backend, the bundled sample's instructor ★
> ratings and seat counts are **placeholder/demo values**. With the live API,
> ratings come from the scraper's **cached RateMyProfessors database** (they can
> lag live RMP). The app labels its data source next to the term badge either way.

There are three tiers, and the app picks the best one available automatically:

1. **Live API (best)** — see *Backend API* below. On load the app probes
   `http://localhost:8000/api/health`; if it answers, the table switches to
   live PostgreSQL data (green **live API** pill) and the Term/Subject/Number
   filters become server-side queries.
2. **📂 Import** — run the
   [drexel-scraper](https://github.com/Zohair-coder/drexel-scraper) yourself
   (it needs your own Drexel login + MFA — that stays on your machine) and load
   the `data.json` it produces.
3. **Sample fallback** — with neither, the bundled sample term loads so the
   hosted/offline prototype always works.

## Backend API (`backend/`)

A lightweight FastAPI layer that serves the scraper's PostgreSQL database
(`schedulerdb`) to the frontend:

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload        # interactive docs at http://localhost:8000/docs
```

- `GET /api/sections` — filterable by `term`, `subject`, `course_number`;
  returns a flat JSON array (one row per section+instructor) which the frontend
  groups by CRN.
- `GET /api/health` — the probe the frontend uses to pick live-vs-sample mode.
- Written against the scraper's *actual* schema (`courses` keyed by CRN,
  `course_instructor` junction, `instructors` with cached RMP ratings, term in
  `metadata`). `building`/`room` are returned as `NULL` placeholders until the
  scraper collects them.
- Term values are treated as **opaque strings** (loose case-insensitive match),
  so the expected quarter→semester code change in August 2027 requires no code
  changes here.
- DB connection is configured via `DB_HOST`, `DB_NAME`, `DB_USER`,
  `DB_PASSWORD`, `DB_PORT` env vars (defaults match the scraper's Docker setup).
- `python3 backend/test_api.py` runs wiring tests with a faked DB (no Postgres
  needed).

The **Live Sections** view is a premium data dashboard: a primary filter bar
(term, subject, course number, "on my map") plus an **Advanced filters** drawer
(instructor rating, difficulty, start/end time, prerequisites, open seats, blank
ratings), and a scannable table with a sticky glass header, accent-colored CRN /
RateMyProfessors links, and live seat bars.

Sections are matched to courses on your map by subject + course number. Courses
that are offered show a `📡` badge (blue = open seats, red = full), and the
course detail popup lists the real sections for that term.

> Note: the scraper is a separate, community-built tool and is not officially
> supported by Drexel. MajorMap AI only *reads* the `data.json` it outputs — it
> never sees your credentials.
