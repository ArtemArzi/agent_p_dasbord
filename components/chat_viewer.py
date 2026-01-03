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
    
    # Add CSS for chat bubbles that works in both light and dark mode
    ui.add_head_html('''
        <style>
            .chat-bubble-user {
                background: linear-gradient(135deg, #8B5CF6 0%, #7C3AED 100%);
                color: white !important;
                border-radius: 18px 18px 4px 18px;
            }
            .chat-bubble-assistant {
                background: #f3f4f6;
                color: #1f2937 !important;
                border-radius: 18px 18px 18px 4px;
                border: 1px solid #e5e7eb;
            }
            body.body--dark .chat-bubble-assistant {
                background: #374151 !important;
                color: #f9fafb !important;
                border-color: #4b5563 !important;
            }
            .chat-bubble-user *, .chat-bubble-assistant * {
                color: inherit !important;
            }
            .chat-time-user { color: rgba(255,255,255,0.7) !important; }
            .chat-time-assistant { color: #9ca3af !important; }
            body.body--dark .chat-time-assistant { color: #9ca3af !important; }
            .chat-messages-area {
                background: #f9fafb;
            }
            body.body--dark .chat-messages-area {
                background: #111827 !important;
            }
        </style>
    ''')
    
    with ui.dialog() as dialog, ui.card().classes("w-[480px] max-h-[85vh] p-0 rounded-2xl overflow-hidden"):
        # Header - Telegram style
        with ui.row().classes("w-full items-center justify-between lavender-header p-4"):
            with ui.row().classes("items-center gap-3"):
                ui.avatar("person", size="md").classes("bg-white text-purple-600 font-bold shadow-sm")
                with ui.column().classes("gap-0"):
                    ui.label(client_name).classes("text-gray-800 font-bold text-base")
                    ui.label(f"{len(history)} сообщений").classes("text-gray-600 text-xs")
            ui.button(icon="close", on_click=dialog.close).props("flat round dense color=grey")
        
        if not history:
            with ui.column().classes("items-center justify-center py-16 w-full chat-messages-area"):
                ui.icon("chat_bubble_outline").classes("text-6xl text-gray-300 mb-4")
                ui.label("История сообщений не найдена").classes("text-gray-400 font-medium")
        else:
            # Messages area
            with ui.scroll_area().classes("h-[400px] w-full p-4 chat-messages-area"):
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
                        bubble_class = "chat-bubble-user" if is_user else "chat-bubble-assistant"
                        with ui.card().classes(f"max-w-[85%] p-3 {bubble_class}").style("box-shadow: 0 2px 4px rgba(0,0,0,0.1)"):
                            with ui.column().classes("gap-1"):
                                # Avatar and message
                                with ui.row().classes("gap-2 items-start"):
                                    if not is_user:
                                        ui.icon("smart_toy").classes("text-lg text-purple-500")
                                    ui.label(msg.get("message", "")).style("word-break: break-word")
                                
                                # Time stamp
                                if time_str:
                                    time_class = "chat-time-user" if is_user else "chat-time-assistant"
                                    ui.label(time_str).classes(f"text-xs {time_class}")
        
        # Footer
        with ui.row().classes("w-full justify-end p-3 border-t").style("background: var(--card-bg); border-color: var(--card-border)"):
            ui.button("Закрыть", on_click=dialog.close).props("unelevated rounded color=purple")
    
    dialog.open()

