"""Settings page with tenant metadata editing."""

from nicegui import ui, app
from auth import require_auth
from components.layout import page_layout
from data import get_tenant_settings, update_tenant_metadata


@ui.page("/settings")
@require_auth()
async def settings_page():
    """Settings page for editing tenant metadata."""
    
    user_role = app.storage.user.get("role", "")
    tenant_id = app.storage.user.get("tenant_id")
    
    # Access control
    if user_role not in ("super_admin", "admin"):
        ui.label("Доступ запрещен").classes("text-h4 text-red")
        return
    
    if not tenant_id:
        ui.label("Выберите салон в меню").classes("text-h5 text-warning")
        return
    
    # Load tenant data
    tenant = get_tenant_settings(tenant_id)
    if not tenant:
        ui.label("Салон не найден").classes("text-h5 text-red")
        return
    
    metadata = tenant.get("metadata") or {}
    current_branch = metadata.get("current_branch") or {}
    
    # Form state - store current values
    form_state = {
        "salon_name": metadata.get("salon_name", ""),
        "welcome_message": metadata.get("welcome_message", ""),
        "closing_time": metadata.get("closing_time", "21:00"),
        "admin_chat_id": str(metadata.get("admin_chat_id", "")),
        "yclients_salon_id": metadata.get("yclients_salon_id", ""),
        "telegram_bot_enabled": metadata.get("telegram_bot_enabled", True),
        "enable_gap_filtering": metadata.get("enable_gap_filtering", False),
        "branch_name": current_branch.get("name", ""),
        "branch_phone": current_branch.get("phone", ""),
        "branch_address": current_branch.get("address", ""),
    }
    
    async def save_settings():
        """Save updated settings to database."""
        # Validate admin_chat_id is numeric
        if form_state["admin_chat_id"]:
            try:
                admin_chat_id = int(form_state["admin_chat_id"])
            except ValueError:
                ui.notify("Admin Chat ID должен быть числом", type="negative")
                return
        else:
            admin_chat_id = None
        
        # Validate closing_time format (HH:MM)
        closing_time = form_state["closing_time"]
        if closing_time:
            import re
            if not re.match(r'^([01]?\d|2[0-3]):[0-5]\d$', closing_time):
                ui.notify("Время закрытия должно быть в формате HH:MM", type="negative")
                return
        
        try:
            # Build updated metadata
            updated_metadata = {
                **metadata,
                "salon_name": form_state["salon_name"],
                "welcome_message": form_state["welcome_message"],
                "closing_time": closing_time,
                "admin_chat_id": admin_chat_id,
                "yclients_salon_id": form_state["yclients_salon_id"],
                "telegram_bot_enabled": form_state["telegram_bot_enabled"],
                "enable_gap_filtering": form_state["enable_gap_filtering"],
                "current_branch": {
                    **current_branch,
                    "name": form_state["branch_name"],
                    "phone": form_state["branch_phone"],
                    "address": form_state["branch_address"],
                }
            }
            
            # Pass authorization parameters
            if update_tenant_metadata(
                tenant_id, 
                updated_metadata,
                user_role=user_role,
                user_tenant_id=tenant_id  # Current tenant being edited
            ):
                ui.notify("Настройки сохранены!", type="positive")
            else:
                ui.notify("Ошибка при сохранении (проверьте права доступа)", type="negative")
        except Exception as e:
            ui.notify(f"Ошибка: {e}", type="negative")

    
    with page_layout("⚙️ Настройки"):
        
        ui.label(f"Настройки салона: {tenant.get('name', 'Unnamed')}").classes("text-h5 mb-4")
        
        # Basic Info Section
        with ui.card().classes("w-full mb-4"):
            ui.label("📍 Основная информация").classes("text-h6 mb-2")
            
            with ui.row().classes("w-full gap-4"):
                ui.input(
                    "Название салона",
                    value=form_state["salon_name"],
                    on_change=lambda e: form_state.update({"salon_name": e.value})
                ).classes("w-64").props("outlined")
                
                ui.input(
                    "Время закрытия",
                    value=form_state["closing_time"],
                    on_change=lambda e: form_state.update({"closing_time": e.value})
                ).classes("w-32").props("outlined")
            
            ui.textarea(
                "Приветственное сообщение",
                value=form_state["welcome_message"],
                on_change=lambda e: form_state.update({"welcome_message": e.value})
            ).classes("w-full").props("outlined rows=2")
        
        # Contact Info Section
        with ui.card().classes("w-full mb-4"):
            ui.label("📞 Контактная информация").classes("text-h6 mb-2")
            
            with ui.row().classes("w-full gap-4"):
                ui.input(
                    "Название филиала",
                    value=form_state["branch_name"],
                    on_change=lambda e: form_state.update({"branch_name": e.value})
                ).classes("flex-1").props("outlined")
                
                ui.input(
                    "Телефон",
                    value=form_state["branch_phone"],
                    on_change=lambda e: form_state.update({"branch_phone": e.value})
                ).classes("w-48").props("outlined")
            
            ui.input(
                "Адрес",
                value=form_state["branch_address"],
                on_change=lambda e: form_state.update({"branch_address": e.value})
            ).classes("w-full").props("outlined")
        
        # Integration Section
        with ui.card().classes("w-full mb-4"):
            ui.label("🔗 Интеграции").classes("text-h6 mb-2")
            
            with ui.row().classes("w-full gap-4 items-center"):
                ui.input(
                    "YClients Salon ID",
                    value=form_state["yclients_salon_id"],
                    on_change=lambda e: form_state.update({"yclients_salon_id": e.value})
                ).classes("w-48").props("outlined")
                
                ui.input(
                    "Admin Chat ID (Telegram)",
                    value=form_state["admin_chat_id"],
                    on_change=lambda e: form_state.update({"admin_chat_id": e.value})
                ).classes("w-48").props("outlined")
            
            with ui.row().classes("w-full gap-8 mt-4"):
                ui.switch(
                    "Telegram Bot включен",
                    value=form_state["telegram_bot_enabled"],
                    on_change=lambda e: form_state.update({"telegram_bot_enabled": e.value})
                )
                
                ui.switch(
                    "Фильтрация окон",
                    value=form_state["enable_gap_filtering"],
                    on_change=lambda e: form_state.update({"enable_gap_filtering": e.value})
                ).tooltip("enable_gap_filtering - фильтрация слотов по длительности")
        
        # Save Button
        ui.button(
            "💾 Сохранить настройки",
            on_click=save_settings
        ).classes("w-full mt-4").props("color=primary size=lg")
        
        # Debug info for super_admin (hide sensitive tokens)
        if user_role == "super_admin":
            with ui.expansion("🔧 Debug Info", icon="bug_report").classes("mt-4"):
                ui.label(f"Tenant ID: {tenant_id}").classes("font-mono text-grey")
                # Filter out sensitive fields containing 'token'
                safe_metadata = {
                    k: v for k, v in metadata.items() 
                    if "token" not in k.lower() and "password" not in k.lower()
                }
                import json
                ui.code(json.dumps(safe_metadata, indent=2, ensure_ascii=False), language="json")
