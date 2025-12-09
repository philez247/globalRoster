# FD Global Roster

Minimal FanDuel-style trading roster app built with FastAPI + Jinja + SQLite. Includes Traders list, add trader flow, and Management tab for soft remove / hard delete.

## Quickstart (local)

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Visit:
- Traders: http://127.0.0.1:8000/traders
- Management: http://127.0.0.1:8000/management

## Docker

```bash
docker build -t fd-global-roster .
docker run -p 10000:10000 fd-global-roster
```

## Repo layout

- `app/` FastAPI application (routers, models, templates, static)
- `requirements.txt` Python dependencies
- `Dockerfile` Render-friendly container
- `SETUP_GITHUB_AND_RENDER.md` Git/GitHub/Render instructions

## Notes

- SQLite database stored at `app/traders.db`
- Tables auto-created on startup
# Global Roster

## Overview

Global Roster is a web application for managing trader scheduling across multiple locations and sports. The project is being built incrementally in phases, with each phase adding new functionality and features. Currently, **Phase 1 – Skeleton App** is implemented, which provides the foundational infrastructure including FastAPI setup, database configuration, template rendering, and static file serving.

## Tech Stack

- **FastAPI** – Modern Python web framework for building APIs and web applications
- **Uvicorn** – ASGI server for running FastAPI (with standard extras)
- **SQLAlchemy 2.0+** – ORM for database operations
- **Alembic** – Database migration tool
- **Jinja2** – Template engine for server-side rendering
- **SQLite** – Database backend (synchronous)
- **Pydantic 2.0+** – Data validation (installed but not yet used in Phase 1)
- **Python 3.11+** – Minimum required Python version

**Architecture Notes:**
- The application uses **synchronous** database operations (SQLAlchemy synchronous engine)
- Database backend is **SQLite** with the file located at `global_roster/traders.db`
- FastAPI handles both sync and async routes; currently all routes are synchronous

## Project Structure

```
Global Roster/
├── pyproject.toml          # Project metadata and dependencies
├── requirements.txt        # Alternative dependency list for pip
├── alembic.ini             # Alembic configuration
├── README.md               # This file
│
├── global_roster/          # Main application package
│   ├── __init__.py
│   ├── main.py             # FastAPI app instance and routes
│   │
│   ├── core/               # Core configuration and utilities
│   │   ├── __init__.py
│   │   ├── config.py       # Path management and DATABASE_URL
│   │   ├── db.py           # SQLAlchemy engine, SessionLocal, get_db()
│   │   └── security.py     # Stub file (empty, reserved for future use)
│   │
│   ├── models/             # SQLAlchemy models
│   │   ├── __init__.py     # Exports Base
│   │   └── base.py         # Declarative base (Base = declarative_base())
│   │
│   ├── templates/          # Jinja2 HTML templates
│   │   ├── base.html       # Base layout template
│   │   └── home.html       # Home page template
│   │
│   └── static/             # Static assets
│       └── styles.css      # Main stylesheet
│
└── migrations/             # Alembic migration scripts
    ├── env.py              # Alembic environment (wired to Base.metadata)
    ├── script.py.mako      # Migration template
    └── README              # Alembic documentation
```

**Note:** The following directories do not yet exist but are planned for future phases:
- `global_roster/routes/` – API route handlers
- `global_roster/services/` – Business logic layer
- `global_roster/schemas/` – Pydantic models for request/response validation

## Current Implementation by Phase

### Phase 1 – Skeleton App

Phase 1 establishes the foundational infrastructure with no business logic.

**Modules Created:**

1. **`global_roster/core/config.py`**
   - Computes project paths using `pathlib.Path`
   - Defines `BASE_DIR` (project root), `APP_DIR`, `TEMPLATES_DIR`, `STATIC_DIR`
   - Sets `DB_PATH` to `global_roster/traders.db`
   - Exports `DATABASE_URL` as `sqlite:///{DB_PATH}` (with forward slashes for Windows compatibility)

2. **`global_roster/core/db.py`**
   - Creates SQLAlchemy engine using `DATABASE_URL` from config
   - Defines `SessionLocal` sessionmaker (synchronous)
   - Implements `get_db()` FastAPI dependency function that yields database sessions

3. **`global_roster/models/base.py`**
   - Creates SQLAlchemy declarative base: `Base = declarative_base()`
   - No table models defined yet

4. **`global_roster/main.py`**
   - Creates FastAPI app instance: `app = FastAPI(title="Global Roster")`
   - Mounts static files at `/static` using `StaticFiles(directory=STATIC_DIR)`
   - Configures Jinja2 templates with `Jinja2Templates(directory=TEMPLATES_DIR)`
   - Defines single route: `GET /` → `read_home()` → renders `home.html`

5. **`global_roster/core/security.py`**
   - Empty stub file (reserved for future authentication/authorization)

**Templates:**

- `templates/base.html` – Base layout with `<header>` containing "Global Roster" title and `<main>` content block
- `templates/home.html` – Extends `base.html`, displays "Global Roster – Phase 1" heading and success message

**Static Assets:**

- `static/styles.css` – Responsive CSS with system font stack, centered layout (max-width 960px), header styling, and card-like main content area

**Database Setup:**

- SQLite database file location: `global_roster/traders.db` (created automatically on first use)
- Database URL format: `sqlite:///{absolute_path}` (uses forward slashes via `Path.as_posix()`)
- Alembic configured to use `Base.metadata` from `global_roster.models.base`
- Alembic `env.py` overrides `sqlalchemy.url` from `alembic.ini` with `DATABASE_URL` from `core.config` for consistency

## Backend Architecture

### FastAPI Application

The FastAPI app is instantiated in `global_roster/main.py`:

```python
app = FastAPI(title="Global Roster")
```

**Static Files Configuration:**
- Mounted at `/static` route
- Serves files from `global_roster/static/` directory
- Uses `StaticFiles` with directory path converted to string

**Template Configuration:**
- Jinja2 templates loaded from `global_roster/templates/` directory
- Template directory path converted to string for compatibility
- Templates instance available as `templates` in `main.py`

**Database Session Management:**
- Engine created in `global_roster/core/db.py` using `create_engine(DATABASE_URL)`
- `SessionLocal` is a `sessionmaker` bound to the engine
- `get_db()` is a FastAPI dependency function that:
  - Creates a new session from `SessionLocal`
  - Yields the session to the route handler
  - Closes the session in a `finally` block

### API Routes

Currently, only one route is implemented:

| HTTP Method | Path | Handler Function | Response Type |
|-------------|------|------------------|---------------|
| GET | `/` | `read_home(request: Request)` | `HTMLResponse` (renders `home.html`) |

**Additional Auto-Generated Routes:**
- `GET /docs` – Swagger UI documentation
- `GET /redoc` – ReDoc documentation
- `GET /openapi.json` – OpenAPI schema

## Database & Models

### Current Models

**Base Model:**
- `Base` (from `global_roster.models.base`) – SQLAlchemy declarative base
  - No tables defined yet
  - Ready for model classes to inherit from in future phases

### Database Configuration

- **Database Type:** SQLite
- **Database File:** `global_roster/traders.db`
- **Connection URL:** `sqlite:///{absolute_path_to_traders.db}`
- **Location:** The database file is created in the `global_roster/` package directory (same level as `main.py`)
- **Session Management:** Synchronous sessions via `SessionLocal` from `core/db.py`

### Alembic Integration

- **Migration Script Location:** `migrations/`
- **Environment File:** `migrations/env.py`
- **Configuration:** 
  - `target_metadata = Base.metadata` (from `global_roster.models.base`)
  - `sqlalchemy.url` is overridden at runtime to use `DATABASE_URL` from `core.config`
  - This ensures Alembic uses the same database URL as the application

## Frontend (Templates & Static Assets)

### Templates

**Base Template (`templates/base.html`):**
- HTML5 document structure
- Includes `<link>` to `/static/styles.css`
- Contains `<header>` with "Global Roster" title
- Defines `<main>` content block using Jinja2 `{% block content %}`
- Mobile-responsive viewport meta tag

**Home Template (`templates/home.html`):**
- Extends `base.html` using `{% extends "base.html" %}`
- Fills content block with:
  - `<h1>Global Roster – Phase 1</h1>`
  - `<p>The app is running successfully.</p>`
- Rendered by `GET /` route

### Static Assets

**Stylesheet (`static/styles.css`):**
- System font stack for cross-platform compatibility
- Responsive design:
  - Body: light gray background (`#f5f5f5`)
  - Header: white background with bottom border
  - Main: centered container (max-width 960px), white background, rounded corners, subtle shadow
- Mobile-friendly padding and spacing

**Static File Serving:**
- Files served from `/static/` URL path
- Example: `/static/styles.css` serves `global_roster/static/styles.css`

## Local Development / Running the App

### Prerequisites

- Python 3.11 or higher
- pip (Python package manager)

### Setup Steps

1. **Create Virtual Environment:**
   ```bash
   python -m venv .venv
   ```

2. **Activate Virtual Environment:**
   - **Windows:**
     ```bash
     .venv\Scripts\activate
     ```
   - **macOS/Linux:**
     ```bash
     source .venv/bin/activate
     ```

3. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
   Or alternatively (if using editable install):
   ```bash
   pip install -e .
   ```

### Running the Development Server

Start the FastAPI development server:

```bash
uvicorn global_roster.main:app --reload --port 8000
```

The `--reload` flag enables auto-reload on code changes.

**Access the Application:**
- Home page: http://127.0.0.1:8000/
- API documentation: http://127.0.0.1:8000/docs
- ReDoc documentation: http://127.0.0.1:8000/redoc

### Database Migrations

**Important:** Alembic migrations expect `DATABASE_URL` to be imported from `global_roster.core.config`. The `migrations/env.py` file overrides the `sqlalchemy.url` from `alembic.ini` with the value from the config module to ensure consistency.

**Create a New Migration:**
```bash
alembic revision --autogenerate -m "create tables"
```

**Apply Migrations:**
```bash
alembic upgrade head
```

**Note:** Currently, no migrations exist because no table models have been defined yet. The first migration will be created in Phase 2 when models are added.

### Gotchas

- **Path Handling:** The application uses `pathlib.Path` objects internally but converts them to strings when passing to FastAPI's `StaticFiles` and `Jinja2Templates` for compatibility
- **Windows Paths:** Database URLs use forward slashes (via `Path.as_posix()`) to ensure SQLite compatibility on Windows
- **Database File:** The `traders.db` file will be created automatically when the database engine is first used or when Alembic runs migrations
- **Alembic URL Override:** `migrations/env.py` programmatically sets the database URL from `core.config`, so changes to `alembic.ini`'s `sqlalchemy.url` are ignored at runtime

## Extensibility / Next Phases

The following are **planned** features and have not yet been implemented:

- **Models (`global_roster/models/`):**
  - `Trader` model – representing individual traders with attributes like name, location, availability
  - `Preference` model – trader scheduling preferences and constraints
  - Additional models for sports, locations, and schedule management

- **Routes (`global_roster/routes/`):**
  - API endpoints for CRUD operations on traders
  - Endpoints for managing preferences
  - Schedule generation and viewing routes

- **Schemas (`global_roster/schemas/`):**
  - Pydantic models for request validation
  - Response models for API endpoints
  - Data transfer objects (DTOs)

- **Services (`global_roster/services/`):**
  - Business logic for trader management
  - Schedule generation algorithms
  - Preference matching and conflict resolution

- **Authentication & Authorization:**
  - Implementation in `core/security.py`
  - User authentication system
  - Role-based access control

- **Additional Templates:**
  - Trader listing and detail pages
  - Schedule view templates
  - Forms for creating/editing traders and preferences
