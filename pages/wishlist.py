"""Wishlist management page."""

from nicegui import ui, app
from datetime import datetime
from auth import require_auth
from components.layout import page_layout
from components.kpi_card import kpi_card
from data import get_wishlist_items, update_wishlist_status, delete_wishlist_item, get_wishlist_stats


@ui.page("/wishlist")
@require_auth()
async def wishlist_page():
    """Wishlist page with pending items and actions."""
    
    tenant_id = app.storage.user.get("tenant_id")
    
    # Pagination state
    page_state = {"current": 0, "limit": 20, "total": 0}
    
    # UI element references (will be assigned later)
    status_select = None
    stats_label = None
    table_container = None
    page_label = None
    prev_btn = None
    next_btn = None
    
    def format_datetime(dt_str: str) -> str:
        """Format datetime for display."""
        if not dt_str:
            return "—"
        try:
            dt = datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
            return dt.strftime("%d.%m.%Y %H:%M")
        except Exception:
            return dt_str[:16]
    
    def format_date(date_str: str | None) -> str:
        """Format date from meta (YYYY-MM-DD or DD.MM) to DD.MM.YYYY."""
        if not date_str:
            return "—"
        try:
            # Try YYYY-MM-DD format first
            dt = datetime.strptime(date_str, "%Y-%m-%d")
            return dt.strftime("%d.%m.%Y")
        except ValueError:
            return date_str  # Return as-is if already formatted (DD.MM)
    
    def format_time_preference(pref: str | None) -> str:
        """Convert time preference to Russian."""
        mapping = {
            "morning": "Утро",
            "day": "День",
            "evening": "Вечер",
        }
        return mapping.get(pref, "—") if pref else "—"
    
    def get_status_badge(status: str) -> tuple[str, str]:
        """Get status display text."""
        mapping = {
            "pending": ("Ожидает", "bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400"),
            "converted": ("Обработано", "bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400"),
            "cancelled": ("Отменено", "bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400"),
        }
        return mapping.get(status, (status, "bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-400"))
    
    async def refresh_table():
        """Refresh wishlist table."""
        nonlocal status_select, stats_label, table_container, page_label, prev_btn, next_btn
        
        if not tenant_id:
            return
        
        data, total = get_wishlist_items(
            tenant_id=tenant_id,
            status_filter=status_select.value if status_select else "pending",
            limit=page_state["limit"],
            offset=page_state["current"] * page_state["limit"],
        )
        
        page_state["total"] = total
        total_pages = max(1, (total + page_state["limit"] - 1) // page_state["limit"])
        
        if stats_label:
            stats_label.text = f"Найдено: {total} заявок"
        if page_label:
            # Simple "1 / 5" style
            page_label.text = f"{page_state['current'] + 1} / {total_pages}"
        
        if prev_btn:
            prev_btn.set_enabled(page_state["current"] > 0)
        if next_btn:
            next_btn.set_enabled(page_state["current"] < total_pages - 1)
        
        if table_container:
            table_container.clear()
            with table_container:
                if not data:
                    ui.label("Нет заявок").classes("text-grey text-center py-8")
                    return
                
                # Table header
                with ui.row().classes("w-full bg-gray-100 dark:bg-gray-800 py-3 px-4 rounded-t-lg gap-4"):
                    ui.label("Клиент").classes("w-32 font-semibold text-gray-600 dark:text-gray-300 text-sm")
                    ui.label("Услуга").classes("w-44 font-semibold text-gray-600 dark:text-gray-300 text-sm")
                    ui.label("Мастер").classes("w-24 font-semibold text-gray-600 dark:text-gray-300 text-sm")
                    ui.label("Желаемая дата").classes("w-28 font-semibold text-gray-600 dark:text-gray-300 text-sm")
                    ui.label("Время").classes("w-16 font-semibold text-gray-600 dark:text-gray-300 text-sm")
                    ui.label("Статус").classes("w-24 font-semibold text-gray-600 dark:text-gray-300 text-sm")
                    ui.label("Действия").classes("w-28 font-semibold text-gray-600 dark:text-gray-300 text-sm")
                
                # Table rows
                for row in data:
                    item_id = row.get("id")
                    client_info = row.get("clients_v2") or {}
                    client_name = client_info.get("full_name") or "—"
                    client_phone = client_info.get("phone") or "—"
                    
                    # Extract human-readable data from meta JSON
                    meta = row.get("meta") or {}
                    service_title = meta.get("service_title") or row.get("item_id") or "—"
                    staff_name = meta.get("staff_name") or "—"
                    preferred_date = format_date(meta.get("date"))
                    time_pref = format_time_preference(meta.get("time_preference"))
                    
                    with ui.row().classes("w-full py-3 px-4 border-b border-gray-200 dark:border-gray-700 gap-4 hover:bg-gray-50 dark:hover:bg-gray-800/50 items-center transition-colors"):
                        ui.label(client_name).classes("w-32 font-medium text-gray-800 dark:text-gray-200 text-sm truncate")
                        ui.label(service_title).classes("w-44 text-gray-800 dark:text-gray-200 text-sm truncate").tooltip(service_title)
                        ui.label(staff_name).classes("w-24 text-gray-500 dark:text-gray-400 text-sm truncate")
                        ui.label(preferred_date).classes("w-28 text-gray-800 dark:text-gray-200 text-sm")
                        ui.label(time_pref).classes("w-16 text-gray-500 dark:text-gray-400 text-sm")
                        
                        # Status badge
                        status_text, status_class = get_status_badge(row.get("status", ""))
                        ui.label(status_text).classes(f"w-24 px-2 py-1 rounded-full text-xs font-medium text-center {status_class}")
                        
                        with ui.row().classes("w-28 gap-1"):
                            # Mark processed button
                            if row.get("status") == "pending":
                                ui.button(
                                    icon="check",
                                    on_click=lambda iid=item_id: mark_processed(iid)
                                ).props("flat round dense color=positive").tooltip("Обработано")
                                
                                # Cancel button
                                ui.button(
                                    icon="close",
                                    on_click=lambda iid=item_id: mark_cancelled(iid)
                                ).props("flat round dense color=warning").tooltip("Отменить")
                            
                            # Contact button
                            ui.button(
                                icon="phone",
                                on_click=lambda name=client_name, phone=client_phone: show_contact_dialog(name, phone)
                            ).props("flat round dense color=info").tooltip("Контакт")
                            
                            # Delete button
                            ui.button(
                                icon="delete",
                                on_click=lambda iid=item_id: confirm_delete(iid)
                            ).props("flat round dense color=negative").tooltip("Удалить")
    
    async def mark_processed(item_id: int):
        """Show amount input dialog and mark item as processed."""
        amount_value = {"value": 0}
        
        with ui.dialog() as dialog, ui.card().classes("w-80"):
            ui.label("💰 Укажите сумму").classes("text-h6")
            ui.label("Введите сумму заказа для этой заявки").classes("text-grey text-sm")
            ui.separator()
            
            amount_input = ui.number(
                label="Сумма (₽)",
                value=0,
                min=0,
                format="%.0f",
                on_change=lambda e: amount_value.update({"value": e.value or 0})
            ).classes("w-full my-4").props("suffix=₽")
            
            with ui.row().classes("w-full gap-2"):
                ui.button("Отмена", on_click=dialog.close).props("flat")
                
                async def do_save():
                    if update_wishlist_status(item_id, "converted", tenant_id, amount=amount_value["value"]):
                        ui.notify(f"Заявка обработана: {amount_value['value']:.0f} ₽", type="positive")
                        dialog.close()
                        await refresh_table()
                        await refresh_kpi()
                    else:
                        ui.notify("Ошибка при обновлении", type="negative")
                
                ui.button("Сохранить", on_click=do_save).props("color=positive")
        
        dialog.open()
    
    async def mark_cancelled(item_id: int):
        """Mark item as cancelled."""
        if update_wishlist_status(item_id, "cancelled", tenant_id):
            ui.notify("Заявка отменена", type="warning")
            await refresh_table()
            await refresh_kpi()
        else:
            ui.notify("Ошибка при обновлении", type="negative")
    
    def show_contact_dialog(client_name: str, phone: str):
        """Show contact info dialog."""
        with ui.dialog() as dialog, ui.card().classes("w-80"):
            ui.label(f"📞 Контакт: {client_name}").classes("text-h6")
            ui.separator()
            
            with ui.row().classes("items-center gap-2 my-4"):
                ui.icon("phone").classes("text-2xl text-primary")
                ui.label(phone).classes("text-h5 font-mono")
            
            if phone != "—":
                ui.button(
                    f"Позвонить {phone}",
                    on_click=lambda: ui.navigate.to(f"tel:{phone}")
                ).classes("w-full").props("color=primary")
            
            ui.button("Закрыть", on_click=dialog.close).classes("w-full").props("flat")
        
        dialog.open()
    
    async def confirm_delete(item_id: int):
        """Show delete confirmation dialog."""
        with ui.dialog() as dialog, ui.card().classes("w-80"):
            ui.label("⚠️ Удалить заявку?").classes("text-h6")
            ui.label("Это действие нельзя отменить.").classes("text-grey")
            
            with ui.row().classes("w-full gap-2 mt-4"):
                ui.button("Отмена", on_click=dialog.close).props("flat")
                
                async def do_delete():
                    if delete_wishlist_item(item_id, tenant_id):
                        ui.notify("Заявка удалена", type="warning")
                        dialog.close()
                        await refresh_table()
                        await refresh_kpi()
                    else:
                        ui.notify("Ошибка при удалении", type="negative")
                
                ui.button("Удалить", on_click=do_delete).props("color=negative")
        
        dialog.open()
    
    async def go_page(delta: int):
        """Navigate to next/prev page."""
        page_state["current"] = max(0, page_state["current"] + delta)
        await refresh_table()
    
    # KPI Cards row
    kpi_container = None


    
    async def refresh_kpi():
        """Refresh KPI cards."""
        nonlocal kpi_container
        if not tenant_id or not kpi_container:
            return
        stats = get_wishlist_stats(tenant_id)
        kpi_container.clear()
        with kpi_container:
            kpi_card("Ожидают", f"{stats['pending']}", "hourglass_empty")
            kpi_card("Заработано", f"{stats['total_revenue']:,.0f} ₽", "payments")
            kpi_card("Обработано", f"{stats['converted']}", "check_circle")
            kpi_card("Отменено", f"{stats['cancelled']}", "cancel")
    
    # Build UI
    with page_layout("Wishlist"):
        
        # KPI Cards (Grid layout)
        kpi_container = ui.element('div').classes("grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 w-full mb-6")
        
        # Filters row
        with ui.row().classes("w-full items-center gap-4 mb-6 p-4 rounded-xl shadow-sm theme-card"):
            ui.icon("filter_list").classes("text-gray-500 dark:text-gray-400")
            
            status_select = ui.select(
                {
                    "pending": "Ожидает", 
                    "converted": "Обработано", 
                    "cancelled": "Отменено",
                    "all": "Все"
                },
                value="pending",
                label="Статус"
            ).classes("w-40").props("outlined dense color=purple options-dense")
            
            ui.space()
            
            ui.button(icon="refresh", on_click=refresh_table).props("flat round color=purple").tooltip("Обновить таблицу")
        
        # Stats row
        stats_label = ui.label().classes("text-grey mb-2")
        
        # Table container
        table_container = ui.column().classes("w-full")
        
        # Pagination
        with ui.row().classes("w-full justify-center items-center gap-4 mt-6"):
            prev_btn = ui.button(icon="chevron_left", on_click=lambda: go_page(-1)).props("round flat color=grey-7").classes("dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-700")
            page_label = ui.label().classes("text-sm font-semibold text-gray-700 dark:text-gray-300 min-w-[3rem] text-center")
            next_btn = ui.button(icon="chevron_right", on_click=lambda: go_page(1)).props("round flat color=grey-7").classes("dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-700")
        
        # Bind status filter
        status_select.on_value_change(refresh_table)
        
        # Initial load
        await refresh_kpi()
        await refresh_table()
