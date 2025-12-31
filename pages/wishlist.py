"""Wishlist management page."""

from nicegui import ui, app
from datetime import datetime
from auth import require_auth
from components.layout import page_layout
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
    
    def get_status_badge(status: str) -> str:
        """Get status display text."""
        mapping = {
            "pending": "🕐 Ожидает",
            "converted": "✅ Обработано",
            "cancelled": "❌ Отменено",
        }
        return mapping.get(status, status)
    
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
            page_label.text = f"Страница {page_state['current'] + 1} из {total_pages}"
        
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
                with ui.row().classes("w-full bg-dark py-2 px-4 rounded-t gap-4"):
                    ui.label("Клиент").classes("w-36 font-bold")
                    ui.label("Услуга").classes("w-40 font-bold")
                    ui.label("Дата").classes("w-32 font-bold")
                    ui.label("Комментарий").classes("w-48 font-bold")
                    ui.label("Статус").classes("w-28 font-bold")
                    ui.label("Действия").classes("w-32 font-bold")
                
                # Table rows
                for row in data:
                    item_id = row.get("id")
                    client_info = row.get("clients_v2") or {}
                    client_name = client_info.get("full_name") or "—"
                    client_phone = client_info.get("phone") or "—"
                    
                    with ui.row().classes("w-full py-2 px-4 border-b border-gray-700 gap-4 hover:bg-gray-800 items-center"):
                        ui.label(client_name).classes("w-36")
                        ui.label(row.get("item_id") or row.get("item_type") or "—").classes("w-40 text-grey")
                        ui.label(format_datetime(row.get("created_at"))).classes("w-32")
                        ui.label(row.get("comment") or "—").classes("w-48 text-grey truncate")
                        ui.label(get_status_badge(row.get("status", ""))).classes("w-28")
                        
                        with ui.row().classes("w-32 gap-1"):
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
            with ui.card().classes("bg-green-900 p-4"):
                ui.label("💰 Заработано").classes("text-grey text-sm")
                ui.label(f"{stats['total_revenue']:,.0f} ₽").classes("text-2xl font-bold text-green-400")
            with ui.card().classes("bg-blue-900 p-4"):
                ui.label("✅ Конвертировано").classes("text-grey text-sm")
                ui.label(f"{stats['converted']}").classes("text-2xl font-bold text-blue-400")
            with ui.card().classes("bg-orange-900 p-4"):
                ui.label("🕐 Ожидают").classes("text-grey text-sm")
                ui.label(f"{stats['pending']}").classes("text-2xl font-bold text-orange-400")
            with ui.card().classes("bg-red-900 p-4"):
                ui.label("❌ Отменено").classes("text-grey text-sm")
                ui.label(f"{stats['cancelled']}").classes("text-2xl font-bold text-red-400")
    
    # Build UI
    with page_layout("📋 Wishlist"):
        
        # KPI Cards
        kpi_container = ui.row().classes("w-full gap-4 mb-6")
        
        # Filters row
        with ui.row().classes("w-full gap-4 mb-4 items-center"):
            status_select = ui.select(
                {"pending": "🕐 Ожидают", "converted": "✅ Обработаны", "cancelled": "❌ Отменены", "all": "Все"},
                value="pending",
                label="Статус"
            ).classes("w-48")
            
            ui.button("Обновить", icon="refresh", on_click=refresh_table).props("flat")
        
        # Stats row
        stats_label = ui.label().classes("text-grey mb-2")
        
        # Table container
        table_container = ui.column().classes("w-full")
        
        # Pagination
        with ui.row().classes("w-full justify-center gap-2 mt-4"):
            prev_btn = ui.button("← Назад", on_click=lambda: go_page(-1)).props("flat")
            page_label = ui.label()
            next_btn = ui.button("Вперёд →", on_click=lambda: go_page(1)).props("flat")
        
        # Bind status filter
        status_select.on_value_change(refresh_table)
        
        # Initial load
        await refresh_kpi()
        await refresh_table()
