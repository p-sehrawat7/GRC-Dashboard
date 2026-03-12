# GRC Audit Simulation Dashboard

![Python](https://img.shields.io/badge/Python-3.12-blue)
![Streamlit](https://img.shields.io/badge/Streamlit-1.40+-red)
![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0-green)
![Tests](https://img.shields.io/badge/Tests-44%20passing-brightgreen)
![CI](https://img.shields.io/badge/CI-GitHub%20Actions-black)
![License](https://img.shields.io/badge/License-Portfolio%20Use-lightgrey)

---

## What is this project?

This is a full-stack GRC (Governance, Risk and Compliance) dashboard I built with Python and Streamlit. The idea came from wanting to simulate what a real enterprise compliance tool looks like under the hood — the kind of software that risk teams, auditors, and CISOs use daily to track risks, assess controls, and manage audit findings.

Rather than building a toy CRUD app, I aligned the data model and terminology to two major industry frameworks — **ISO 27001** (the international standard for information security management) and **NIST CSF** (the US National Institute of Standards and Technology's Cybersecurity Framework). Every risk and control in the system is tagged to a specific ISO clause and NIST function, which is exactly how real GRC tools like ServiceNow GRC, RSA Archer, and OneTrust operate.

The app runs locally or in Docker, persists data to SQLite (swappable to PostgreSQL), and has proper authentication, role-based access, an audit trail, PDF/Excel exports, and a CI/CD pipeline. I built it as a portfolio piece to demonstrate that I can architect and ship a multi-layer Python application — not just write scripts.

---

## Pages and Features

### Executive Dashboard
The first thing you see after logging in. It gives you a high-level read on the organisation's risk posture at a glance.

- **Risk Appetite Monitor** — you pick the organisation's risk appetite level (Low / Medium / High) from the sidebar, and the dashboard immediately flags which registered risks exceed that threshold. If 8 risks are rated "High" and the appetite is set to "Medium", those 8 risks light up in a warning alert along with a filterable table.
- **KPI Panels** — two rows of metric cards: one for risks (total, critical, high, medium) and one for controls (total implemented, partial, missing). Each card has a hover shadow effect.
- **Risk Heatmap** — an Impact × Likelihood matrix showing where your risks cluster. Darker red = more risks at that intersection.
- **Risk Level Donut** — breakdown of how many risks sit at each level (Critical / High / Medium / Low).
- **Treatment Strategy Donut** — shows how risks are being handled: Mitigated, In Progress, Accepted, Transferred, or Avoided.
- **Residual Risk Comparison** — a grouped bar chart that shows, for each risk ID, what the inherent risk level was vs. what it dropped to after controls were applied.
- **ISO 27001 Clause Coverage** — grouped bar chart showing which ISO Annex A clauses have Implemented, Partial, or Missing controls mapped to them.
- **NIST CSF Function Coverage** — stacked bar chart across the five NIST functions (Identify, Protect, Detect, Respond, Recover) showing control implementation depth.
- **Remediation Gauge** — a dial that shows what percentage of audit findings have been closed. Thresholds at 40% (red) and 70% (green) match common audit KPI benchmarks.
- **Open Findings by Severity** — bar chart showing how many Critical, High, Medium, and Low findings are still unresolved.

---

### Risk Register
A full register of all identified information security risks — 40 rows seeded out of the box, each mapped to a real threat scenario.

Each risk record stores:
- **Risk ID** — unique reference like R-01, R-02, etc.
- **Asset** — the system, dataset, or process being put at risk (e.g. "Customer PII Database", "Cloud Infrastructure")
- **Threat** — the actor or event that could exploit the vulnerability (e.g. "External Attacker", "Negligent Insider")
- **Vulnerability** — the specific gap or weakness (e.g. "No MFA on admin accounts")
- **Impact score** — 1 (negligible) to 5 (catastrophic)
- **Likelihood score** — 1 (rare) to 5 (almost certain)
- **Risk Score** — automatically calculated as Impact × Likelihood, giving a 1–25 scale
- **Risk Level** — derived from the score: Low (1–6), Medium (7–12), High (13–18), Critical (19–25)
- **Treatment Status** — what's being done about it: In Progress, Mitigated, Accepted, Transferred, or Avoided
- **ISO 27001 Clause** — which part of the standard applies (e.g. A.9.4 for Access Control)
- **NIST CSF Function** — which framework function the risk falls under

The table is colour-coded by risk level so you can scan it at a glance. Filters in the sidebar let you slice by asset type, risk level, treatment status, ISO clause, and NIST function. There are CSV and Excel export buttons at the bottom.

If you're logged in as Admin or Auditor, an "Add New Risk" expander appears with a fully validated form. It includes a live risk score preview that updates as you adjust the Impact and Likelihood sliders, colour-coded from green to red.

---

### Control Matrix
Lists the 40 security controls mapped against the risks in the register. Each control describes a safeguard or measure that's been applied (or should be applied) to reduce a specific risk.

Each control record stores:
- **Control ID** — unique reference like C-01
- **Control Name** — short label (e.g. "Multi-Factor Authentication", "Endpoint Detection and Response")
- **Control Description** — what the control actually does in practice
- **Mapped Risk ID** — which risk this control addresses (foreign key relationship)
- **Control Type** — Preventive (stops the threat), Detective (identifies it), Corrective (fixes it), or Recovery (restores operations)
- **Implementation Status** — Implemented, Partial, or Missing
- **Effectiveness** — Effective, Needs Improvement, or Ineffective
- **Evidence** — what proof exists that the control is working (e.g. log files, audit reports, training records)
- **Gap Description** — what's still missing or incomplete
- **Residual Risk Level** — the risk level that remains after the control is applied
- **ISO 27001 Clause** and **NIST CSF Function** — same as risks, for cross-framework traceability

Admin and Auditor roles can add new controls directly from the UI.

---

### Audit Findings
Tracks the specific gaps and failures discovered during an audit. This is where a finding like "MFA not enabled on 3 out of 12 admin accounts" would live, along with who owns it, its due date, and whether it's been resolved.

Each finding stores:
- **Finding ID** — unique reference like F-01
- **Linked Risk and Control** — which risk scenario and which control failure this finding relates to
- **Title** — short, descriptive name of the finding
- **Severity** — Critical / High / Medium / Low
- **Status** — Open, In Remediation, or Closed
- **Due Date** — deadline for remediation
- **Owner** — the person or team responsible for fixing it
- **Description** — detailed notes about what was found

The page automatically calculates whether findings are **overdue** (due date has passed and status isn't Closed). Overdue findings appear highlighted and are surfaced prominently in the summary.

Filters let you drill down by severity, status, and whether items are overdue. Admins can update finding statuses and add new findings from the UI. All three export formats (CSV, Excel, PDF) are available here with a "PDF Executive Summary" button that generates a well-formatted PDF report of the current findings view.

---

## Authentication and Role-Based Access

The login page is a clean, centred card UI — no Streamlit header chrome, no default styling — just the login form on a grey background. Passwords are hashed using **bcrypt** before going anywhere near the database. There's no plaintext storage.

Three roles are built in:

| Username | Password | Role | What they can do |
|---|---|---|---|
| `admin` | `admin123` | Admin | Everything — add, edit, view, export across all pages |
| `auditor` | `audit123` | Auditor | Add and edit records, view all data, export |
| `viewer` | `view123` | Viewer | Read-only access to all pages and data |

Role enforcement works through a `require_role()` function that checks the current user's role against a hierarchy (`viewer < auditor < admin`). Any button or form that requires elevated access wraps behind this check — if you don't meet the threshold, you'll see an access-denied message instead of the form.

Every login attempt (success or failure) is recorded in the application log. Session state is cleared completely on sign-out.

> These are demo credentials. Change them before using this in any real environment.

---

## Audit Trail

Every time a record is created, updated, or deleted, a row is written to the `audit_log` table in the database. It stores:
- Which table was affected (risks, controls, audit_findings)
- The record ID
- The action type (CREATE, UPDATE, DELETE)
- The username who made the change
- A timestamp
- A detail field with the before/after data

This is the kind of functionality that matters in a compliance context — if an auditor asks "who changed this risk rating and when?", you can answer that.

---

## Exports

Three export formats are supported:

- **CSV** — raw data download, useful for further analysis in Excel or importing into other tools
- **Excel (`.xlsx`)** — formatted workbook using openpyxl, with column headers and proper data types. The findings export includes an "Is Overdue" column already calculated.
- **PDF Executive Summary** — generated using fpdf2. Includes a cover section, key metrics, and a findings table suitable for sharing with non-technical stakeholders or management.

All export buttons are scoped to the currently filtered view — so if you've filtered to only Critical findings, the export only includes those.

---

## Logging

The app writes to a rotating log file at `logs/grc_app.log`. The logger is set up with a 1MB file size limit and keeps 3 backup files, so logs don't grow unbounded. Log entries capture:
- Login success and failure (with username)
- Logout events
- Record creation, update, delete (with record ID and username)
- Any application errors

The logger is imported as a module-level singleton — `get_logger(__name__)` — so every file has its own named logger, making it easy to trace which module produced which log line.

---

## Database

The ORM layer uses **SQLAlchemy 2.0** with five tables:

| Table | Purpose |
|---|---|
| `risks` | Core risk register |
| `controls` | Controls mapped to risks (FK relationship) |
| `audit_findings` | Findings linked to both risks and controls |
| `audit_log` | Immutable change log for all mutations |
| `users` | Login credentials with bcrypt-hashed passwords |

By default the app uses **SQLite** (stored at `backend/grc.db`), which requires zero configuration for local development. To go to production, you swap in a `DATABASE_URL` environment variable pointing at a PostgreSQL instance and the same ORM code works without modification — SQLAlchemy abstracts the driver.

The seed script (`database/seed.py`) populates 40 risks, 40 controls, and 40 audit findings with realistic, varied data — different risk levels, NIST functions, ISO clauses, treatment statuses, overdue dates, and finding severities. It also creates the three demo users with bcrypt-hashed passwords.

---

## Project Structure

```
grc-dashboard/
│
├── dashboard/               # All Streamlit UI code
│   ├── app.py               # Entry point — page config, CSS, routing
│   ├── auth.py              # Login page, bcrypt verification, RBAC guard
│   ├── views/
│   │   ├── dashboard.py     # Executive summary, KPIs, all charts
│   │   ├── risk_register.py # Risk table, filters, add-risk form
│   │   ├── control_matrix.py# Control table, filters, add-control form
│   │   └── audit_findings.py# Findings table, overdue logic, exports
│   └── utils/
│       ├── charts.py        # All Plotly chart functions (decoupled from UI)
│       ├── crud.py          # Pure SQLAlchemy CRUD helpers (no Streamlit)
│       ├── data_loader.py   # Cached data-loading functions
│       ├── filters.py       # Sidebar filter widgets
│       └── logger.py        # Rotating file logger setup
│
├── database/
│   ├── models.py            # SQLAlchemy ORM models (Risk, Control, etc.)
│   ├── db.py                # Engine creation, session context manager
│   └── seed.py              # Seeds 40+ realistic rows into each table
│
├── backend/
│   └── grc.db               # SQLite database file (auto-created by seed.py)
│
├── tests/
│   ├── conftest.py          # In-memory SQLite fixture, seeded test data
│   ├── test_auth.py         # Tests for bcrypt verification and RBAC logic
│   ├── test_crud.py         # Tests for create, update, delete operations
│   ├── test_data.py         # Tests for ORM models and overdue calculations
│   └── test_exports.py      # Tests for PDF and Excel export functions
│
├── .github/workflows/
│   └── ci.yml               # GitHub Actions: Black + Flake8 + pytest on push
│
├── docs/
│   └── architecture.md      # Component diagram and data flow description
│
├── logs/                    # Application log output (gitignored)
├── Dockerfile               # Container build instructions
├── docker-compose.yml       # Docker Compose config with volume mounts
├── requirements.txt         # Python dependencies
├── pyproject.toml           # Black and pytest configuration
├── .flake8                  # Flake8 linting config
├── .env.example             # Template for environment variables
└── .gitignore               # Excludes .venv, grc.db, logs, secrets, etc.
```

---

## Getting Started

### Local Python (quickest way to run it)

```bash
# 1. Clone or download the project, then navigate to it
cd grc-dashboard

# 2. Create a virtual environment
python -m venv .venv

# 3. Activate it
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # macOS / Linux

# 4. Install dependencies
pip install -r requirements.txt

# 5. Seed the database with realistic sample data
python database/seed.py

# 6. Start the app
streamlit run dashboard/app.py
```

Open http://localhost:8501 in your browser. Log in with `admin` / `admin123`.

---

### Docker (if you prefer containers)

```bash
# Build the image and start the container
docker compose up --build

# The app will be available at http://localhost:8501
# Login: admin / admin123
```

The `docker-compose.yml` mounts `./backend` and `./logs` as volumes so the database and logs persist between container restarts.

---

## Running the Test Suite

```bash
# Run all 44 tests with verbose output
pytest tests/ -v

# Run only the auth tests
pytest tests/test_auth.py -v

# Run with coverage report
pip install pytest-cov
pytest tests/ --cov=dashboard --cov-report=term-missing
```

The tests use an **in-memory SQLite database** — nothing is written to disk, there's no test-specific config to set up, and each test function gets a fresh database via the `db_session` fixture in `conftest.py`. The auth tests use `monkeypatch` to stub `st.session_state` so they can test the RBAC logic without a running Streamlit server.

Test breakdown:
- `test_auth.py` — 11 tests covering bcrypt password verification (correct, wrong, empty, invalid hash) and role-based access (all role combinations)
- `test_crud.py` — 14 tests covering create, update, delete for risks, controls, and findings, plus audit log entries
- `test_data.py` — 11 tests for ORM model structure and the overdue calculation logic
- `test_exports.py` — 8 tests checking PDF byte output and Excel sheet/column structure

---

## Linting and Code Formatting

The project uses **Black** for formatting and **Flake8** for linting. Both run automatically in CI on every push.

```bash
# Auto-format the codebase
black dashboard/ tests/ database/

# Check formatting without changing files (what CI runs)
black --check dashboard/ tests/ database/

# Run the linter
flake8 dashboard/ tests/ database/
```

Black and Flake8 config lives in `pyproject.toml` and `.flake8` respectively.

---

## CI/CD Pipeline

Every push to `main`, `master`, or `develop` triggers a GitHub Actions workflow (`.github/workflows/ci.yml`) that:

1. Checks out the code
2. Sets up Python 3.12
3. Installs all dependencies from `requirements.txt`
4. Runs `black --check` to verify formatting
5. Runs `flake8` to catch style issues
6. Runs the full pytest suite against an in-memory SQLite database

Pull requests to `main` and `master` also trigger the same checks. Nothing merges if any step fails.

---

## Switching to PostgreSQL

If you want to run this against a real database instead of SQLite:

1. Install the PostgreSQL driver:
   ```bash
   pip install psycopg2-binary
   ```

2. Copy the environment template:
   ```bash
   cp .env.example .env
   ```

3. Open `.env` and set your connection string:
   ```
   DATABASE_URL=postgresql+psycopg2://your_user:your_password@localhost:5432/grc_db
   ```

4. Re-run the seed script to populate the PostgreSQL database:
   ```bash
   python database/seed.py
   ```

The ORM code stays identical — SQLAlchemy handles the driver switch transparently.

---

## Deploying to Streamlit Cloud

Streamlit Cloud is the easiest way to get a live public URL for this app, and it's free.

The app is **Streamlit Cloud ready out of the box** — on first boot, `db.py` automatically creates all tables and seeds the full dataset (40 risks, 40 controls, 40 findings, 3 users) via `_auto_seed_if_empty()`. No manual steps or committed database files are needed.

### Deploy steps

1. Go to **[share.streamlit.io](https://share.streamlit.io)** and sign in with your GitHub account
2. Click **New app**
3. Select your repository and branch (`main`)
4. Set the **Main file path** to `dashboard/app.py`
5. Click **Deploy** — Streamlit Cloud reads `requirements.txt` and installs everything automatically

Your app will be live in 2–3 minutes at a URL like:
`https://your-username-grc-dashboard-dashboard-app-xxxx.streamlit.app`

### Using PostgreSQL on Streamlit Cloud

For persistent data across restarts, point the app at a hosted PostgreSQL instance (e.g. Supabase, Neon, or Railway — all have free tiers). In Streamlit Cloud:

1. Go to **App settings → Secrets**
2. Add the following:
   ```toml
   DATABASE_URL = "postgresql+psycopg2://user:password@host:5432/grc_db"
   ```
3. Run `python database/seed.py` once against that database to populate it

---

## Technology Stack

| Layer | Technology | Why |
|---|---|---|
| UI Framework | Streamlit 1.40+ | Fast to build data-heavy UIs in pure Python without a separate frontend |
| Data Processing | pandas 2.0+ | DataFrame manipulation for filtering, aggregation, and export prep |
| Visualisation | Plotly 5.18+ | Interactive charts — hover tooltips, zoom, responsive layout |
| ORM | SQLAlchemy 2.0 | Clean model definitions, database-agnostic queries, relationship handling |
| Database | SQLite (dev) / PostgreSQL (prod) | SQLite for zero-config local dev; PostgreSQL for production deployments |
| Authentication | bcrypt + session state | Industry-standard password hashing; no third-party auth service needed |
| PDF Export | fpdf2 2.7+ | Lightweight, pure-Python PDF generation without Java or wkhtmltopdf |
| Excel Export | openpyxl 3.1+ | Native `.xlsx` generation with proper formatting and column types |
| Testing | pytest 7.4+ | Clean fixtures, parametrize support, monkeypatching for Streamlit mocking |
| Containers | Docker + Compose | Single command to spin up a reproducible environment |
| CI/CD | GitHub Actions | Automated lint + test on every push, no manual intervention |
| Linting | Black + Flake8 | Black enforces consistent formatting; Flake8 catches logical style issues |

---

## Known Limitations

- **No delete UI for risks/controls** — The backend `delete_risk()` function exists and is tested, but there's no delete button in the UI. In real GRC tools, hard deletion is rarely allowed — records are "retired" instead to preserve the audit trail. This project follows the same philosophy.
- **SQLite is single-threaded** — Fine for a single-user local or Streamlit Cloud deployment. For multi-user production, switch to PostgreSQL via `DATABASE_URL`.
- **No login rate limiting** — The login form has no lockout after repeated failures. A production deployment should add this.
- **No user management UI** — Users are managed via the seed script or direct database access, not from within the dashboard.

---

## Screenshots

### Login Page
![Login Page](docs/screenshots/1.png)

---

### Executive Dashboard — Summary & KPIs
![Executive Dashboard](docs/screenshots/2.png)

---

### Risk Register — Score Chart & Colour-coded Table
![Risk Register Table](docs/screenshots/3.png)

---

### Risk Register — Click-to-Edit Panel
![Edit Risk Panel](docs/screenshots/4.png)

---

### Dashboard — Governance & Compliance Coverage
![Governance Coverage](docs/screenshots/5.png)

---

### Dashboard — Findings Analysis Charts
![Findings Analysis](docs/screenshots/6.png)

---

### Audit Findings — Close a Finding
![Close Finding](docs/screenshots/7.png)

---

### Control Matrix — Add New Control Form
![Add Control Form](docs/screenshots/8.png)

---

### Audit Findings — Full Findings Table
![Findings Table](docs/screenshots/9.png)

---

### Sidebar Filters
![Sidebar Filters](docs/screenshots/10.png)

---
