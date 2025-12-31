---
description: Reviews code for security, style, and logic errors, and executes test procedures. Use when the user asks to review a file, check for bugs, or validate a feature.
---

# Code Review & QA

## Overview
Validates implementation against the project's architecture, specifically checking for Supabase RLS breaches, Auth bypasses, and NiceGUI state leaks.

## When to use this skill
**Triggers:**
- "Review this file"
- "Are there any bugs in this logic?"
- "Verify the security of this query"

## Objective & Boundaries
**Goal:** Identify critical issues and suggest specific fixes.
**Boundaries:** Focus on logic and security, not just PEP8 formatting.

## Inputs
- Python code files (`pages/*.py`, `data.py`).
- SQL migrations.

## Outputs
**Format:** Review Report with "Critical", "Warning", and "Suggestion" sections.

## Workflow
1. **Security Audit:**
   - Check if `dashboard.users` writes are protected.
   - Verify `public.*` is treated as READ-ONLY in `data.py`.
   - Ensure `@require_auth` is present on protected pages.
2. **State Leak Check:** Ensure `app.storage.user` is used instead of module-level variables for user-specific data.
3. **Logic Validation:** Trace `await` calls to ensure UI doesn't freeze.
4. **Data Integrity:** Verify Pydantic models match the SQL schema provided in `03_DATABASE.md`.

## Guardrails
- **RLS Verification:** Flag any SQL query that bypasses `tenant_id` filtering (unless Super Admin).
- **Password Safety:** Flag any plain-text password handling; ensure `bcrypt` is used.

## Quality Bar
- [ ] All database queries filter by `tenant_id`.
- [ ] No mixing of synchronous blocking code in async handlers.
- [ ] Error handling (try/except) is present for external API calls.

## Examples
**Input:** Code snippet reading `public.clients_v2` without tenant filter.
**Output:**
> **CRITICAL:** The query `sb.table("clients_v2").select("*").execute()` is missing a `.eq("tenant_id", tenant_id)` filter. This violates multi-tenancy isolation.