"""Sessions page with filterable table and chat viewer."""

from nicegui import ui, app
from datetime import datetime
from auth import require_auth
from components.layout import page_layout
from components.chat_viewer import show_chat_dialog
from data import get_sessions


@ui.page("/sessions")
@require_auth()
async def sessions_page():
    """Sessions page with table, filters, and chat history viewer."""

    tenant_id = app.storage.user.get("tenant_id")

    # Pagination state
    page_state = {"current": 0, "limit": 20, "total": 0}

    # UI element references (will be assigned later)
    status_select = None
    date_from = None
    date_to = None
    stats_label = None
    table_container = None
    page_label = None
    prev_btn = None
    next_btn = None

    def format_datetime(dt_str: str) -> str:
        """Format datetime string for display."""
        if not dt_str:
            return "—"
        try:
            dt = datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
            return dt.strftime("%d.%m.%Y %H:%M")
        except Exception:
            return dt_str[:16]

    def get_status_badge(status: str) -> tuple[str, str]:
        """Get status display text and color."""
        mapping = {
            "done": (
                "Завершён",
                "bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400",
            ),
            "completed": (
                "Завершён",
                "bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400",
            ),
            "booked": (
                "Записан",
                "bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400",
            ),
            "abandoned": (
                "Ушёл",
                "bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400",
            ),
            "auto_closed": (
                "Таймаут",
                "bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-400",
            ),
            "transferred": (
                "Оператору",
                "bg-purple-100 text-purple-800 dark:bg-purple-900/30 dark:text-purple-400",
            ),
            "ghost": (
                "Без ответа",
                "bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-400",
            ),
            "no_slots": (
                "Нет слотов",
                "bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400",
            ),
            "price_too_high": (
                "Дорого",
                "bg-orange-100 text-orange-800 dark:bg-orange-900/30 dark:text-orange-400",
            ),
        }
        return mapping.get(
            status,
            (status, "bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-400"),
        )

    def get_intent_label(intent: str | None) -> str:
        if not intent:
            return "—"
        mapping = {
            "info": "Консультация",
            "unknown": "Не определён",
            "booking_refinement": "Уточнение",
            "finalize_booking": "Запись",
            "cancel_booking": "Отмена",
            "add_service": "Доп. услуга",
            "join_wishlist": "Лист ожидания",
            "greeting": "Приветствие",
            "complaint": "Жалоба",
            "reschedule": "Перенос",
        }
        return mapping.get(intent, intent)

    async def refresh_table():
        """Refresh sessions table."""
        nonlocal \
            status_select, \
            date_from, \
            date_to, \
            stats_label, \
            table_container, \
            page_label, \
            prev_btn, \
            next_btn

        if not tenant_id:
            return

        # Get data
        data, total = get_sessions(
            tenant_id=tenant_id,
            limit=page_state["limit"],
            offset=page_state["current"] * page_state["limit"],
            status_filter=status_select.value
            if status_select and status_select.value != "all"
            else None,
            date_from=date_from.value if date_from and date_from.value else None,
            date_to=date_to.value if date_to and date_to.value else None,
        )

        page_state["total"] = total
        total_pages = max(1, (total + page_state["limit"] - 1) // page_state["limit"])

        # Update stats
        if stats_label:
            stats_label.text = f"Найдено: {total} сессий"
        if page_label:
            # Simple "1 / 5" style
            page_label.text = f"{page_state['current'] + 1} / {total_pages}"

        # Update pagination buttons
        if prev_btn:
            prev_btn.set_enabled(page_state["current"] > 0)
        if next_btn:
            next_btn.set_enabled(page_state["current"] < total_pages - 1)

        # Rebuild table
        if table_container:
            table_container.clear()
            with table_container:
                if not data:
                    ui.label("Нет данных").classes("text-grey text-center py-8")
                    return

                # Table header
                with ui.row().classes(
                    "w-full bg-gray-100 dark:bg-gray-800 py-3 px-4 rounded-t-lg gap-4"
                ):
                    ui.label("ID").classes(
                        "w-16 font-semibold text-gray-600 dark:text-gray-300 text-sm"
                    )
                    ui.label("Дата").classes(
                        "w-36 font-semibold text-gray-600 dark:text-gray-300 text-sm"
                    )
                    ui.label("Клиент").classes(
                        "w-40 font-semibold text-gray-600 dark:text-gray-300 text-sm"
                    )
                    ui.label("Статус").classes(
                        "w-32 font-semibold text-gray-600 dark:text-gray-300 text-sm"
                    )
                    ui.label("Цель").classes(
                        "w-40 font-semibold text-gray-600 dark:text-gray-300 text-sm"
                    )
                    ui.label("").classes("w-20")

                # Table rows
                for row in data:
                    session_id = row.get("session_id")
                    client_info = row.get("clients_v2") or {}
                    client_name = client_info.get("full_name") or "—"
                    summary = row.get("summary") or ""

                    with ui.row().classes(
                        "w-full py-3 px-4 border-b border-gray-200 dark:border-gray-700 gap-4 hover:bg-gray-50 dark:hover:bg-gray-800/50 items-center transition-colors"
                    ) as row_el:
                        if summary:
                            row_el.tooltip(summary)
                        ui.label(str(row.get("id", "—"))).classes(
                            "w-16 text-gray-500 dark:text-gray-400 text-sm"
                        )
                        ui.label(format_datetime(row.get("started_at"))).classes(
                            "w-36 text-gray-800 dark:text-gray-200 text-sm"
                        )
                        ui.label(client_name).classes(
                            "w-40 text-gray-800 dark:text-gray-200 font-medium text-sm"
                        )

                        # Status badge
                        status_text, status_class = get_status_badge(
                            row.get("final_status", "")
                        )
                        ui.label(status_text).classes(
                            f"w-32 px-2 py-1 rounded-full text-xs font-medium text-center {status_class}"
                        )

                        intent_raw = row.get("final_intent")
                        intent_label = get_intent_label(intent_raw)
                        ui.label(intent_label).classes(
                            "w-40 text-gray-500 dark:text-gray-400 text-sm truncate"
                        ).tooltip(intent_raw or "—")

                        ui.button(
                            icon="visibility",
                            on_click=lambda sid=session_id,
                            name=client_name,
                            tid=tenant_id,
                            s=summary: show_chat_dialog(sid, name, tid, s),
                        ).props("flat round dense").tooltip("Просмотреть диалог")

    async def go_page(delta: int):
        """Navigate to next/prev page."""
        page_state["current"] = max(0, page_state["current"] + delta)
        await refresh_table()

    async def reset_filters():
        """Reset all filters."""
        nonlocal status_select, date_from, date_to
        if status_select:
            status_select.value = "all"
        if date_from:
            date_from.value = ""
        if date_to:
            date_to.value = ""
        page_state["current"] = 0
        await refresh_table()

    # Inject locale
    import json
    from components.common import RU_LOCALE

    ui.add_body_html(
        f"<script> const ru_locale = {json.dumps(RU_LOCALE, ensure_ascii=False)}; </script>"
    )

    # Build UI
    with page_layout("Диалоги"):
        # Filters row
        with ui.row().classes(
            "w-full items-center gap-4 mb-6 p-4 rounded-xl shadow-sm theme-card"
        ):
            ui.icon("filter_list").classes("text-gray-500 dark:text-gray-400")
            status_select = (
                ui.select(
                    {
                        "all": "Все статусы",
                        "done": "Завершён",
                        "booked": "Записан",
                        "abandoned": "Ушёл",
                        "auto_closed": "Таймаут",
                        "transferred": "Оператору",
                        "ghost": "Без ответа",
                    },
                    value="all",
                    label="Статус",
                )
                .classes("w-40")
                .props("outlined dense color=purple options-dense")
            )

            ui.separator().props("vertical").classes("mx-2 hidden sm:block h-8")

            with (
                ui.input("С даты")
                .classes("w-36")
                .props("outlined dense color=purple") as date_from
            ):
                with ui.menu().props("no-parent-event") as menu_from:
                    ui.date().bind_value(date_from).props(
                        "minimal color=purple :locale='ru_locale'"
                    ).on("input", menu_from.close).classes("w-64")
                with date_from.add_slot("append"):
                    ui.icon("edit_calendar").on("click", menu_from.open).classes(
                        "cursor-pointer text-gray-500 hover:text-purple-600 transition-colors"
                    )

            ui.label("-").classes("text-gray-400")

            with (
                ui.input("По дату")
                .classes("w-36")
                .props("outlined dense color=purple") as date_to
            ):
                with ui.menu().props("no-parent-event") as menu_to:
                    ui.date().bind_value(date_to).props(
                        "minimal color=purple :locale='ru_locale'"
                    ).on("input", menu_to.close).classes("w-64")
                with date_to.add_slot("append"):
                    ui.icon("edit_calendar").on("click", menu_to.open).classes(
                        "cursor-pointer text-gray-500 hover:text-purple-600 transition-colors"
                    )

            ui.space()

            ui.button(icon="search", on_click=refresh_table).props(
                "flat round color=purple"
            ).tooltip("Найти")
            ui.button(icon="restart_alt", on_click=reset_filters).props(
                "flat round color=grey"
            ).tooltip("Сбросить")

        # Stats row
        stats_label = ui.label().classes("text-grey mb-2")

        # Table container
        table_container = ui.column().classes("w-full")

        # Pagination
        with ui.row().classes("w-full justify-center items-center gap-4 mt-6"):
            prev_btn = (
                ui.button(icon="chevron_left", on_click=lambda: go_page(-1))
                .props("round flat color=grey-7")
                .classes("dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-700")
            )
            page_label = ui.label().classes(
                "text-sm font-semibold text-gray-700 dark:text-gray-300 min-w-[3rem] text-center"
            )
            next_btn = (
                ui.button(icon="chevron_right", on_click=lambda: go_page(1))
                .props("round flat color=grey-7")
                .classes("dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-700")
            )

        # Initial load
        await refresh_table()
