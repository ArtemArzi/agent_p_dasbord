"""Sidebar navigation component."""

from nicegui import ui, app


def create_sidebar() -> ui.left_drawer:
    """Create navigation sidebar. Returns the drawer element for toggle control."""
    
    # Keep sidebar dark for consistent contrast
    with ui.left_drawer(value=True).classes("bg-gray-900 border-r border-gray-800") as drawer:
        # Logo section with refined styling
        with ui.column().classes("w-full items-center py-8"):
            ui.label("AMICA").style(
                "font-family: 'Outfit', sans-serif; letter-spacing: 3px; font-weight: 300;"
            ).classes("text-4xl text-white")
            ui.label("Dashboard").style(
                "font-family: 'Outfit', sans-serif; letter-spacing: 4px;"
            ).classes("text-xs text-gray-500 uppercase mt-2")
        
        # Elegant divider with champagne accent
        with ui.row().classes("w-full px-6 mb-6"):
            ui.element("div").classes("flex-1 h-px bg-gradient-to-r from-transparent via-amber-200/30 to-transparent")
        
        # Menu items with refined typography
        menu_items = [
            ("/overview", "Обзор", "dashboard"),
            ("/sessions", "Диалоги", "forum"),
            ("/wishlist", "Wishlist", "favorite_border"),
        ]
        
        # Super admin users management
        user_role = app.storage.user.get("role", "")
        if user_role == "super_admin":
            menu_items.append(("/users", "Сотрудники", "people"))

        # Settings for super_admin and admin only
        if user_role in ("super_admin", "admin"):
            menu_items.append(("/settings", "Настройки", "tune"))
        
        with ui.column().classes("w-full gap-2 px-4"):
            for path, label, icon in menu_items:
                with ui.button(on_click=lambda p=path: ui.navigate.to(p)).classes(
                    "w-full justify-start py-3 px-4 rounded-xl "
                    "text-gray-400 hover:text-white hover:bg-white/5 "
                    "transition-all duration-200 group"
                ).props("flat no-caps"):
                    ui.icon(icon).classes(
                        "text-xl mr-4 text-gray-500 group-hover:text-amber-200/80 transition-colors"
                    )
                    ui.label(label).style(
                        "font-family: 'Outfit', sans-serif; font-weight: 400; letter-spacing: 0.5px;"
                    ).classes("text-base")
        
        ui.space()
        
        # Version at bottom with subtle styling
        with ui.column().classes("w-full p-6 items-center"):
            ui.label("v1.0.0").style("font-family: 'Outfit', sans-serif;").classes("text-xs text-gray-700 tracking-wider")
    
    return drawer
