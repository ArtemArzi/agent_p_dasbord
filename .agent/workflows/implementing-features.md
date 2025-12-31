---
description: Generates Python code, SQL, and NiceGUI components for the Dashboard. Use when the user asks to write code, build a page, or fix a bug.
---

# Feature Implementation

## Overview
Writes production-ready Python code using the NiceGUI framework and Supabase client, following the project's established patterns.

## When to use this skill
**Triggers:**
- "Write the code for..."
- "Implement the login logic"
- "Create the database migration for..."

**Anti-Triggers:**
- Do NOT use for high-level architectural planning (use `planning-features`).

## Objective & Boundaries
**Goal:** Generate runnable, type-hinted Python code.
**Permissions:** Assumes access to `config.py` settings and `get_supabase()` client.

## Inputs
- Implementation plan or specific coding task.
- Target file paths.

## Outputs
**Format:** Python code blocks or SQL blocks.

## Workflow
1. **Model Definition:** Create/Update Pydantic models in `models.py` to match DB schema.
2. **Data Layer:** Implement async functions in `data.py` using the `_supabase` client.
   - *Check:* Use `select("*")` or specific columns. Handle empty results.
3. **UI Implementation:** Create pages in `pages/` using `nicegui`.
   - *Pattern:* Use `@ui.page("/")` and `@require_auth`.
   - *Layout:* Wrap content in `components.layout.page_layout`.
4. **Integration:** Connect UI events to Data functions using `async/await`.

## Guardrails
- **Sync vs Async:** Always use `async def` for DB operations and UI event handlers.
- **State Management:** Use `app.storage.user` for session data. Do not use global variables for user state.
- **SQL Injection:** Always use Supabase builder methods (`.eq()`, `.insert()`), never raw f-strings for SQL queries.

## Quality Bar
- [ ] Code is fully typed (`def func() -> return_type:`).
- [ ] NiceGUI components use standard styling classes (Tailwind/Quasar).
- [ ] Imports are absolute (e.g., `from components.layout import ...`).

## Examples
**Input:** "Create a query to get clients."
**Output:**
```python
async def get_clients(tenant_id: str) -> list[Client]:
    sb = get_supabase()
    res = sb.table("clients_v2").select("*").eq("tenant_id", tenant_id).execute()
    return [Client(**row) for row in res.data]