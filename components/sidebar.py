"""Sidebar navigation component."""

from nicegui import ui, app


def create_sidebar() -> ui.left_drawer:
    """
    Create navigation sidebar.
    Returns the drawer element for toggle control.
    """
    
    with ui.left_drawer(value=True).classes("bg-dark") as drawer:
        # Logo section
        with ui.column().classes("w-full items-center py-4"):
            ui.icon("smart_toy", size="48px").classes("text-primary")
            ui.label("Agent P").classes("text-h6 text-white")
        
        ui.separator()
        
        # Menu items
        menu_items = [
            ("/overview", "📈 Обзор", "dashboard"),
            ("/sessions", "💬 Диалоги", "chat"),
            ("/wishlist", "📋 Wishlist", "list"),
        ]
        
        # Settings for super_admin and owner only
        user_role = app.storage.user.get("role", "")
        if user_role in ("super_admin", "owner"):
            menu_items.append(("/settings", "⚙️ Настройки", "settings"))
        
        with ui.column().classes("w-full gap-1 p-2"):
            for path, label, icon in menu_items:
                ui.button(
                    label,
                    icon=icon,
                    on_click=lambda p=path: ui.navigate.to(p)
                ).classes("w-full justify-start").props("flat color=white")
        
        # Spacer
        ui.space()
        
        # User info at bottom
        ui.separator()
        with ui.column().classes("w-full p-2"):
            email = app.storage.user.get("email", "")
            role = app.storage.user.get("role", "")
            
            ui.label(email).classes("text-caption text-grey")
            ui.label(role.replace("_", " ").title()).classes("text-caption text-primary")
    
    return drawer
