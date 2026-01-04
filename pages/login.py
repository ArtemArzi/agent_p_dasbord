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
    
    # Add fonts and styles
    ui.add_head_html("""
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <style>
        body { margin: 0; padding: 0; font-family: 'Outfit', sans-serif !important; overflow: hidden; }
        .nicegui-content { padding: 0; margin: 0; }
    </style>
    """)
    
    # Main Container (Centered Glass Design)
    with ui.element("div").classes("w-full h-screen flex items-center justify-center bg-gradient-to-br from-indigo-900 via-purple-900 to-slate-900 relative overflow-hidden"):
        
        # Animated Background Elements
        ui.element("div").classes("absolute top-0 left-0 w-full h-full opacity-20 z-0").style("background-image: url('data:image/svg+xml,%3Csvg viewBox=\"0 0 200 200\" xmlns=\"http://www.w3.org/2000/svg\"%3E%3Cfilter id=\"noiseFilter\"%3E%3CfeTurbulence type=\"fractalNoise\" baseFrequency=\"0.65\" numOctaves=\"3\" stitchTiles=\"stitch\"/%3E%3C/filter%3E%3Crect width=\"100%25\" height=\"100%25\" filter=\"url(%23noiseFilter)\" opacity=\"0.1\"/%3E%3C/svg%3E');")
        ui.element("div").classes("absolute top-[-10%] left-[-10%] w-[50%] h-[50%] rounded-full bg-purple-600 blur-[120px] opacity-30 animate-pulse")
        ui.element("div").classes("absolute bottom-[-10%] right-[-10%] w-[50%] h-[50%] rounded-full bg-blue-600 blur-[120px] opacity-30 animate-pulse delay-1000")
        
        # Glass Card
        with ui.card().classes("w-full max-w-md p-8 rounded-2xl bg-white/10 backdrop-blur-xl border border-white/20 shadow-2xl z-10 mx-4"):
            
            # Header
            with ui.column().classes("w-full items-center gap-2 mb-8"):
                ui.label("AMICA").style("font-family: 'Outfit', sans-serif; letter-spacing: 2px;").classes("text-4xl font-bold text-white")
                ui.label("Intelligent Salon Management").classes("text-sm text-purple-200 font-light tracking-widest uppercase text-center")
            
            # Form
            with ui.column().classes("w-full gap-5"):
                email = ui.input(
                    "Email", 
                    placeholder="name@example.com"
                ).classes("w-full").props("outlined dark dense color=white bg-color=transparent input-class=text-white label-color=purple-200").style("font-size: 16px")
                
                context = {
                    "password_visible": False
                }
                
                password = ui.input(
                    "Пароль", 
                    password=True,
                    value=""
                ).classes("w-full").props("outlined dark dense color=white bg-color=transparent input-class=text-white label-color=purple-200")
                
                # Custom password toggle
                with password.add_slot("append"):
                    def toggle_pass():
                        context["password_visible"] = not context["password_visible"]
                        password.props(f"type={'text' if context['password_visible'] else 'password'}")
                        icon.props(f"name={'visibility' if context['password_visible'] else 'visibility_off'}")
                    
                    icon = ui.icon("visibility_off").classes("cursor-pointer text-purple-200 hover:text-white").on("click", toggle_pass)
                
                # Error label
                error_label = ui.label().classes("text-red-400 text-sm text-center w-full hidden")
                
                async def try_login():
                    if not email.value or not password.value:
                        error_label.text = "Введите email и пароль"
                        error_label.classes(remove="hidden")
                        return
                    
                    user = await authenticate(email.value, password.value)
                    
                    if user:
                        # Clear specific overrides to let global theme take over (NiceGUI handles this usually on navigate)
                        app.storage.user.update({
                            "authenticated": True,
                            "user_id": user.id,
                            "email": user.email,
                            "role": user.role,
                            "tenant_id": str(user.tenant_id) if user.tenant_id else None,
                            "first_name": user.first_name,
                            "last_name": user.last_name,
                        })
                        ui.notify(f"Добро пожаловать, {user.first_name}!", type="positive")
                        ui.navigate.to("/overview")
                    else:
                        error_label.text = "Неверный логин или пароль"
                        error_label.classes(remove="hidden")
                        password.set_value("")
                
                # Submit on Enter
                password.on("keydown.enter", try_login)
                email.on("keydown.enter", try_login)
                
                # Login Button
                ui.button(
                    "Войти в систему", 
                    on_click=try_login
                ).classes("w-full h-12 text-md font-semibold shadow-lg hover:shadow-purple-500/50 transition-all bg-gradient-to-r from-purple-500 to-indigo-500 hover:scale-[1.02] border-none").props("rounded unelevated")
            
            # Footer
            with ui.row().classes("w-full justify-center mt-6"):
               ui.label("© 2026 AMICA Dashboard").classes("text-xs text-purple-300/50")
