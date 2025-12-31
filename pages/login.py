"""Login page."""

from nicegui import ui, app
from auth import authenticate


@ui.page("/login")
async def login_page():
    """Login page for dashboard authentication."""
    
    # Already authenticated → redirect to overview
    if app.storage.user.get("authenticated"):
        ui.navigate.to("/overview")
        return
    
    # Dark theme
    ui.dark_mode().enable()
    
    # Custom styles
    ui.add_head_html("""
    <style>
        .login-card {
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            border: 1px solid #2d3748;
        }
    </style>
    """)
    
    # Center card
    with ui.card().classes("absolute-center w-96 login-card"):
        # Logo / Title
        with ui.column().classes("w-full items-center mb-4"):
            ui.icon("smart_toy", size="64px").classes("text-primary")
            ui.label("Agent P Dashboard").classes("text-h5 text-center w-full")
            ui.label("Вход в систему").classes("text-subtitle2 text-grey")
        
        ui.separator()
        
        # Form fields
        email = ui.input(
            "Email",
            placeholder="admin@example.com"
        ).classes("w-full").props("outlined")
        
        password = ui.input(
            "Пароль", 
            password=True,
            password_toggle_button=True
        ).classes("w-full").props("outlined")
        
        # Error message (hidden by default)
        error_label = ui.label().classes("text-negative text-center w-full hidden")
        
        async def try_login():
            """Attempt to authenticate user."""
            # Validate inputs
            if not email.value or not password.value:
                error_label.text = "Заполните все поля"
                error_label.classes(remove="hidden")
                return
            
            # Authenticate
            user = await authenticate(email.value, password.value)
            
            if user:
                # Success: store session and redirect
                app.storage.user.update({
                    "authenticated": True,
                    "user_id": user.id,
                    "email": user.email,
                    "role": user.role,
                    "tenant_id": str(user.tenant_id) if user.tenant_id else None,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                })
                ui.notify("Добро пожаловать!", type="positive")
                ui.navigate.to("/overview")
            else:
                # Failed: show error
                error_label.text = "Неверный email или пароль"
                error_label.classes(remove="hidden")
                password.set_value("")
        
        # Submit on Enter key
        password.on("keydown.enter", try_login)
        
        # Login button
        ui.button(
            "Войти", 
            on_click=try_login
        ).classes("w-full mt-4").props("color=primary unelevated")
        
        # Footer
        ui.label("© 2025 Agent P").classes("text-caption text-grey text-center w-full mt-4")
