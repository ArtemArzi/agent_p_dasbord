# Backend спецификация

## 1. Обзор

Backend Dashboard отвечает за:
- Data Access Layer (запросы к Supabase)
- Бизнес-логику (агрегация метрик, фильтрация)
- Авторизацию и управление сессиями
- Background Jobs (сбор метрик)

> [!IMPORTANT]
> Dashboard использует **только Python**. Никакого JavaScript на бэкенде.

---

## 2. Структура файлов

```
agent-p-dashboard/
├── main.py           # Точка входа
├── config.py         # Конфигурация
├── auth.py           # Авторизация
├── data.py           # Data Access Layer
├── models.py         # Pydantic модели
└── jobs/
    └── metrics_collector.py
```

---

## 3. Конфигурация (`config.py`)

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Supabase
    supabase_url: str
    supabase_service_key: str  # service_role для записи в dashboard.*
    
    # App
    app_secret: str  # Для сессий
    app_port: int = 8080
    app_host: str = "0.0.0.0"
    
    # Optional
    debug: bool = False
    
    class Config:
        env_file = ".env"

settings = Settings()
```

### Переменные окружения

| Variable | Описание | Обязательно |
|----------|----------|-------------|
| `SUPABASE_URL` | URL проекта Supabase | ✅ |
| `SUPABASE_SERVICE_KEY` | Service Role Key | ✅ |
| `APP_SECRET` | Секрет для сессий | ✅ |
| `APP_PORT` | Порт приложения | ❌ (default: 8080) |
| `DEBUG` | Debug режим | ❌ (default: false) |

---

## 4. Pydantic модели (`models.py`)

### 4.1 User (Dashboard User)

```python
from pydantic import BaseModel, EmailStr
from uuid import UUID
from datetime import datetime
from typing import Optional, Literal

class User(BaseModel):
    id: int
    email: EmailStr
    role: Literal["super_admin", "admin", "staff"]
    tenant_id: Optional[UUID] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    active: bool = True
    created_at: datetime
```

### 4.2 DailyMetrics

```python
class DailyMetrics(BaseModel):
    """Дневные метрики для Overview page"""
    date: date
    tenant_id: UUID
    total_sessions: int = 0
    total_bookings: int = 0
    total_revenue: float = 0.0
    conversion_rate: float = 0.0
    top_services: list[dict] = []
    top_staff: list[dict] = []
```

### 4.3 Session (Conversation)

```python
class ConversationSession(BaseModel):
    """Сессия диалога для Sessions page"""
    id: int
    session_id: UUID
    tenant_id: UUID
    user_id: UUID
    channel: str
    started_at: datetime
    ended_at: Optional[datetime]
    duration_sec: Optional[int]
    final_status: str
    final_intent: Optional[str]
    booking_id: Optional[str]
    messages_count: Optional[int]
    meta: dict = {}
    
    # Computed
    client_name: Optional[str] = None
    sentiment: Optional[str] = None
    drop_off_stage: Optional[str] = None
```

### 4.4 WishlistItem

```python
class WishlistItem(BaseModel):
    """Элемент листа ожидания"""
    id: int
    tenant_id: UUID
    user_id: UUID
    item_type: str
    item_id: str
    source: Optional[str]
    comment: Optional[str]
    status: str = "pending"
    meta: dict = {}
    created_at: datetime
    processed_at: Optional[datetime]
    
    # Joined from clients_v2
    client_name: Optional[str] = None
    client_phone: Optional[str] = None
```

### 4.5 Client

```python
class Client(BaseModel):
    """Клиент салона"""
    id: UUID
    tenant_id: UUID
    telegram_chat_id: Optional[int]
    phone: Optional[str]
    full_name: Optional[str]
    created_at: datetime
    
    # From user_ltm_v2
    preferred_staff_id: Optional[str] = None
    preferred_service_id: Optional[str] = None
```

---

## 5. Data Access Layer (`data.py`)

### 5.1 Инициализация клиента

```python
from supabase import create_client, Client
from config import settings

# Singleton Supabase client
_supabase: Client | None = None

def get_supabase() -> Client:
    global _supabase
    if _supabase is None:
        _supabase = create_client(
            settings.supabase_url,
            settings.supabase_service_key
        )
    return _supabase
```

### 5.2 Queries: Overview

```python
from datetime import date, timedelta
from models import DailyMetrics

async def get_daily_metrics(
    tenant_id: str, 
    start_date: date, 
    end_date: date
) -> list[DailyMetrics]:
    """Получить метрики за период"""
    sb = get_supabase()
    
    response = sb.table("metrics_dailies") \
        .select("*") \
        .eq("tenant_id", tenant_id) \
        .gte("day", start_date.isoformat()) \
        .lte("day", end_date.isoformat()) \
        .order("day", desc=True) \
        .execute()
    
    return [DailyMetrics(**row) for row in response.data]


async def get_kpi_summary(tenant_id: str, days: int = 7) -> dict:
    """Агрегированные KPI за N дней"""
    sb = get_supabase()
    start = date.today() - timedelta(days=days)
    
    # Сессии
    sessions = sb.table("conversation_sessions_v2") \
        .select("id", count="exact") \
        .eq("tenant_id", tenant_id) \
        .gte("started_at", start.isoformat()) \
        .execute()
    
    # Записи (booking_id IS NOT NULL)
    bookings = sb.table("conversation_sessions_v2") \
        .select("id", count="exact") \
        .eq("tenant_id", tenant_id) \
        .gte("started_at", start.isoformat()) \
        .not_.is_("booking_id", "null") \
        .execute()
    
    total_sessions = sessions.count or 0
    total_bookings = bookings.count or 0
    conversion = (total_bookings / total_sessions * 100) if total_sessions > 0 else 0
    
    return {
        "sessions": total_sessions,
        "bookings": total_bookings,
        "conversion": round(conversion, 1),
    }
```

### 5.3 Queries: Sessions

```python
async def get_sessions(
    tenant_id: str,
    limit: int = 50,
    offset: int = 0,
    status_filter: str | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
) -> list[ConversationSession]:
    """Получить список сессий с пагинацией и фильтрами"""
    sb = get_supabase()
    
    query = sb.table("conversation_sessions_v2") \
        .select("*, clients_v2(full_name)") \
        .eq("tenant_id", tenant_id) \
        .order("started_at", desc=True) \
        .range(offset, offset + limit - 1)
    
    if status_filter:
        query = query.eq("final_status", status_filter)
    if date_from:
        query = query.gte("started_at", date_from.isoformat())
    if date_to:
        query = query.lte("started_at", date_to.isoformat())
    
    response = query.execute()
    
    sessions = []
    for row in response.data:
        session = ConversationSession(**row)
        session.client_name = row.get("clients_v2", {}).get("full_name")
        session.sentiment = row.get("meta", {}).get("sentiment")
        session.drop_off_stage = row.get("meta", {}).get("drop_off_stage")
        sessions.append(session)
    
    return sessions


async def get_session_history(session_id: str) -> list[dict]:
    """Получить историю сообщений сессии"""
    sb = get_supabase()
    
    response = sb.table("recent_history_v2") \
        .select("role, message, created_at") \
        .eq("session_id", session_id) \
        .order("created_at") \
        .execute()
    
    return response.data
```

### 5.4 Queries: Wishlist

```python
async def get_pending_wishlist(tenant_id: str) -> list[WishlistItem]:
    """Получить pending элементы wishlist"""
    sb = get_supabase()
    
    response = sb.table("wishlist_v2") \
        .select("*, clients_v2(full_name, phone)") \
        .eq("tenant_id", tenant_id) \
        .eq("status", "pending") \
        .order("created_at", desc=True) \
        .execute()
    
    items = []
    for row in response.data:
        item = WishlistItem(**row)
        client = row.get("clients_v2", {})
        item.client_name = client.get("full_name")
        item.client_phone = client.get("phone")
        items.append(item)
    
    return items


async def update_wishlist_status(
    item_id: int, 
    status: str, 
    processed_by: int | None = None
) -> bool:
    """Обновить статус wishlist элемента"""
    sb = get_supabase()
    
    update_data = {
        "status": status,
        "processed_at": datetime.now().isoformat(),
    }
    if processed_by:
        update_data["processed_by"] = processed_by
    
    response = sb.table("wishlist_v2") \
        .update(update_data) \
        .eq("id", item_id) \
        .execute()
    
    return len(response.data) > 0
```

### 5.5 Queries: Clients

```python
async def get_clients(
    tenant_id: str,
    limit: int = 50,
    offset: int = 0,
    search: str | None = None,
) -> list[Client]:
    """Получить список клиентов с LTM данными"""
    sb = get_supabase()
    
    query = sb.table("clients_v2") \
        .select("*, user_ltm_v2(preferred_staff_id, preferred_service_id)") \
        .eq("tenant_id", tenant_id) \
        .order("created_at", desc=True) \
        .range(offset, offset + limit - 1)
    
    if search:
        query = query.or_(f"full_name.ilike.%{search}%,phone.ilike.%{search}%")
    
    response = query.execute()
    
    clients = []
    for row in response.data:
        client = Client(**row)
        ltm = row.get("user_ltm_v2", [])
        if ltm and len(ltm) > 0:
            client.preferred_staff_id = ltm[0].get("preferred_staff_id")
            client.preferred_service_id = ltm[0].get("preferred_service_id")
        clients.append(client)
    
    return clients
```

---

## 6. Авторизация (`auth.py`)

### 6.1 Password Hashing

```python
import bcrypt

def hash_password(password: str) -> str:
    """Хэширование пароля"""
    return bcrypt.hashpw(
        password.encode(), 
        bcrypt.gensalt()
    ).decode()

def verify_password(password: str, hashed: str) -> bool:
    """Проверка пароля"""
    return bcrypt.checkpw(
        password.encode(), 
        hashed.encode()
    )
```

### 6.2 Login Flow

```python
from models import User
from data import get_supabase

async def authenticate(email: str, password: str) -> User | None:
    """Аутентификация пользователя"""
    sb = get_supabase()
    
    response = sb.schema("dashboard").table("users") \
        .select("*") \
        .eq("email", email) \
        .eq("active", True) \
        .single() \
        .execute()
    
    if not response.data:
        return None
    
    user_data = response.data
    if not verify_password(password, user_data["encrypted_password"]):
        return None
    
    return User(**user_data)
```

### 6.3 Auth Middleware (NiceGUI)

```python
from nicegui import app, ui

def require_auth():
    """Decorator для защищённых страниц"""
    def decorator(page_func):
        async def wrapper(*args, **kwargs):
            if not app.storage.user.get("authenticated"):
                ui.navigate.to("/login")
                return
            return await page_func(*args, **kwargs)
        return wrapper
    return decorator

# Использование:
@ui.page("/overview")
@require_auth()
async def overview_page():
    ...
```

---

## 7. Background Jobs (`jobs/metrics_collector.py`)

### 7.1 Daily Metrics Collector

```python
from prefect import flow, task, get_run_logger
from datetime import date, timedelta
from data import get_supabase

@task
async def collect_metrics_for_tenant(tenant_id: str, target_date: date):
    """Собрать метрики для одного тенанта"""
    logger = get_run_logger()
    sb = get_supabase()
    
    # 1. Считаем сессии
    sessions = sb.table("conversation_sessions_v2") \
        .select("id", count="exact") \
        .eq("tenant_id", tenant_id) \
        .gte("started_at", target_date.isoformat()) \
        .lt("started_at", (target_date + timedelta(days=1)).isoformat()) \
        .execute()
    
    # 2. Считаем записи
    bookings = sb.table("conversation_sessions_v2") \
        .select("id, booking_amount", count="exact") \
        .eq("tenant_id", tenant_id) \
        .gte("started_at", target_date.isoformat()) \
        .lt("started_at", (target_date + timedelta(days=1)).isoformat()) \
        .not_.is_("booking_id", "null") \
        .execute()
    
    total_sessions = sessions.count or 0
    total_bookings = bookings.count or 0
    total_revenue = sum(b.get("booking_amount", 0) or 0 for b in bookings.data)
    conversion = (total_bookings / total_sessions * 100) if total_sessions > 0 else 0
    
    # 3. Upsert в dashboard.metrics_dailies
    sb.schema("dashboard").table("metrics_dailies") \
        .upsert({
            "tenant_id": tenant_id,
            "day": target_date.isoformat(),
            "dialogs_started": total_sessions,
            "bookings": total_bookings,
            "conversion": round(conversion, 2),
        }, on_conflict="tenant_id,day") \
        .execute()
    
    logger.info(f"Collected metrics for {tenant_id}: {total_sessions} sessions, {total_bookings} bookings")


@flow(name="Daily Metrics Collector")
async def collect_daily_metrics(target_date: date | None = None):
    """
    Собирает метрики за указанную дату (по умолчанию — вчера).
    Запуск: ежедневно в 01:00 через cron.
    """
    logger = get_run_logger()
    
    if target_date is None:
        target_date = date.today() - timedelta(days=1)
    
    logger.info(f"Collecting metrics for {target_date}")
    
    # Получаем все активные тенанты
    sb = get_supabase()
    tenants = sb.table("tenants_v2") \
        .select("id") \
        .eq("is_active", True) \
        .execute()
    
    for tenant in tenants.data:
        await collect_metrics_for_tenant(tenant["id"], target_date)
    
    logger.info(f"Completed metrics collection for {len(tenants.data)} tenants")
```

---

## 8. Чеклист разработки Backend

### Phase 1: MVP

- [ ] `config.py` — Settings с env vars
- [ ] `models.py` — Базовые Pydantic модели
- [ ] `data.py` — Supabase client + базовые queries
- [ ] `auth.py` — Login/logout логика
- [ ] Middleware авторизации

### Phase 2: Features

- [ ] `jobs/metrics_collector.py` — Prefect flow
- [ ] Queries для клиентов с LTM
- [ ] Queries для tenant settings
- [ ] Realtime subscriptions (Supabase)

---

## 9. Ссылки

- [03_DATABASE.md](./03_DATABASE.md) — Схемы таблиц
- [04_INTEGRATIONS.md](./04_INTEGRATIONS.md) — Supabase Realtime, Auth
