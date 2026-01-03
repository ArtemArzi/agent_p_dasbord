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
    
    # Inject locale for this page (can also be global, but page-scope is safer for hot reload)
    from components.common import RU_LOCALE
    ui.add_body_html(f"<script> const ru_locale = {RU_LOCALE}; </script>")
    
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
    with page_layout("Обзор"):
        
        # Date range selector (Initialized with values)
        today = date.today()
        default_from = (today - timedelta(days=7)).isoformat()
        default_to = today.isoformat()
        
        with ui.row().classes("w-full items-center gap-4 mb-6 p-4 rounded-xl shadow-sm theme-card"):
            with ui.row().classes("items-center gap-2"):
                ui.icon("calendar_today").classes("text-gray-500 dark:text-gray-400")
                
                with ui.input("С даты", value=default_from).classes("w-36").props("outlined dense color=purple") as date_from_input:
                    with ui.menu().props("no-parent-event") as menu_from:
                        ui.date().bind_value(date_from_input).props("minimal color=purple :locale='ru_locale'").on("input", menu_from.close).classes("w-64")
                    with date_from_input.add_slot("append"):
                        ui.icon("edit_calendar").on("click", menu_from.open).classes("cursor-pointer text-gray-500 hover:text-purple-600 transition-colors")
                
                ui.label("-").classes("text-gray-400")
                
                with ui.input("По дату", value=default_to).classes("w-36").props("outlined dense color=purple") as date_to_input:
                    with ui.menu().props("no-parent-event") as menu_to:
                        ui.date().bind_value(date_to_input).props("minimal color=purple :locale='ru_locale'").on("input", menu_to.close).classes("w-64")
                    with date_to_input.add_slot("append"):
                        ui.icon("edit_calendar").on("click", menu_to.open).classes("cursor-pointer text-gray-500 hover:text-purple-600 transition-colors")
                
                ui.button(icon="search", on_click=refresh_data).props("flat round color=purple").tooltip("Применить")
            
            ui.separator().props("vertical").classes("mx-2 hidden sm:block")
            
            # Quick preset buttons
            with ui.row().classes("gap-2"):
                ui.button("Сегодня", on_click=lambda: set_preset(0)).props("unelevated dense rounded color=purple-1 text-color=purple-8").classes("dark:bg-purple-900/30 dark:text-purple-300 font-medium")
                ui.button("Вчера", on_click=lambda: set_preset(1)).props("unelevated dense rounded color=purple-1 text-color=purple-8").classes("dark:bg-purple-900/30 dark:text-purple-300 font-medium")
                ui.button("Неделя", on_click=lambda: set_preset(7)).props("unelevated dense rounded color=purple-1 text-color=purple-8").classes("dark:bg-purple-900/30 dark:text-purple-300 font-medium")
                ui.button("Месяц", on_click=lambda: set_preset(30)).props("unelevated dense rounded color=purple-1 text-color=purple-8").classes("dark:bg-purple-900/30 dark:text-purple-300 font-medium")
        
        # KPI Cards container (Grid layout)
        kpi_row = ui.element('div').classes("grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 w-full mb-6")
        
        # Funnel Chart container
        with ui.card().classes("w-full p-4 bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 shadow-sm"):
            ui.label("Воронка конверсии").classes("text-lg font-semibold mb-4 text-gray-800 dark:text-white")
            funnel_container = ui.column().classes("w-full")
        
        # Initial load
        await refresh_data()
