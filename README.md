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

> ⚠️ **Prototype data:** the bundled sample's instructor ★ ratings and seat
> counts are **placeholder/demo values** — not real RateMyProfessors or live
> registrar data. The app shows this notice next to the term badge.

1. The app loads the bundled `data/sample-drexel-data.json` automatically.
2. To use *real* current data, run the
   [drexel-scraper](https://github.com/Zohair-coder/drexel-scraper) yourself
   (it needs your own Drexel login + MFA — that stays on your machine), then click
   **📂 Import** in the Course Database and pick the `data.json` it produced.

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
