"""KPI Card component."""

from nicegui import ui


def kpi_card(
    title: str, 
    value: str | int | float, 
    icon: str = "info",
    delta: str | None = None,
    delta_positive: bool = True
) -> None:
    """
    KPI Card component with icon, value, and optional delta indicator.
    """
    card = ui.card().classes("w-full p-4 rounded-xl theme-card shadow-sm transition-all hover:shadow-md")
    with card:
        with ui.row().classes("w-full items-start justify-between mb-2"):
            ui.label(title).classes("text-sm font-medium opacity-70 tracking-wide uppercase")
            
            # Icon with colored background
            with ui.element("div").classes("p-2 rounded-lg bg-purple-100 dark:bg-purple-900/30"):
                ui.icon(icon).classes("text-lg text-purple-600 dark:text-purple-400")
        
        # Value
        ui.label(value).classes("text-3xl font-bold tracking-tight mb-1")
        
        # Delta indicator
        if delta:
            color_text = "text-green-600 dark:text-green-400" if delta_positive else "text-red-600 dark:text-red-400"
            color_bg = "bg-green-50 dark:bg-green-900/20" if delta_positive else "bg-red-50 dark:bg-red-900/20"
            icon_name = "arrow_upward" if delta_positive else "arrow_downward"
            
            with ui.row().classes(f"items-center gap-1 mt-2 px-2 py-1 rounded-md {color_bg} self-start"):
                ui.icon(icon_name).classes(f"text-xs {color_text}")
                ui.label(delta).classes(f"text-xs font-medium {color_text}")
