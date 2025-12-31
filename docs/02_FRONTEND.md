# Frontend спецификация (NiceGUI)

## 1. Обзор

Frontend Dashboard построен на **NiceGUI** — Python-фреймворке для создания веб-интерфейсов. NiceGUI использует Quasar (Vue.js) компоненты под капотом, но весь код пишется на Python.

> [!NOTE]
> NiceGUI автоматически синхронизирует состояние между сервером и клиентом через WebSockets.

---

## 2. Структура страниц

```
pages/
├── login.py        # 🔐 Авторизация
├── overview.py     # 📈 Обзор (KPI, воронка)
├── sessions.py     # 💬 Диалоги
├── wishlist.py     # 📋 Лист ожидания
├── clients.py      # 👥 Клиенты
└── settings.py     # ⚙️ Настройки (super_admin)
```

---

## 3. Основной layout (`main.py`)

### 3.1 Точка входа

```python
from nicegui import app, ui
from config import settings

# Импорт страниц
from pages import login, overview, sessions, wishlist, clients, settings_page

# Настройка storage
app.storage.secret = settings.app_secret

def main():
    ui.run(
        host=settings.app_host,
        port=settings.app_port,
        title="Agent P Dashboard",
        favicon="static/favicon.ico",
        dark=True,  # Dark theme по умолчанию
        storage_secret=settings.app_secret,
    )

if __name__ == "__main__":
    main()
```

### 3.2 Shared Layout с Sidebar

```python
# components/layout.py
from nicegui import ui, app
from components.sidebar import create_sidebar

def page_layout(title: str):
    """Общий layout для всех страниц"""
    
    # Header
    with ui.header().classes("bg-primary"):
        ui.button(icon="menu", on_click=lambda: sidebar.toggle())
        ui.label(title).classes("text-h6")
        ui.space()
        ui.label(app.storage.user.get("email", ""))
        ui.button(icon="logout", on_click=logout)
    
    # Sidebar
    sidebar = create_sidebar()
    
    # Main content area
    with ui.column().classes("w-full p-4"):
        yield  # Content вставляется здесь

async def logout():
    app.storage.user.clear()
    ui.navigate.to("/login")
```

---

## 4. Страница Login (`pages/login.py`)

### 4.1 UI

```python
from nicegui import ui, app
from auth import authenticate

@ui.page("/login")
async def login_page():
    # Если уже авторизован — редирект
    if app.storage.user.get("authenticated"):
        ui.navigate.to("/overview")
        return
    
    with ui.card().classes("absolute-center w-96"):
        ui.label("Agent P Dashboard").classes("text-h4 text-center w-full")
        ui.separator()
        
        email = ui.input("Email").classes("w-full")
        password = ui.input("Пароль", password=True).classes("w-full")
        error_label = ui.label().classes("text-negative hidden")
        
        async def try_login():
            user = await authenticate(email.value, password.value)
            if user:
                app.storage.user.update({
                    "authenticated": True,
                    "user_id": user.id,
                    "email": user.email,
                    "role": user.role,
                    "tenant_id": str(user.tenant_id) if user.tenant_id else None,
                })
                ui.navigate.to("/overview")
            else:
                error_label.text = "Неверный email или пароль"
                error_label.classes(remove="hidden")
        
        ui.button("Войти", on_click=try_login).classes("w-full mt-4")
```

### 4.2 Поведение

| Состояние | Действие |
|-----------|----------|
| Успешный логин | Сохраняем user в `app.storage.user`, редирект на `/overview` |
| Неуспешный логин | Показываем ошибку |
| Уже авторизован | Редирект на `/overview` |

---

## 5. Страница Overview (`pages/overview.py`)

### 5.1 Структура

```
┌─────────────────────────────────────────────────────────────┐
│ [KPI Card]  [KPI Card]  [KPI Card]  [KPI Card]              │
│  Сессии      Записи      Конверсия   Доход                  │
├─────────────────────────────────────────────────────────────┤
│ [Date Picker: 7д / 30д / Custom]                            │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  [Funnel Chart]              [Revenue Chart]                │
│  Воронка конверсии           График выручки                 │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│ [Top Services Table]         [Top Staff Table]              │
│ Топ-5 услуг                  Топ-5 мастеров                 │
└─────────────────────────────────────────────────────────────┘
```

### 5.2 Компоненты

```python
from nicegui import ui
from components.layout import page_layout
from components.kpi_card import KPICard
from components.funnel_chart import FunnelChart
from data import get_kpi_summary, get_daily_metrics

@ui.page("/overview")
@require_auth()
async def overview_page():
    tenant_id = app.storage.user.get("tenant_id")
    
    with page_layout("📈 Обзор"):
        # KPI Cards Row
        with ui.row().classes("w-full gap-4"):
            kpi = await get_kpi_summary(tenant_id, days=7)
            
            KPICard("Сессии", kpi["sessions"], icon="chat")
            KPICard("Записи", kpi["bookings"], icon="event")
            KPICard("Конверсия", f"{kpi['conversion']}%", icon="trending_up")
            KPICard("Доход", f"{kpi.get('revenue', 0):,.0f} ₽", icon="payments")
        
        # Date Filter
        with ui.row().classes("w-full"):
            period = ui.toggle(["7д", "30д", "90д"], value="7д")
            period.on_value_change(lambda: refresh_data())
        
        # Charts Row
        with ui.row().classes("w-full gap-4"):
            with ui.card().classes("flex-1"):
                ui.label("Воронка конверсии").classes("text-h6")
                FunnelChart(tenant_id)
            
            with ui.card().classes("flex-1"):
                ui.label("Выручка по дням").classes("text-h6")
                # ECharts line chart
                ui.echart({...})
```

### 5.3 KPI Card Component

```python
# components/kpi_card.py
from nicegui import ui

class KPICard:
    def __init__(self, title: str, value: str | int, icon: str = "info"):
        with ui.card().classes("w-48"):
            with ui.row().classes("items-center gap-2"):
                ui.icon(icon).classes("text-2xl text-primary")
                ui.label(title).classes("text-subtitle1")
            ui.label(str(value)).classes("text-h4 font-bold")
```

---

## 6. Страница Sessions (`pages/sessions.py`)

### 6.1 Структура

```
┌─────────────────────────────────────────────────────────────┐
│ [Filters: Status ▼] [Date Range] [Search 🔍]                │
├─────────────────────────────────────────────────────────────┤
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ ID │ Дата │ Клиент │ Статус │ Intent │ Sentiment │ 👁️  │ │
│ ├────┼──────┼────────┼────────┼────────┼───────────┼─────┤ │
│ │ 42 │ 30.12│ Мария  │ ✅ done│ booking│ 😊 pos    │ [O] │ │
│ │ 41 │ 30.12│ Иван   │ ⚠️ drop│ info   │ 😐 neu    │ [O] │ │
│ │ ...│      │        │        │        │           │     │ │
│ └─────────────────────────────────────────────────────────┘ │
├─────────────────────────────────────────────────────────────┤
│ [Pagination: < 1 2 3 ... 10 >]                              │
└─────────────────────────────────────────────────────────────┘
```

### 6.2 Table Implementation

```python
from nicegui import ui
from data import get_sessions, get_session_history

@ui.page("/sessions")
@require_auth()
async def sessions_page():
    tenant_id = app.storage.user.get("tenant_id")
    
    with page_layout("💬 Диалоги"):
        # Filters
        with ui.row().classes("w-full gap-4 mb-4"):
            status_filter = ui.select(
                ["Все", "done", "dropped", "escalated"],
                value="Все",
                label="Статус"
            )
            date_from = ui.date(label="С даты")
            date_to = ui.date(label="По дату")
            ui.button("Применить", on_click=refresh_table)
        
        # Table
        columns = [
            {"name": "id", "label": "ID", "field": "id"},
            {"name": "started_at", "label": "Дата", "field": "started_at"},
            {"name": "client_name", "label": "Клиент", "field": "client_name"},
            {"name": "final_status", "label": "Статус", "field": "final_status"},
            {"name": "final_intent", "label": "Intent", "field": "final_intent"},
            {"name": "sentiment", "label": "Sentiment", "field": "sentiment"},
            {"name": "actions", "label": "", "field": "actions"},
        ]
        
        sessions = await get_sessions(tenant_id, limit=50)
        rows = [s.model_dump() for s in sessions]
        
        table = ui.table(
            columns=columns,
            rows=rows,
            row_key="id",
            pagination={"rowsPerPage": 20}
        ).classes("w-full")
        
        # Row click handler
        table.on("row-click", lambda e: show_session_dialog(e.args[1]["session_id"]))
```

### 6.3 Session Dialog (Chat Viewer)

```python
# components/chat_viewer.py
from nicegui import ui
from data import get_session_history

async def show_session_dialog(session_id: str):
    """Показать диалог с историей сообщений"""
    
    with ui.dialog() as dialog, ui.card().classes("w-96 max-h-[80vh]"):
        ui.label("История диалога").classes("text-h6")
        ui.separator()
        
        history = await get_session_history(session_id)
        
        with ui.scroll_area().classes("h-96"):
            for msg in history:
                role = msg["role"]
                text = msg["message"]
                time = msg["created_at"]
                
                # Стилизация по роли
                if role == "user":
                    with ui.row().classes("justify-end"):
                        ui.chat_message(text, sent=True)
                else:
                    with ui.row().classes("justify-start"):
                        ui.chat_message(text, sent=False, avatar="🤖")
        
        ui.button("Закрыть", on_click=dialog.close)
    
    dialog.open()
```

---

## 7. Страница Wishlist (`pages/wishlist.py`)

### 7.1 Структура с Realtime

```python
from nicegui import ui
from data import get_pending_wishlist, update_wishlist_status

@ui.page("/wishlist")
@require_auth()
async def wishlist_page():
    tenant_id = app.storage.user.get("tenant_id")
    
    with page_layout("📋 Лист ожидания"):
        # Stats
        with ui.row().classes("w-full gap-4 mb-4"):
            items = await get_pending_wishlist(tenant_id)
            ui.label(f"Ожидают: {len(items)}").classes("text-h6")
        
        # Table
        columns = [
            {"name": "created_at", "label": "Дата", "field": "created_at"},
            {"name": "client_name", "label": "Клиент", "field": "client_name"},
            {"name": "client_phone", "label": "Телефон", "field": "client_phone"},
            {"name": "item_type", "label": "Тип", "field": "item_type"},
            {"name": "comment", "label": "Комментарий", "field": "comment"},
            {"name": "actions", "label": "Действия", "field": "actions"},
        ]
        
        rows = [item.model_dump() for item in items]
        table = ui.table(columns=columns, rows=rows, row_key="id")
        
        # Action buttons в каждой строке
        table.add_slot("body-cell-actions", """
            <q-td :props="props">
                <q-btn flat icon="check" color="positive" @click="$parent.$emit('convert', props.row)" />
                <q-btn flat icon="close" color="negative" @click="$parent.$emit('cancel', props.row)" />
                <q-btn flat icon="phone" color="info" @click="$parent.$emit('contact', props.row)" />
            </q-td>
        """)
        
        # Event handlers
        table.on("convert", lambda e: handle_convert(e.args["id"]))
        table.on("cancel", lambda e: handle_cancel(e.args["id"]))
        table.on("contact", lambda e: handle_contact(e.args))

async def handle_convert(item_id: int):
    """Конвертировать в запись"""
    user_id = app.storage.user.get("user_id")
    await update_wishlist_status(item_id, "converted", processed_by=user_id)
    ui.notify("Запись создана", type="positive")
    # TODO: Trigger bot to create booking

async def handle_cancel(item_id: int):
    """Отменить заявку"""
    await update_wishlist_status(item_id, "cancelled")
    ui.notify("Заявка отменена", type="warning")
```

### 7.2 Realtime Updates

```python
# Supabase Realtime subscription
from supabase import create_client

async def setup_realtime(tenant_id: str, table: ui.table):
    """Подписка на изменения wishlist"""
    sb = get_supabase()
    
    def on_insert(payload):
        # Добавить новую строку в таблицу
        new_item = payload["new"]
        if new_item["tenant_id"] == tenant_id:
            table.add_rows([new_item])
            ui.notify("Новая заявка!", type="info")
    
    def on_update(payload):
        # Обновить строку или удалить если статус изменился
        updated = payload["new"]
        if updated["status"] != "pending":
            table.remove_rows([{"id": updated["id"]}])
    
    channel = sb.channel("wishlist-changes")
    channel.on_postgres_changes(
        event="INSERT",
        schema="public",
        table="wishlist_v2",
        callback=on_insert
    )
    channel.on_postgres_changes(
        event="UPDATE",
        schema="public",
        table="wishlist_v2",
        callback=on_update
    )
    channel.subscribe()
```

---

## 8. Страница Clients (`pages/clients.py`)

### 8.1 Структура

```python
@ui.page("/clients")
@require_auth()
async def clients_page():
    tenant_id = app.storage.user.get("tenant_id")
    
    with page_layout("👥 Клиенты"):
        # Search
        with ui.row().classes("w-full mb-4"):
            search = ui.input(placeholder="Поиск по имени или телефону...")
            search.on("keyup.enter", lambda: refresh_clients())
        
        # Clients Table
        clients = await get_clients(tenant_id)
        
        columns = [
            {"name": "full_name", "label": "Имя", "field": "full_name"},
            {"name": "phone", "label": "Телефон", "field": "phone"},
            {"name": "preferred_staff_id", "label": "Любимый мастер", "field": "preferred_staff_id"},
            {"name": "created_at", "label": "Дата регистрации", "field": "created_at"},
        ]
        
        rows = [c.model_dump() for c in clients]
        ui.table(columns=columns, rows=rows, row_key="id").classes("w-full")
```

---

## 9. Страница Settings (`pages/settings.py`)

> [!WARNING]
> Доступна только для `role = "super_admin"`

### 9.1 Tenant Selector (Super Admin)

```python
@ui.page("/settings")
@require_auth()
async def settings_page():
    user_role = app.storage.user.get("role")
    
    if user_role != "super_admin":
        ui.label("Доступ запрещён").classes("text-h4 text-negative")
        return
    
    with page_layout("⚙️ Настройки"):
        # Tenant List
        tenants = await get_all_tenants()
        
        with ui.list().classes("w-full"):
            for tenant in tenants:
                with ui.item(on_click=lambda t=tenant: edit_tenant(t)):
                    with ui.item_section():
                        ui.item_label(tenant["name"])
                        ui.item_label(f"ID: {tenant['id']}").props("caption")
                    with ui.item_section().props("side"):
                        status = "✅" if tenant["is_active"] else "❌"
                        ui.badge(status)
```

---

## 10. Компоненты (`components/`)

### 10.1 Sidebar

```python
# components/sidebar.py
from nicegui import ui, app

def create_sidebar():
    """Боковое меню навигации"""
    
    with ui.left_drawer().classes("bg-dark") as drawer:
        ui.label("Agent P").classes("text-h5 text-center py-4")
        ui.separator()
        
        menu_items = [
            ("/overview", "📈 Обзор", "dashboard"),
            ("/sessions", "💬 Диалоги", "chat"),
            ("/wishlist", "📋 Wishlist", "list"),
            ("/clients", "👥 Клиенты", "people"),
        ]
        
        # Settings только для super_admin
        if app.storage.user.get("role") == "super_admin":
            menu_items.append(("/settings", "⚙️ Настройки", "settings"))
        
        for path, label, icon in menu_items:
            ui.button(
                label,
                icon=icon,
                on_click=lambda p=path: ui.navigate.to(p)
            ).classes("w-full justify-start")
    
    return drawer
```

### 10.2 Funnel Chart

```python
# components/funnel_chart.py
from nicegui import ui

class FunnelChart:
    def __init__(self, tenant_id: str):
        # Данные воронки из conversation_sessions_v2
        stages = [
            {"name": "Начали диалог", "value": 100},
            {"name": "Выбрали услугу", "value": 75},
            {"name": "Выбрали мастера", "value": 60},
            {"name": "Выбрали время", "value": 45},
            {"name": "Записались", "value": 35},
        ]
        
        # ECharts funnel
        ui.echart({
            "series": [{
                "type": "funnel",
                "data": stages,
                "label": {"position": "inside"},
            }]
        }).classes("w-full h-64")
```

---

## 11. Стилизация

### 11.1 Dark Theme (по умолчанию)

```python
# main.py
ui.run(dark=True)
```

### 11.2 Кастомные стили

```python
# Добавление Tailwind-подобных классов
ui.add_head_html("""
<style>
    .kpi-card {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
        border-radius: 12px;
        padding: 20px;
    }
    .status-done { color: #4caf50; }
    .status-dropped { color: #ff9800; }
    .status-escalated { color: #f44336; }
</style>
""")
```

---

## 12. Чеклист разработки Frontend

### Phase 1: MVP

- [ ] `main.py` — Entry point + NiceGUI config
- [ ] `components/layout.py` — Shared layout
- [ ] `components/sidebar.py` — Navigation
- [ ] `pages/login.py` — Auth UI
- [ ] `pages/overview.py` — KPI cards + charts
- [ ] `pages/sessions.py` — Table + dialog viewer
- [ ] `pages/wishlist.py` — CRUD + realtime

### Phase 2: Polish

- [ ] `pages/clients.py` — Client list + LTM
- [ ] `pages/settings.py` — Tenant config
- [ ] Dark/Light theme toggle
- [ ] Responsive mobile layout
- [ ] Loading states + error handling

---

## 13. Ссылки

- [NiceGUI Documentation](https://nicegui.io/documentation)
- [ECharts Examples](https://echarts.apache.org/examples/)
- [01_BACKEND.md](./01_BACKEND.md) — Data layer
