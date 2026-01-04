# Phase 2: Features (Расширение)

## Обзор

**Срок:** 2-3 недели (после MVP)  
**Цель:** Добавить продвинутые функции для роста бизнеса.

---

## Scope Phase 2

| Фича | Описание |
|------|----------|
| 🎯 Smart Waitlist 2.0 | Визуализация рисковых слотов |
| 🔄 AI Win-Back Dashboard | Управление возвратом клиентов |
| 👥 Clients Page | Полный список клиентов + LTM |
| ⚙️ Tenant Settings | Настройки салона (super_admin) |
| 📊 Metrics Collector | Prefect job для сбора метрик |
| 🔔 Realtime Updates | Live обновления wishlist |

---

## Feature 1: Smart Waitlist 2.0

### Концепция

Показывать записи с высоким риском отмены рядом с wishlist для проактивного матчинга.

```
┌─────────────────────────────────────────────────────────────┐
│ 📋 Лист ожидания          │ ⚠️ Рисковые слоты               │
├───────────────────────────┼─────────────────────────────────┤
│ Мария — Маникюр, 31.12    │ Иван — Маникюр, 31.12 14:00    │
│ Ждёт: утро                │ Risk: 75% (давно не был)       │
│ [Match] [Cancel]          │ [Notify] [Ignore]              │
└───────────────────────────┴─────────────────────────────────┘
```

### Компоненты

**Таблица `predictions`:**
```sql
CREATE TABLE dashboard.predictions (
  id BIGSERIAL PRIMARY KEY,
  tenant_id UUID NOT NULL,
  booking_id TEXT NOT NULL,
  risk_score NUMERIC NOT NULL,  -- 0.0 - 1.0
  risk_factors JSONB,
  predicted_at TIMESTAMP DEFAULT now(),
  UNIQUE(tenant_id, booking_id)
);
```

**Risk Factors:**
```json
{
  "days_since_last_visit": 45,
  "cancel_rate": 0.3,
  "lead_time_days": 14,
  "is_new_client": false
}
```

### Чеклист
- [ ] Таблица `predictions`
- [ ] Job для расчёта риска
- [ ] UI: Split view (wishlist + risks)
- [ ] Action: Match wishlist → risky slot

---

## Feature 2: AI Win-Back Dashboard

### Концепция

Список клиентов "на вылет" с возможностью запустить win-back сообщение.

```
┌─────────────────────────────────────────────────────────────┐
│ 🔄 Клиенты на вылет                                         │
├─────────────────────────────────────────────────────────────┤
│ Клиент       │ Последний визит │ Цикл  │ Risk  │ Action    │
│ Мария П.     │ 25 дней назад   │ 14д   │ 🔴 80%│ [Вернуть] │
│ Иван С.      │ 20 дней назад   │ 21д   │ 🟡 50%│ [Вернуть] │
└─────────────────────────────────────────────────────────────┘
```

### Изменения в LTM

```sql
ALTER TABLE public.user_ltm_v2
  ADD COLUMN last_visit_date TIMESTAMPTZ,
  ADD COLUMN avg_visit_interval INTEGER,
  ADD COLUMN churn_risk_score NUMERIC DEFAULT 0.0;
```

### Алгоритм Churn Risk

```python
def calculate_churn_risk(ltm: dict) -> float:
    avg_interval = ltm.get("avg_visit_interval", 30)
    last_visit = parse_date(ltm["last_visit_date"])
    days_since = (now() - last_visit).days
    
    deviation = days_since / avg_interval
    
    if deviation < 1.0:
        return 0.0
    elif deviation < 1.3:
        return 0.3
    elif deviation < 1.5:
        return 0.6
    else:
        return 0.9
```

### Чеклист
- [ ] Миграция LTM
- [ ] Query: get_at_risk_clients()
- [ ] UI: Таблица с actions
- [ ] Integration: Trigger bot message

---

## Feature 3: Clients Page

### UI

```
┌─────────────────────────────────────────────────────────────┐
│ 🔍 [Search by name or phone...              ]               │
├─────────────────────────────────────────────────────────────┤
│ Имя          │ Телефон        │ Любимый мастер │ Визитов   │
│ Мария П.     │ +7 999 123-... │ Анна           │ 5         │
│ Иван С.      │ +7 999 456-... │ —              │ 2         │
└─────────────────────────────────────────────────────────────┘
```

### Query

```python
async def get_clients_with_ltm(tenant_id: str, search: str = None):
    sb = get_supabase()
    query = sb.table("clients_v2") \
        .select("*, user_ltm_v2(preferred_staff_id, ltm_data)") \
        .eq("tenant_id", tenant_id)
    
    if search:
        query = query.or_(f"full_name.ilike.%{search}%,phone.ilike.%{search}%")
    
    return query.order("created_at", desc=True).execute().data
```

### Чеклист
- [ ] `pages/clients.py`
- [ ] Search functionality
- [ ] LTM data display
- [ ] Client detail dialog

---

## Feature 4: Tenant Settings

### Доступ: `super_admin` only

### UI

```
┌─────────────────────────────────────────────────────────────┐
│ ⚙️ Настройки салона: Beauty Studio                          │
├─────────────────────────────────────────────────────────────┤
│ Название:     [Beauty Studio          ]                     │
│ YClients ID:  [123456                 ]                     │
│ Admin Chat:   [-1001234567890         ]                     │
│ Closing Time: [21:00                  ]                     │
│ Gap Filter:   [✓] Включить                                  │
├─────────────────────────────────────────────────────────────┤
│                                    [Сохранить]              │
└─────────────────────────────────────────────────────────────┘
```

### Редактирование metadata

```python
async def update_tenant_metadata(tenant_id: str, updates: dict):
    sb = get_supabase()
    
    # Получить текущий metadata
    tenant = sb.table("tenants_v2").select("metadata") \
        .eq("id", tenant_id).single().execute()
    
    current = tenant.data["metadata"]
    current.update(updates)
    
    # Сохранить
    sb.table("tenants_v2").update({"metadata": current}) \
        .eq("id", tenant_id).execute()
```

### Чеклист
- [ ] `pages/settings.py`
- [ ] Tenant selector (for super_admin)
- [ ] Metadata editor
- [ ] Validation

---

## Feature 5: Metrics Collector Job

### Prefect Flow

```python
from prefect import flow, task
from datetime import date, timedelta

@flow(name="Daily Metrics Collector")
async def collect_daily_metrics():
    yesterday = date.today() - timedelta(days=1)
    
    tenants = await get_active_tenants()
    for tenant in tenants:
        await collect_for_tenant(tenant["id"], yesterday)

@task
async def collect_for_tenant(tenant_id: str, target_date: date):
    sb = get_supabase()
    
    # Count sessions
    sessions = sb.table("conversation_sessions_v2") \
        .select("id", count="exact") \
        .eq("tenant_id", tenant_id) \
        .gte("started_at", target_date.isoformat()) \
        .lt("started_at", (target_date + timedelta(days=1)).isoformat()) \
        .execute()
    
    # Count bookings
    bookings = sb.table("conversation_sessions_v2") \
        .select("id", count="exact") \
        .eq("tenant_id", tenant_id) \
        .gte("started_at", target_date.isoformat()) \
        .not_.is_("booking_id", "null") \
        .execute()
    
    total = sessions.count or 0
    booked = bookings.count or 0
    
    # Upsert
    sb.schema("dashboard").table("metrics_dailies").upsert({
        "tenant_id": tenant_id,
        "day": target_date.isoformat(),
        "dialogs_started": total,
        "bookings": booked,
        "conversion": round(booked / total * 100, 2) if total else 0,
        "avg_response_ms": 0,
    }, on_conflict="tenant_id, day").execute()
```

### Расписание

```
0 1 * * * # Ежедневно в 01:00
```

### Чеклист
- [ ] `jobs/metrics_collector.py`
- [ ] Добавить в crontab
- [ ] Тестирование

---

## Feature 6: Realtime Updates

### Wishlist Live Updates

```python
from supabase import create_client

def setup_wishlist_realtime(tenant_id: str, table: ui.table):
    sb = get_supabase()
    channel = sb.channel(f"wishlist-{tenant_id}")
    
    def on_insert(payload):
        new = payload["new"]
        if new["status"] == "pending":
            table.add_rows([new])
            ui.notify("Новая заявка!")
    
    def on_update(payload):
        updated = payload["new"]
        if updated["status"] != "pending":
            table.remove_rows([{"id": updated["id"]}])
    
    channel.on_postgres_changes(event="INSERT", schema="public", 
        table="wishlist_v2", callback=on_insert)
    channel.on_postgres_changes(event="UPDATE", schema="public",
        table="wishlist_v2", callback=on_update)
    
    channel.subscribe()
```

### Чеклист
- [ ] Realtime subscription
- [ ] UI updates
- [ ] Fallback polling

---

## Критерии готовности Phase 2

| Критерий | Проверка |
|----------|----------|
| ✅ Clients отображаются | Поиск работает |
| ✅ Settings редактируются | Metadata сохраняется |
| ✅ Metrics собираются | Job без ошибок |
| ✅ Realtime работает | Wishlist обновляется live |

---

## Ссылки

- [05_PHASE1_MVP.md](./05_PHASE1_MVP.md) — Предыдущая фаза
- [07_PHASE3_MINIAPP.md](./07_PHASE3_MINIAPP.md) — Следующая фаза
