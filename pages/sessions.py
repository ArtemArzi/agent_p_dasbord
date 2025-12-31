"""Sessions page with filterable table and chat viewer."""

from nicegui import ui, app
from datetime import datetime
from auth import require_auth
from components.layout import page_layout
from components.chat_viewer import show_chat_dialog
from data import get_sessions


@ui.page("/sessions")
@require_auth()
async def sessions_page():
    """Sessions page with table, filters, and chat history viewer."""
    
    tenant_id = app.storage.user.get("tenant_id")
    
    # Pagination state
    page_state = {"current": 0, "limit": 20, "total": 0}
    
    # UI element references (will be assigned later)
    status_select = None
    date_from = None
    date_to = None
    stats_label = None
    table_container = None
    page_label = None
    prev_btn = None
    next_btn = None
    
    def format_datetime(dt_str: str) -> str:
        """Format datetime string for display."""
        if not dt_str:
            return "—"
        try:
            dt = datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
            return dt.strftime("%d.%m.%Y %H:%M")
        except Exception:
            return dt_str[:16]
    
    def get_status_badge(status: str) -> str:
        """Get status display text."""
        mapping = {
            "done": "✅ Завершён",
            "completed": "✅ Завершён",
            "booked": "📅 Записан",
            "abandoned": "⚠️ Прерван",
            "transferred": "🔄 Передан",
            "ghost": "👻 Призрак",
            "no_slots": "📵 Нет слотов",
            "price_too_high": "💰 Дорого",
        }
        return mapping.get(status, status)
    
    async def refresh_table():
        """Refresh sessions table."""
        nonlocal status_select, date_from, date_to, stats_label, table_container, page_label, prev_btn, next_btn
        
        if not tenant_id:
            return
        
        # Get data
        data, total = get_sessions(
            tenant_id=tenant_id,
            limit=page_state["limit"],
            offset=page_state["current"] * page_state["limit"],
            status_filter=status_select.value if status_select and status_select.value != "all" else None,
            date_from=date_from.value if date_from and date_from.value else None,
            date_to=date_to.value if date_to and date_to.value else None,
        )
        
        page_state["total"] = total
        total_pages = max(1, (total + page_state["limit"] - 1) // page_state["limit"])
        
        # Update stats
        if stats_label:
            stats_label.text = f"Найдено: {total} сессий"
        if page_label:
            page_label.text = f"Страница {page_state['current'] + 1} из {total_pages}"
        
        # Update pagination buttons
        if prev_btn:
            prev_btn.set_enabled(page_state["current"] > 0)
        if next_btn:
            next_btn.set_enabled(page_state["current"] < total_pages - 1)
        
        # Rebuild table
        if table_container:
            table_container.clear()
            with table_container:
                if not data:
                    ui.label("Нет данных").classes("text-grey text-center py-8")
                    return
                
                # Table header
                with ui.row().classes("w-full bg-dark py-2 px-4 rounded-t gap-4"):
                    ui.label("ID").classes("w-16 font-bold")
                    ui.label("Дата").classes("w-36 font-bold")
                    ui.label("Клиент").classes("w-40 font-bold")
                    ui.label("Статус").classes("w-32 font-bold")
                    ui.label("Intent").classes("w-24 font-bold")
                    ui.label("").classes("w-20 font-bold")
                
                # Table rows
                for row in data:
                    session_id = row.get("session_id")
                    client_info = row.get("clients_v2") or {}
                    client_name = client_info.get("full_name") or "—"
                    
                    with ui.row().classes("w-full py-2 px-4 border-b border-gray-700 gap-4 hover:bg-gray-800 items-center"):
                        ui.label(str(row.get("id", "—"))).classes("w-16 text-grey")
                        ui.label(format_datetime(row.get("started_at"))).classes("w-36")
                        ui.label(client_name).classes("w-40")
                        ui.label(get_status_badge(row.get("final_status", ""))).classes("w-32")
                        ui.label(row.get("final_intent") or "—").classes("w-24 text-grey")
                        
                        ui.button(
                            icon="visibility",
                            on_click=lambda sid=session_id, name=client_name, tid=tenant_id: show_chat_dialog(sid, name, tid)
                        ).props("flat round dense").tooltip("Просмотреть диалог")
    
    async def go_page(delta: int):
        """Navigate to next/prev page."""
        page_state["current"] = max(0, page_state["current"] + delta)
        await refresh_table()
    
    async def reset_filters():
        """Reset all filters."""
        nonlocal status_select, date_from, date_to
        if status_select:
            status_select.value = "all"
        if date_from:
            date_from.value = ""
        if date_to:
            date_to.value = ""
        page_state["current"] = 0
        await refresh_table()
    
    # Build UI
    with page_layout("💬 Диалоги"):
        
        # Filters row
        with ui.row().classes("w-full gap-4 mb-4 items-end"):
            status_select = ui.select(
                {
                    "all": "📊 Все",
                    "done": "✅ Завершён", 
                    "booked": "📅 Записан",
                    "abandoned": "⚠️ Прерван",
                    "transferred": "🔄 Передан",
                    "ghost": "👻 Призрак",
                },
                value="all",
                label="Статус"
            ).classes("w-48")
            
            date_from = ui.input(
                "С даты",
                placeholder="2025-01-01"
            ).classes("w-40").props("type=date")
            
            date_to = ui.input(
                "По дату",
                placeholder="2025-12-31"
            ).classes("w-40").props("type=date")
            
            ui.button("Применить", icon="search", on_click=refresh_table).props("color=primary")
            ui.button("Сбросить", icon="clear", on_click=reset_filters).props("flat")
        
        # Stats row
        stats_label = ui.label().classes("text-grey mb-2")
        
        # Table container
        table_container = ui.column().classes("w-full")
        
        # Pagination
        with ui.row().classes("w-full justify-center gap-2 mt-4"):
            prev_btn = ui.button("← Назад", on_click=lambda: go_page(-1)).props("flat")
            page_label = ui.label()
            next_btn = ui.button("Вперёд →", on_click=lambda: go_page(1)).props("flat")
        
        # Initial load
        await refresh_table()
