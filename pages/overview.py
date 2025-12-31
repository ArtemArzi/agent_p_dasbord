"""Overview page with KPI cards and funnel chart."""

from nicegui import ui, app
from datetime import date, timedelta
from auth import require_auth
from components.layout import page_layout
from components.kpi_card import kpi_card
from components.funnel_chart import funnel_chart
from data import get_kpi_summary, get_funnel_data


@ui.page("/overview")
@require_auth()
async def overview_page():
    """Overview page with KPIs and conversion funnel."""
    
    tenant_id = app.storage.user.get("tenant_id")
    
    # UI element references
    date_from_input = None
    date_to_input = None
    kpi_row = None
    funnel_container = None
    
    async def refresh_data():
        """Refresh all data based on selected date range."""
        nonlocal date_from_input, date_to_input, kpi_row, funnel_container
        
        date_from = date_from_input.value if date_from_input else None
        date_to = date_to_input.value if date_to_input else None
        
        # Clear and rebuild KPI cards
        if kpi_row:
            kpi_row.clear()
            with kpi_row:
                if tenant_id:
                    kpi = get_kpi_summary(tenant_id, date_from=date_from, date_to=date_to)
                    
                    kpi_card("Сессии", kpi["sessions"], icon="chat")
                    kpi_card("Записи", kpi["bookings"], icon="event_available")
                    kpi_card("Конверсия", f"{kpi['conversion']}%", icon="trending_up")
                    kpi_card("Доход", f"{kpi['revenue']:,.0f} ₽", icon="payments")
                else:
                    ui.label("Tenant не настроен").classes("text-warning")
        
        # Clear and rebuild funnel
        if funnel_container:
            funnel_container.clear()
            with funnel_container:
                if tenant_id:
                    funnel_data = get_funnel_data(tenant_id, date_from=date_from, date_to=date_to)
                    funnel_chart(funnel_data)
                else:
                    ui.label("Нет данных").classes("text-grey")
    
    def set_preset(days: int):
        """Set date preset."""
        nonlocal date_from_input, date_to_input
        today = date.today()
        if days == 0:  # Today
            date_from_input.value = today.isoformat()
            date_to_input.value = today.isoformat()
        elif days == 1:  # Yesterday
            yesterday = today - timedelta(days=1)
            date_from_input.value = yesterday.isoformat()
            date_to_input.value = yesterday.isoformat()
        else:  # Week/Month
            date_from_input.value = (today - timedelta(days=days)).isoformat()
            date_to_input.value = today.isoformat()
    
    # Build UI
    with page_layout("📈 Обзор"):
        
        # Date range selector
        with ui.row().classes("w-full items-end gap-4 mb-4"):
            date_from_input = ui.input(
                "С даты",
                value=(date.today() - timedelta(days=7)).isoformat()
            ).classes("w-40").props("type=date")
            
            date_to_input = ui.input(
                "По дату",
                value=date.today().isoformat()
            ).classes("w-40").props("type=date")
            
            # Quick preset buttons
            ui.button("Сегодня", on_click=lambda: set_preset(0)).props("flat dense")
            ui.button("Вчера", on_click=lambda: set_preset(1)).props("flat dense")
            ui.button("Неделя", on_click=lambda: set_preset(7)).props("flat dense")
            ui.button("Месяц", on_click=lambda: set_preset(30)).props("flat dense")
            
            ui.button("Применить", icon="search", on_click=refresh_data).props("color=primary")
        
        # KPI Cards container
        kpi_row = ui.row().classes("w-full gap-4 mb-6")
        
        # Funnel Chart container
        with ui.card().classes("w-full"):
            ui.label("Воронка конверсии").classes("text-h6 mb-2")
            funnel_container = ui.column().classes("w-full")
        
        # Initial load
        await refresh_data()
