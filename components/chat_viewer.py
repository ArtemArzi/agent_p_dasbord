"""Chat Viewer Dialog component - Telegram style."""

from nicegui import ui
from data import get_session_history


def show_chat_dialog(session_id: str, client_name: str = "Клиент", tenant_id: str | None = None) -> None:
    """
    Show Telegram-style chat history dialog for a session.
    
    Args:
        session_id: UUID of the session
        client_name: Name to display in header
        tenant_id: Tenant ID for security validation
    """
    if not tenant_id:
        ui.notify("Ошибка: tenant_id не указан", type="negative")
        return
    
    history = get_session_history(session_id, tenant_id)
    
    with ui.dialog() as dialog, ui.card().classes("w-[450px] max-h-[85vh] p-0"):
        # Header - Telegram style
        with ui.row().classes("w-full items-center justify-between bg-primary p-3"):
            with ui.row().classes("items-center gap-3"):
                ui.avatar("👤", size="md").classes("bg-blue-600")
                with ui.column().classes("gap-0"):
                    ui.label(client_name).classes("text-white font-medium")
                    ui.label(f"{len(history)} сообщений").classes("text-white/70 text-xs")
            ui.button(icon="close", on_click=dialog.close).props("flat round dense color=white")
        
        if not history:
            with ui.column().classes("items-center justify-center py-16"):
                ui.icon("chat_bubble_outline").classes("text-6xl text-grey")
                ui.label("История сообщений не найдена").classes("text-grey")
        else:
            # Messages area - Telegram style
            with ui.scroll_area().classes("h-[400px] w-full bg-gray-900 p-4") as scroll:
                for msg in history:
                    is_user = msg.get("role") == "user"
                    time_str = ""
                    if msg.get("created_at"):
                        try:
                            from datetime import datetime
                            dt = datetime.fromisoformat(msg["created_at"].replace("Z", "+00:00"))
                            time_str = dt.strftime("%H:%M")
                        except:
                            pass
                    
                    # Message bubble
                    with ui.row().classes(f"w-full {'justify-end' if is_user else 'justify-start'} mb-3"):
                        with ui.card().classes(
                            f"max-w-[85%] p-3 {'bg-blue-600 rounded-l-2xl rounded-tr-2xl rounded-br-sm' if is_user else 'bg-gray-700 rounded-r-2xl rounded-tl-2xl rounded-bl-sm'}"
                        ).style("box-shadow: none"):
                            with ui.column().classes("gap-1"):
                                # Avatar and message
                                with ui.row().classes("gap-2 items-start"):
                                    if not is_user:
                                        ui.label("🤖").classes("text-lg")
                                    ui.label(msg.get("message", "")).classes(
                                        f"text-white {'text-right' if is_user else 'text-left'}"
                                    ).style("word-break: break-word")
                                    if is_user:
                                        ui.label("👤").classes("text-lg")
                                
                                # Time stamp
                                if time_str:
                                    ui.label(time_str).classes(
                                        f"text-xs text-white/50 {'text-right' if is_user else 'text-left'}"
                                    )
        
        # Footer
        with ui.row().classes("w-full justify-end p-3 bg-gray-800"):
            ui.button("Закрыть", on_click=dialog.close).props("flat color=grey")
    
    dialog.open()
