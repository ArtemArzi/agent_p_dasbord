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
    # Global CSS and Fonts (added to each page that uses this layout)
    # Tailwind Dark Mode Sync (Using common utility)
    # Styles and fonts
    ui.add_head_html('''
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&display=swap');
            
            body {
                font-family: 'Outfit', sans-serif;
                background-color: #f8fafc; /* gray-50 */
                color: #1e293b; /* gray-800 */
            }
            /* AMICA Premium Tech Color Palette */
            :root {
                --amica-base: #E6E0F8;      /* Digital Lavender */
                --amica-action: #312E81;    /* Deep Indigo */
                --amica-accent: #6D28D9;    /* Royal Purple */
                --amica-luxury: #F5E6D3;    /* Champagne */
                --amica-sand: #D4C4AA;      /* Warm Sand */
            }
            
            /* THEME VARIABLES */
            body {
                --card-bg: #ffffff;
                --card-text: #1f2937;
                --card-border: #e5e7eb;
                --header-text: var(--amica-action);
            }
            body.body--dark {
                --card-bg: #1e293b;
                --card-text: #f1f5f9;
                --card-border: #334155;
                --header-text: #ffffff;
                background-color: #0f172a !important;
            }
            
            /* Utils */
            .theme-card {
                background-color: var(--card-bg) !important;
                color: var(--card-text) !important;
                border: 1px solid var(--card-border) !important;
            }
            .header-text {
                color: var(--header-text) !important;
            }
            
            .lavender-header {
                background: linear-gradient(135deg, var(--amica-base) 0%, #C4B5FD 50%, #A78BFA 100%);
            }
            body.body--dark .lavender-header {
                background: linear-gradient(135deg, var(--amica-action) 0%, #4C1D95 100%);
            }
            
            /* Tenant selector dark mode fix */
            .tenant-selector .q-field__control {
                background: transparent !important;
            }
            body.body--dark .tenant-selector .q-field__native,
            body.body--dark .tenant-selector .q-field__label {
                color: #ffffff !important;
            }
            body.body--dark .tenant-selector .q-field__control::before {
                border-color: rgba(255,255,255,0.5) !important;
            }
            .glass-card {
                background: rgba(255, 255, 255, 0.9);
                backdrop-filter: blur(10px);
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 16px;
                box-shadow: 0 10px 30px rgba(0, 0, 0, 0.05);
                transition: transform 0.2s ease;
            }
            .body--dark .glass-card {
                background: rgba(30, 30, 30, 0.8);
                border: 1px solid rgba(255, 255, 255, 0.05);
            }
            .glass-card:hover { transform: translateY(-2px); }
        </style>
    ''')
    
    # Header
    with ui.header(elevated=False).classes("lavender-header h-16 px-6 shadow-sm flex items-center justify-between z-20 transition-all"):
        
        # Toggle drawer button
        with ui.row().classes("items-center gap-3"):
            ui.button(icon="menu", on_click=lambda: sidebar.toggle()).props("flat round dense").classes("header-text")
            ui.label(title).style(
                "font-family: 'Outfit', sans-serif; font-weight: 500; letter-spacing: 1px;"
            ).classes("text-xl header-text")
        
        # Right Side: Theme Toggle & Info
        with ui.row().classes("items-center gap-6"): # Increased gap
            
            # Theme Toggle (Persistent & Robust)
            from components.common import setup_dark_mode
            dark = setup_dark_mode()
            
            ui.button(
                icon="dark_mode", 
                on_click=lambda: dark.toggle()
            ).bind_visibility_from(dark, 'value', value=False).props("flat round dense").tooltip("Тёмная тема").classes("header-text")
            
            ui.button(
                icon="light_mode", 
                on_click=lambda: dark.toggle()
            ).bind_visibility_from(dark, 'value', value=True).props("flat round dense").tooltip("Светлая тема").classes("header-text")
            
            # Super Admin Tenant Selector
            user_role = app.storage.user.get("role", "")
            
            if user_role == "super_admin":
                from data import get_tenants  # Lazy import
                
                try:
                    tenants = get_tenants()
                    options = {str(t["id"]): t.get("name") or "Unnamed Salon" for t in tenants}
                    current_tenant = app.storage.user.get("tenant_id")
                    
                    # Ensure current_tenant is string for select matching
                    if current_tenant:
                        current_tenant = str(current_tenant)
                    
                    # Validate that current_tenant exists in available options
                    # If not (e.g., old session with deleted tenant), reset to first available
                    if current_tenant and current_tenant not in options:
                        print(f"WARNING: tenant_id {current_tenant} not in available tenants, resetting")
                        current_tenant = None
                    
                    if not current_tenant and options:
                        first_id = list(options.keys())[0]
                        app.storage.user["tenant_id"] = first_id
                        current_tenant = first_id
                    
                    def on_tenant_change(e):
                        if e.value:
                            app.storage.user["tenant_id"] = str(e.value)
                            ui.notify(f"Переключено на: {options.get(str(e.value), e.value)}")
                            # Increased delay to ensure storage is saved before reload
                            ui.run_javascript('setTimeout(() => location.reload(), 1000)')

                    # Tenant selector needs inline style because it's a Quasar component with internal input
                    ui.select(
                        options=options,
                        value=current_tenant,
                        label="Салон",
                        on_change=on_tenant_change
                    ).classes("w-48 tenant-selector").props("outlined dense rounded options-dense behavior=menu color=deep-purple")
                except Exception as e:
                    print(f"Error loading tenants: {e}")
                    ui.label("Error").classes("text-red text-caption")
            
            # User info
            with ui.row().classes("items-center gap-3 border-l border-purple-300 dark:border-gray-600 pl-6 h-8"):
                # Simplified User Display
                with ui.row().classes("items-center gap-2"):
                    ui.icon("account_circle").classes("text-2xl header-text")
                    ui.label(user_role.replace("_", " ").title()).classes("font-medium header-text hidden sm:block")
                
                ui.button(
                    icon="logout", 
                    on_click=logout
                ).props("flat round dense").classes("header-text hover:bg-purple-200 dark:hover:bg-purple-900").tooltip("Выйти")
    
    # Sidebar
    sidebar = create_sidebar()
    
    # Main content area
    with ui.column().classes("w-full p-6 gap-4"):
        yield
