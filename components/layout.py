"""Shared page layout component."""

from contextlib import contextmanager
from nicegui import ui, app
from components.sidebar import create_sidebar
from auth import logout


@contextmanager
def page_layout(title: str):
    """
    Shared layout with header and sidebar.
    
    Usage:
        with page_layout("Page Title"):
            ui.label("Content here")
    """
    # Enable dark mode
    ui.dark_mode().enable()
    
    # Header
    with ui.header().classes("bg-primary items-center px-4"):
        menu_button = ui.button(
            icon="menu", 
            on_click=lambda: sidebar.toggle()
        ).props("flat color=white round")
        
        ui.label(title).classes("text-h6 text-white ml-2")
        
        ui.space()
        
        # Super Admin Tenant Selector
        user_role = app.storage.user.get("role", "")
        if user_role == "super_admin":
            from data import get_tenants  # Lazy import to avoid circular dep if any
            
            try:
                tenants = get_tenants()
                print(f"DEBUG layout.py: get_tenants returned {len(tenants)} tenants: {tenants}")
                
                if not tenants:
                    ui.label("Нет доступных салонов").classes("text-warning text-caption")
                else:
                    # Create options dict: id (as string) -> name
                    options = {str(t["id"]): t.get("name") or "Unnamed Salon" for t in tenants}
                    
                    # Get current tenant and ensure it's a string for comparison
                    current_tenant = app.storage.user.get("tenant_id")
                    if current_tenant:
                        current_tenant = str(current_tenant)
                    print(f"DEBUG layout.py: current_tenant = {current_tenant}")
                    
                    # If no tenant selected and we have tenants, select first one automatically
                    if not current_tenant and options:
                        first_id = list(options.keys())[0]
                        app.storage.user["tenant_id"] = first_id
                        current_tenant = first_id
                        print(f"DEBUG layout.py: auto-selected tenant {first_id}")
                    
                    def on_tenant_change(e):
                        if e.value:
                            app.storage.user["tenant_id"] = str(e.value)
                            ui.notify(f"Переключено на: {options.get(str(e.value), e.value)}")
                            # Force page reload with JavaScript for more reliable refresh
                            ui.run_javascript('setTimeout(() => location.reload(), 500)')

                    ui.select(
                        options=options,
                        value=current_tenant,
                        label="🏢 Салон",
                        on_change=on_tenant_change
                    ).classes("w-48 mr-4").props("dense outlined bg-color=white options-dense behavior=menu")
                
            except Exception as e:
                print(f"Error loading tenants: {e}")
                import traceback
                traceback.print_exc()
                ui.label("Error loading tenants").classes("text-red text-caption")
        
        # User info
        user_email = app.storage.user.get("email", "")
        user_role = app.storage.user.get("role", "")
        
        with ui.row().classes("items-center gap-2"):
            ui.label(user_email).classes("text-white text-caption")
            ui.chip(
                user_role.replace("_", " ").title(), 
                color="white"
            ).props("outline")
            
            ui.button(
                icon="logout", 
                on_click=logout
            ).props("flat color=white round").tooltip("Выйти")
    
    # Sidebar
    sidebar = create_sidebar()
    
    # Main content area
    with ui.column().classes("w-full p-6 gap-4"):
        yield
