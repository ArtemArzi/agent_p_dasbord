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
    
    Args:
        title: Card title (e.g., "Сессии")
        value: Main value to display
        icon: Material icon name
        delta: Optional change indicator (e.g., "+12%")
        delta_positive: Whether delta is positive (green) or negative (red)
    """
    with ui.card().classes("w-48 hover:shadow-lg transition-shadow"):
        with ui.row().classes("items-center gap-2 mb-2"):
            ui.icon(icon).classes("text-2xl text-primary")
            ui.label(title).classes("text-subtitle2 text-grey")
        
        ui.label(str(value)).classes("text-h4 font-bold")
        
        if delta:
            color = "text-positive" if delta_positive else "text-negative"
            icon_name = "trending_up" if delta_positive else "trending_down"
            with ui.row().classes("items-center gap-1"):
                ui.icon(icon_name).classes(f"text-sm {color}")
                ui.label(delta).classes(f"text-caption {color}")
