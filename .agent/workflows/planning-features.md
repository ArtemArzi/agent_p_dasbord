---
description: Analyzes requirements and generates implementation plans for Agent P Dashboard. Use when the user requests a new feature, architecture changes, or roadmap planning.
---

# Feature Planning & Architecture

## Overview
Generates detailed, step-by-step implementation plans aligned with the Agent P Dashboard architecture (NiceGUI + Supabase + Python).

## When to use this skill
**Triggers:**
- "Plan the [feature name] module"
- "How should we implement [functionality]?"
- "Break down the task for [ticket]"

**Anti-Triggers:**
- Do NOT use for writing actual code (use `implementing-features`).
- Do NOT use for simple one-line fixes.

## Objective & Boundaries
**Goal:** Produce a Markdown-formatted plan covering Database, Backend, and Frontend layers.
**Boundaries:**
- Must strictly adhere to `00_ARCHITECTURE.md` (Python-only, no JS).
- Must respect Schema Separation (`public` is read-only, `dashboard` is read/write).

## Inputs
- Feature requirements or user story.
- Current project context (Phase 1 vs Phase 2).

## Outputs
**Format:** Markdown Checklist.
**Structure:**
1. **Database Layer:** SQL migrations, RLS policies.
2. **Backend Layer:** Pydantic models, Supabase queries (`data.py`).
3. **Frontend Layer:** NiceGUI components, page logic.
4. **Verification:** Success criteria.

## Workflow
1. **Contextual Analysis:** Check `05_PHASE1_MVP.md` and `00_ARCHITECTURE.md` to ensure the request fits the current phase.
2. **Schema Design:** Define SQL changes. Ensure strict separation of `dashboard.*` (writeable) vs `public.*` (read-only).
3. **Data Access Definition:** Plan the Pydantic models (`models.py`) and Supabase query functions (`data.py`).
4. **UI/UX Strategy:** Plan the NiceGUI layout using existing components (`components/layout.py`, `KPICard`).
5. **Security Check:** Explicitly define Auth requirements (`require_auth`) and RLS policies.

## Guardrails
- **Single Source of Truth:** Never plan data duplication from `public` to `dashboard` unless aggregating metrics.
- **Technology Constraint:** Do NOT suggest React, Vue, or raw HTML/JS. Use NiceGUI/Quasar wrappers.
- **Idempotency:** Plan database migrations to be idempotent (`IF NOT EXISTS`).

## Quality Bar
- [ ] Plan includes specific file paths (e.g., `pages/sessions.py`).
- [ ] Database migration SQL is provided.
- [ ] Auth scope is defined (Admin vs Super Admin).

## Examples
**Input:** "Plan the Wishlist feature."
**Output:**
```markdown
### 1. Database
- Update `wishlist_v2`: Add `status` column.
### 2. Backend
- Model: `WishlistItem` in `models.py`.
- Query: `get_pending_wishlist` in `data.py`.
### 3. Frontend
- Page: `pages/wishlist.py` with `ui.table`.