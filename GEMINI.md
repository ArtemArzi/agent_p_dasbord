# Agent P Dashboard: Project Structure and Working Guide

## Scope
- Source: docs/00_ARCHITECTURE.md through docs/05_PHASE1_MVP.md.
- Excludes docs/06_PHASE2_FEATURES.md and docs/07_PHASE3_MINIAPP.md.
- Phase 2 items are included only when they appear in docs/00-05.

## Architecture Summary
- Ecosystem: Agent P Bot (Python/Aiogram) writes to Supabase public.*; Dashboard (Python/NiceGUI) reads public.* and writes dashboard.*.
- Strategy: Python-native stack with NiceGUI (FastAPI under the hood).
- Auth: Supabase Auth + custom dashboard.users table.
- Realtime: Supabase Realtime (WebSockets).
- Deploy: Docker + Coolify.

## Project Structure
```
agent-p-dashboard/
├── main.py                 # NiceGUI entrypoint
├── config.py               # Settings (env vars)
├── auth.py                 # Auth + middleware
├── data.py                 # Supabase queries (DAL) — 12 functions
├── models.py               # Pydantic models
├── pages/
│   ├── login.py            # Login page
│   ├── overview.py         # KPI + funnel
│   ├── sessions.py         # Dialog sessions
│   ├── wishlist.py         # Wishlist management
│   ├── clients.py          # Client list (Phase 2 polish)
│   └── settings.py         # Tenant settings (admin/owner/super_admin)
├── components/
│   ├── layout.py           # Shared layout + tenant selector
│   ├── sidebar.py          # Navigation drawer
│   ├── kpi_card.py         # KPI card
│   ├── chat_viewer.py      # Dialog viewer
│   └── funnel_chart.py     # Funnel chart
├── jobs/
│   └── metrics_collector.py # Daily metrics aggregation (optional for MVP, used for history)
├── static/
│   └── logo.png
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── README.md
```

## Backend Responsibilities (docs/01)
- Data Access Layer: Supabase client + queries for KPI, sessions, wishlist, clients, tenant settings.
- Auth: bcrypt password verification, login flow, require_auth decorator.
- Background Jobs: Script `jobs/metrics_collector.py` to aggregate daily metrics (optional optimization).

## Frontend Responsibilities (docs/02)
- NiceGUI pages: login, overview, sessions, wishlist, clients, settings.
- Shared layout: header + sidebar, role-based navigation, tenant selector for super_admin.
- Sessions: table with filters + dialog viewer for history.
- Wishlist: table with actions (converted/cancelled status).
- Settings: tenant metadata editing form.

## Configuration (docs/01)
Required env vars:
- SUPABASE_URL
- SUPABASE_SERVICE_KEY (service_role for dashboard.* writes)
- APP_SECRET

Optional:
- APP_PORT (default 8080)
- DEBUG (default false)

## Database Model (docs/03)
- Schemas:
  - public.*: bot data, read-only for Dashboard.
  - dashboard.*: Dashboard-owned data, read/write.

Key public tables:
- tenants_v2 (metadata contains yclients and branch settings)
- clients_v2
- conversation_sessions_v2 (session analytics)
- recent_history_v2 (message history)
- wishlist_v2 (status: pending/converted/cancelled, processed_at)
- user_ltm_v2 (preferences)

Key dashboard tables:
- users (roles: super_admin, admin, owner, staff)
- metrics_dailies (daily KPI)
- alerts, audits, conversations, bookings

## Commands and Entry Points
- Install deps (Dockerfile): `pip install --no-cache-dir -r requirements.txt`
- Run app (Dockerfile entrypoint): `python main.py`
- Docker: Dockerfile exposes port 8080; docker-compose.yml exists for local dev.

---

## Implementation Status (Updated: 2025-12-31)

### Phase 1 MVP: ✅ Complete + Bug Fixes

| Chunk | Status | Key Files |
|-------|--------|-----------|
| 1. Foundation | ✅ | `config.py`, `auth.py`, `data.py`, `models.py`, `pages/login.py` |
| 2. Core Pages | ✅ | `pages/overview.py`, `pages/sessions.py`, `components/kpi_card.py`, `components/funnel_chart.py` |
| 3. Wishlist | ✅ | `pages/wishlist.py` |
| 4. Settings | ✅ | `pages/settings.py` (tenant metadata form) |

### Data Layer Functions (data.py)
- `get_user_by_email()` — Auth
- `get_tenants()` — Tenant selector (super_admin only)
- `get_tenant_settings()`, `update_tenant_metadata()` — Settings page
- `get_kpi_summary()`, `get_funnel_data()` — Overview
- `get_sessions()`, `get_session_history()` — Sessions
- `get_wishlist_items()`, `update_wishlist_status()`, `delete_wishlist_item()` — Wishlist

### Security Measures
- `@require_auth` on all protected pages
- `tenant_id` filter on all queries
- Authorization check on `update_tenant_metadata()`
- Input validation (closing_time HH:MM, admin_chat_id numeric)
- Sensitive token filtering in debug views

### Bug Fixes (2025-12-31)
- Wishlist: status 'processed' → 'converted' to match DB
- Settings: full implementation with metadata form
- Authorization: added user_role/user_tenant_id checks
- Validation: closing_time format, admin_chat_id type

### Pending
- **Deploy** — Docker + Coolify (deferred)

### Detailed Progress
See `docs/08_PROGRESS.md` for full implementation details.
