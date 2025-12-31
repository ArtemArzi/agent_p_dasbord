# Phase 1: MVP (Foundation)

## Обзор

**Срок:** 1-2 недели  
**Цель:** Запустить рабочий дашборд с базовой функциональностью.

---

## Scope MVP

| Страница | Функциональность |
|----------|------------------|
| 🔐 Login | Авторизация через dashboard.users |
| 📈 Overview | KPI cards, воронка конверсии |
| 💬 Sessions | Таблица диалогов + просмотр истории |
| 📋 Wishlist | Управление листом ожидания |

---

## Детальные задачи

### Task 1: Project Setup (Day 1)

**Цель:** Инициализировать репозиторий и зависимости.

#### Чеклист:
- [ ] Создать репозиторий `agent-p-dashboard`
- [ ] Структура директорий:
  ```
  agent-p-dashboard/
  ├── main.py
  ├── config.py
  ├── auth.py
  ├── data.py
  ├── models.py
  ├── pages/
  ├── components/
  ├── static/
  ├── requirements.txt
  └── Dockerfile
  ```
- [ ] `requirements.txt`:
  ```
  nicegui>=2.0.0
  supabase>=2.0.0
  pydantic>=2.0.0
  pydantic-settings>=2.0.0
  bcrypt>=4.0.0
  httpx>=0.27.0
  python-dotenv>=1.0.0
  ```
- [ ] `.env.example` с переменными
- [ ] `Dockerfile` для деплоя

---

### Task 2: Database Migrations (Day 1-2)

**Цель:** Подготовить схему dashboard в Supabase.

#### SQL Миграции:

```sql
-- 001: Create schema
CREATE SCHEMA IF NOT EXISTS dashboard;

-- 002: Create users table
CREATE TABLE dashboard.users (
  id BIGSERIAL PRIMARY KEY,
  email VARCHAR NOT NULL UNIQUE,
  encrypted_password VARCHAR NOT NULL,
  first_name VARCHAR,
  last_name VARCHAR,
  role VARCHAR NOT NULL DEFAULT 'admin',
  active BOOLEAN NOT NULL DEFAULT true,
  tenant_id UUID REFERENCES public.tenants_v2(id),
  created_at TIMESTAMP DEFAULT now(),
  updated_at TIMESTAMP DEFAULT now()
);

-- 003: Create metrics table
CREATE TABLE dashboard.metrics_dailies (
  id BIGSERIAL PRIMARY KEY,
  tenant_id UUID NOT NULL REFERENCES public.tenants_v2(id),
  day DATE NOT NULL,
  dialogs_started INTEGER DEFAULT 0,
  bookings INTEGER DEFAULT 0,
  conversion NUMERIC DEFAULT 0.0,
  UNIQUE(tenant_id, day)
);

-- 004: Add status to wishlist
ALTER TABLE public.wishlist_v2 
  ADD COLUMN IF NOT EXISTS status TEXT DEFAULT 'pending',
  ADD COLUMN IF NOT EXISTS processed_at TIMESTAMPTZ;
```

#### Чеклист:
- [ ] Выполнить миграции в Supabase SQL Editor
- [ ] Создать тестового пользователя:
  ```sql
  INSERT INTO dashboard.users (email, encrypted_password, role)
  VALUES ('admin@test.com', '$2b$12$...', 'super_admin');
  ```
- [ ] Проверить индексы на таблицах

---

### Task 3: Auth System (Day 2)

**Цель:** Реализовать вход/выход.

#### Файлы:

**`config.py`**
```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    supabase_url: str
    supabase_service_key: str
    app_secret: str
    app_port: int = 8080
    
    class Config:
        env_file = ".env"

settings = Settings()
```

**`auth.py`**
```python
import bcrypt
from data import get_supabase
from models import User

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode(), hashed.encode())

async def authenticate(email: str, password: str) -> User | None:
    sb = get_supabase()
    response = sb.schema("dashboard").table("users") \
        .select("*").eq("email", email).eq("active", True).single().execute()
    
    if not response.data:
        return None
    if not verify_password(password, response.data["encrypted_password"]):
        return None
    
    return User(**response.data)
```

**`pages/login.py`**
```python
from nicegui import ui, app
from auth import authenticate

@ui.page("/login")
async def login_page():
    if app.storage.user.get("authenticated"):
        ui.navigate.to("/overview")
        return
    
    with ui.card().classes("absolute-center w-80"):
        ui.label("Agent P Dashboard").classes("text-h5 text-center w-full")
        email = ui.input("Email").classes("w-full")
        password = ui.input("Пароль", password=True).classes("w-full")
        error = ui.label().classes("text-negative hidden")
        
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
                error.text = "Неверные данные"
                error.classes(remove="hidden")
        
        ui.button("Войти", on_click=try_login).classes("w-full mt-4")
```

#### Чеклист:
- [ ] `config.py` — Settings
- [ ] `auth.py` — authenticate()
- [ ] `pages/login.py` — Login UI
- [ ] Middleware require_auth()
- [ ] Logout functionality

---

### Task 4: Overview Page (Day 3-4)

**Цель:** Главная страница с KPI.

#### Компоненты:

**KPI Cards:**
- Сессии (7д)
- Записи (7д)
- Конверсия (%)
- (Доход — Phase 2)

**Воронка конверсии:**
- Начали диалог → Выбрали услугу → ... → Записались

#### Queries:

```python
async def get_kpi_summary(tenant_id: str, days: int = 7) -> dict:
    sb = get_supabase()
    start = date.today() - timedelta(days=days)
    
    sessions = sb.table("conversation_sessions_v2") \
        .select("id", count="exact") \
        .eq("tenant_id", tenant_id) \
        .gte("started_at", start.isoformat()).execute()
    
    bookings = sb.table("conversation_sessions_v2") \
        .select("id", count="exact") \
        .eq("tenant_id", tenant_id) \
        .gte("started_at", start.isoformat()) \
        .not_.is_("booking_id", "null").execute()
    
    total = sessions.count or 0
    booked = bookings.count or 0
    
    return {
        "sessions": total,
        "bookings": booked,
        "conversion": round(booked / total * 100, 1) if total else 0,
    }
```

#### Чеклист:
- [ ] `components/kpi_card.py`
- [ ] `pages/overview.py`
- [ ] KPI queries в `data.py`
- [ ] ECharts воронка (опционально)

---

### Task 5: Sessions Page (Day 4-5)

**Цель:** Просмотр диалогов бота.

#### UI:
- Таблица: ID, Дата, Клиент, Статус, Intent
- Фильтры: Статус, Дата
- Клик по строке → Dialog с историей

#### Queries:

```python
async def get_sessions(tenant_id: str, limit: int = 50) -> list:
    sb = get_supabase()
    response = sb.table("conversation_sessions_v2") \
        .select("*, clients_v2(full_name)") \
        .eq("tenant_id", tenant_id) \
        .order("started_at", desc=True) \
        .limit(limit).execute()
    return response.data

async def get_session_history(session_id: str) -> list:
    sb = get_supabase()
    response = sb.table("recent_history_v2") \
        .select("role, message, created_at") \
        .eq("session_id", session_id) \
        .order("created_at").execute()
    return response.data
```

#### Чеклист:
- [ ] `pages/sessions.py`
- [ ] ui.table с пагинацией
- [ ] Фильтры
- [ ] `components/chat_viewer.py` — Dialog

---

### Task 6: Wishlist Page (Day 5-6)

**Цель:** Управление листом ожидания.

#### UI:
- Таблица pending items
- Кнопки: ✅ Convert, ❌ Cancel, 📞 Contact

#### Actions:

```python
async def update_wishlist_status(item_id: int, status: str):
    sb = get_supabase()
    sb.table("wishlist_v2").update({
        "status": status,
        "processed_at": datetime.now().isoformat()
    }).eq("id", item_id).execute()
```

#### Чеклист:
- [ ] `pages/wishlist.py`
- [ ] CRUD операции
- [ ] Realtime updates (опционально)

---

### Task 7: Deploy (Day 6-7)

**Цель:** Деплой на Coolify.

#### Dockerfile:

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8080
CMD ["python", "main.py"]
```

#### Чеклист:
- [ ] Dockerfile
- [ ] docker-compose.yml (для локальной разработки)
- [ ] Добавить в Coolify
- [ ] Настроить домен
- [ ] Проверить production

---

## Критерии готовности MVP

| Критерий | Проверка |
|----------|----------|
| ✅ Авторизация работает | Логин/логаут без ошибок |
| ✅ Overview показывает данные | KPI отображаются корректно |
| ✅ Sessions загружаются | Таблица + просмотр истории |
| ✅ Wishlist управляется | Convert/Cancel работают |
| ✅ Деплой стабилен | Приложение доступно по URL |

---

## Ссылки

- [01_BACKEND.md](./01_BACKEND.md)
- [02_FRONTEND.md](./02_FRONTEND.md)
- [03_DATABASE.md](./03_DATABASE.md)
