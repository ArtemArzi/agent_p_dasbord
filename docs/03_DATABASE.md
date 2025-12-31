# Database спецификация

## 1. Обзор

Dashboard работает с двумя схемами в Supabase:
- **`public`** — схема бота Agent P (READ ONLY для Dashboard)
- **`dashboard`** — собственная схема Dashboard (READ/WRITE)

> [!IMPORTANT]
> Dashboard **никогда** не пишет в `public.*`. Это защищает целостность данных бота.

---

## 2. Архитектура схем

```mermaid
erDiagram
    PUBLIC_SCHEMA {
        tenants_v2 PK
        clients_v2 PK
        active_sessions_v2 PK
        conversation_sessions_v2 PK
        recent_history_v2 PK
        user_ltm_v2 PK
        wishlist_v2 PK
    }
    
    DASHBOARD_SCHEMA {
        users PK
        metrics_dailies PK
        alerts PK
        audits PK
        bookings PK
        conversations PK
    }
    
    DASHBOARD_SCHEMA ||--o{ PUBLIC_SCHEMA : "reads"
```

---

## 3. Схема `public.*` (Bot Data)

### 3.1 `tenants_v2` — Салоны

```sql
CREATE TABLE public.tenants_v2 (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name TEXT NOT NULL,
  slug TEXT UNIQUE,
  is_active BOOLEAN NOT NULL DEFAULT true,
  metadata JSONB NOT NULL DEFAULT '{}',
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

**Поле `metadata` содержит:**
```json
{
  "yclients_company_id": "123456",
  "yclients_token": "...",
  "telegram_bot_token": "...",
  "admin_chat_id": "-1001234567890",
  "enable_gap_filtering": true,
  "closing_time_override": "21:00",
  "current_branch": {
    "id": "456",
    "phone": "+7 999 123-45-67",
    "address": "ул. Примерная, 1"
  }
}
```

### 3.2 `clients_v2` — Клиенты

```sql
CREATE TABLE public.clients_v2 (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id UUID NOT NULL REFERENCES tenants_v2(id),
  telegram_chat_id BIGINT,
  whatsapp_id TEXT,
  phone TEXT,
  yclients_client_id BIGINT,
  full_name TEXT,
  meta JSONB NOT NULL DEFAULT '{}',
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_clients_tenant ON clients_v2(tenant_id);
CREATE INDEX idx_clients_phone ON clients_v2(phone);
```

### 3.3 `conversation_sessions_v2` — Архив сессий

```sql
CREATE TABLE public.conversation_sessions_v2 (
  id BIGSERIAL PRIMARY KEY,
  session_id UUID NOT NULL,
  tenant_id UUID NOT NULL REFERENCES tenants_v2(id),
  user_id UUID NOT NULL REFERENCES clients_v2(id),
  channel TEXT NOT NULL,  -- 'telegram', 'whatsapp'
  started_at TIMESTAMPTZ NOT NULL,
  ended_at TIMESTAMPTZ,
  duration_sec INTEGER,
  final_status TEXT NOT NULL,  -- 'done', 'dropped', 'escalated'
  final_intent TEXT,
  final_summary TEXT,
  booking_id TEXT,
  booking_source TEXT,
  booking_status TEXT,
  booking_datetime TIMESTAMPTZ,
  booking_amount NUMERIC,
  booking_currency TEXT,
  messages_count INTEGER,
  agent_messages_count INTEGER,
  user_messages_count INTEGER,
  meta JSONB NOT NULL DEFAULT '{}',
  summary TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_sessions_tenant ON conversation_sessions_v2(tenant_id);
CREATE INDEX idx_sessions_started ON conversation_sessions_v2(started_at);
CREATE INDEX idx_sessions_status ON conversation_sessions_v2(final_status);
```

**Поле `meta` содержит:**
```json
{
  "sentiment": "positive",
  "drop_off_stage": "time_selection",
  "services_mentioned": ["маникюр", "педикюр"],
  "analyzed_at": "2025-12-30T12:00:00Z"
}
```

### 3.4 `recent_history_v2` — История сообщений

```sql
CREATE TABLE public.recent_history_v2 (
  id BIGSERIAL PRIMARY KEY,
  tenant_id UUID NOT NULL REFERENCES tenants_v2(id),
  user_id UUID NOT NULL REFERENCES clients_v2(id),
  session_id UUID,
  role TEXT NOT NULL,  -- 'user', 'assistant'
  channel TEXT NOT NULL DEFAULT 'unknown',
  message TEXT NOT NULL,
  meta JSONB NOT NULL DEFAULT '{}',
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_history_session ON recent_history_v2(session_id);
CREATE INDEX idx_history_user ON recent_history_v2(user_id);
```

### 3.5 `wishlist_v2` — Лист ожидания

```sql
CREATE TABLE public.wishlist_v2 (
  id BIGSERIAL PRIMARY KEY,
  tenant_id UUID NOT NULL REFERENCES tenants_v2(id),
  user_id UUID NOT NULL REFERENCES clients_v2(id),
  item_type TEXT NOT NULL,  -- 'slot', 'service'
  item_id TEXT NOT NULL,
  source TEXT,
  comment TEXT,
  status TEXT NOT NULL DEFAULT 'pending',  -- 'pending', 'converted', 'cancelled', 'expired'
  meta JSONB NOT NULL DEFAULT '{}',
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  processed_at TIMESTAMPTZ
);

CREATE INDEX idx_wishlist_tenant ON wishlist_v2(tenant_id);
CREATE INDEX idx_wishlist_status ON wishlist_v2(status);
```

**Поле `meta` содержит:**
```json
{
  "service_title": "Маникюр",
  "staff_name": "Анна",
  "staff_id": "123",
  "preferred_date": "2025-12-31",
  "time_preference": "morning"
}
```

### 3.6 `user_ltm_v2` — Долгосрочная память

```sql
CREATE TABLE public.user_ltm_v2 (
  id BIGSERIAL PRIMARY KEY,
  tenant_id UUID NOT NULL REFERENCES tenants_v2(id),
  user_id UUID NOT NULL REFERENCES clients_v2(id),
  preferred_staff_id TEXT,
  preferred_service_id TEXT,
  preferred_time TEXT,
  language TEXT,
  allow_notifications BOOLEAN NOT NULL DEFAULT true,
  ltm_data JSONB NOT NULL DEFAULT '{}',
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  
  UNIQUE(tenant_id, user_id)
);
```

**Поле `ltm_data` содержит:**
```json
{
  "booking_stats": {
    "staff_123": 5,
    "staff_456": 2
  },
  "last_visit_date": "2025-12-15",
  "avg_visit_interval": 21
}
```

---

## 4. Схема `dashboard.*` (Dashboard Data)

### 4.1 `users` — Пользователи дашборда

```sql
CREATE TABLE dashboard.users (
  id BIGSERIAL PRIMARY KEY,
  email VARCHAR NOT NULL UNIQUE,
  encrypted_password VARCHAR NOT NULL,
  reset_password_token VARCHAR,
  reset_password_sent_at TIMESTAMP,
  remember_created_at TIMESTAMP,
  first_name VARCHAR,
  last_name VARCHAR,
  role VARCHAR NOT NULL DEFAULT 'staff',  -- 'super_admin', 'admin', 'staff'
  active BOOLEAN NOT NULL DEFAULT true,
  tenant_id UUID REFERENCES public.tenants_v2(id),
  created_at TIMESTAMP NOT NULL DEFAULT now(),
  updated_at TIMESTAMP NOT NULL DEFAULT now()
);

CREATE UNIQUE INDEX idx_users_email ON dashboard.users(email);
```

**Роли:**
| Роль | Описание | Доступ |
|------|----------|--------|
| `super_admin` | Владелец платформы | Все тенанты, настройки |
| `admin` | Владелец салона | Только свой tenant_id |
| `staff` | Сотрудник | Ограниченный доступ |

### 4.2 `metrics_dailies` — Дневные метрики

```sql
CREATE TABLE dashboard.metrics_dailies (
  id BIGSERIAL PRIMARY KEY,
  tenant_id UUID NOT NULL REFERENCES public.tenants_v2(id),
  day DATE NOT NULL,
  dialogs_started INTEGER NOT NULL DEFAULT 0,
  bookings INTEGER NOT NULL DEFAULT 0,
  conversion NUMERIC NOT NULL DEFAULT 0.0,
  avg_response_ms INTEGER NOT NULL DEFAULT 0,
  digest_sent_at TIMESTAMP,
  created_at TIMESTAMP NOT NULL DEFAULT now(),
  updated_at TIMESTAMP NOT NULL DEFAULT now(),
  
  UNIQUE(tenant_id, day)
);

CREATE INDEX idx_metrics_tenant_day ON dashboard.metrics_dailies(tenant_id, day);
```

### 4.3 `alerts` — Алерты

```sql
CREATE TABLE dashboard.alerts (
  id BIGSERIAL PRIMARY KEY,
  tenant_id UUID REFERENCES public.tenants_v2(id),
  kind VARCHAR NOT NULL,  -- 'low_conversion', 'high_drop_off', 'error_spike'
  threshold NUMERIC,
  actual NUMERIC,
  severity VARCHAR NOT NULL DEFAULT 'warning',  -- 'info', 'warning', 'critical'
  description TEXT,
  triggered_at TIMESTAMP NOT NULL,
  acknowledged_at TIMESTAMP,
  notification_sent_at TIMESTAMP,
  created_at TIMESTAMP NOT NULL DEFAULT now(),
  updated_at TIMESTAMP NOT NULL DEFAULT now()
);
```

### 4.4 `audits` — Аудит действий

```sql
CREATE TABLE dashboard.audits (
  id BIGSERIAL PRIMARY KEY,
  user_id BIGINT REFERENCES dashboard.users(id),
  tenant_id UUID,
  action VARCHAR NOT NULL,  -- 'login', 'update_settings', 'convert_wishlist'
  description TEXT NOT NULL,
  metadata JSON NOT NULL DEFAULT '{}',
  ip_address VARCHAR,
  user_agent VARCHAR,
  created_at TIMESTAMP NOT NULL DEFAULT now(),
  updated_at TIMESTAMP NOT NULL DEFAULT now()
);

CREATE INDEX idx_audits_user ON dashboard.audits(user_id);
CREATE INDEX idx_audits_tenant ON dashboard.audits(tenant_id);
```

### 4.5 `conversations` — Копия для Dashboard

```sql
CREATE TABLE dashboard.conversations (
  id BIGSERIAL PRIMARY KEY,
  tenant_id UUID,
  client_id VARCHAR NOT NULL,
  status VARCHAR NOT NULL DEFAULT 'active',  -- 'active', 'resolved', 'escalated'
  escalated BOOLEAN NOT NULL DEFAULT false,
  escalated_at TIMESTAMP,
  escalation_reason TEXT,
  closed_at TIMESTAMP,
  closure_reason TEXT,
  last_message_at TIMESTAMP,
  created_at TIMESTAMP NOT NULL DEFAULT now(),
  updated_at TIMESTAMP NOT NULL DEFAULT now()
);
```

### 4.6 `bookings` — Верификация записей

```sql
CREATE TABLE dashboard.bookings (
  id BIGSERIAL PRIMARY KEY,
  tenant_id UUID,
  external_id VARCHAR NOT NULL,  -- YClients booking ID
  client_id VARCHAR NOT NULL,
  start_at TIMESTAMP NOT NULL,
  service_code VARCHAR,
  status VARCHAR NOT NULL DEFAULT 'created',  -- 'created', 'confirmed', 'completed', 'cancelled'
  verified_at TIMESTAMP,
  verification_data JSON,
  yclients_attendance INTEGER,  -- 1=пришёл, 0=не пришёл
  created_at TIMESTAMP NOT NULL DEFAULT now(),
  updated_at TIMESTAMP NOT NULL DEFAULT now()
);

CREATE INDEX idx_bookings_tenant ON dashboard.bookings(tenant_id);
CREATE INDEX idx_bookings_external ON dashboard.bookings(external_id);
```

---

## 5. Миграции

### 5.1 Создание схемы dashboard

```sql
-- Migration: 001_create_dashboard_schema.sql

CREATE SCHEMA IF NOT EXISTS dashboard;

-- Grant usage to authenticated users
GRANT USAGE ON SCHEMA dashboard TO authenticated;
GRANT USAGE ON SCHEMA dashboard TO service_role;
```

### 5.2 Создание таблицы users

```sql
-- Migration: 002_create_dashboard_users.sql

CREATE TABLE dashboard.users (
  id BIGSERIAL PRIMARY KEY,
  email VARCHAR NOT NULL UNIQUE,
  encrypted_password VARCHAR NOT NULL,
  reset_password_token VARCHAR,
  reset_password_sent_at TIMESTAMP,
  first_name VARCHAR,
  last_name VARCHAR,
  role VARCHAR NOT NULL DEFAULT 'staff',
  active BOOLEAN NOT NULL DEFAULT true,
  tenant_id UUID REFERENCES public.tenants_v2(id),
  created_at TIMESTAMP NOT NULL DEFAULT now(),
  updated_at TIMESTAMP NOT NULL DEFAULT now()
);

-- Insert default super_admin
INSERT INTO dashboard.users (email, encrypted_password, role)
VALUES ('admin@example.com', '$2b$12$...', 'super_admin');
```

### 5.3 Создание таблицы metrics_dailies

```sql
-- Migration: 003_create_dashboard_metrics.sql

CREATE TABLE dashboard.metrics_dailies (
  id BIGSERIAL PRIMARY KEY,
  tenant_id UUID NOT NULL REFERENCES public.tenants_v2(id),
  day DATE NOT NULL,
  dialogs_started INTEGER NOT NULL DEFAULT 0,
  bookings INTEGER NOT NULL DEFAULT 0,
  conversion NUMERIC NOT NULL DEFAULT 0.0,
  avg_response_ms INTEGER NOT NULL DEFAULT 0,
  created_at TIMESTAMP NOT NULL DEFAULT now(),
  updated_at TIMESTAMP NOT NULL DEFAULT now(),
  
  UNIQUE(tenant_id, day)
);

CREATE INDEX idx_metrics_tenant_day ON dashboard.metrics_dailies(tenant_id, day);
```

---

## 6. Row Level Security (RLS)

### 6.1 Политики для `dashboard.users`

```sql
-- Enable RLS
ALTER TABLE dashboard.users ENABLE ROW LEVEL SECURITY;

-- Super admin видит всех
CREATE POLICY "Super admin can see all users"
  ON dashboard.users
  FOR SELECT
  USING (
    auth.jwt() ->> 'role' = 'super_admin'
  );

-- Admin видит только своих
CREATE POLICY "Admin can see own tenant users"
  ON dashboard.users
  FOR SELECT
  USING (
    tenant_id = (auth.jwt() ->> 'tenant_id')::uuid
  );
```

### 6.2 Политики для чтения `public.*`

```sql
-- Dashboard читает только свой tenant
CREATE POLICY "Dashboard reads own tenant sessions"
  ON public.conversation_sessions_v2
  FOR SELECT
  TO dashboard_reader
  USING (
    tenant_id = (auth.jwt() ->> 'tenant_id')::uuid
    OR auth.jwt() ->> 'role' = 'super_admin'
  );
```

---

## 7. SQL Views для Dashboard

### 7.1 Воронка конверсии

```sql
-- View: dashboard.v_conversion_funnel
CREATE VIEW dashboard.v_conversion_funnel AS
SELECT 
  tenant_id,
  DATE(started_at) as day,
  COUNT(*) as total_sessions,
  COUNT(*) FILTER (WHERE meta->>'drop_off_stage' IS NULL OR final_status = 'done') as completed,
  COUNT(*) FILTER (WHERE meta->>'drop_off_stage' = 'service_selection') as dropped_at_service,
  COUNT(*) FILTER (WHERE meta->>'drop_off_stage' = 'staff_selection') as dropped_at_staff,
  COUNT(*) FILTER (WHERE meta->>'drop_off_stage' = 'date_selection') as dropped_at_date,
  COUNT(*) FILTER (WHERE meta->>'drop_off_stage' = 'time_selection') as dropped_at_time
FROM public.conversation_sessions_v2
WHERE final_status IS NOT NULL
GROUP BY tenant_id, DATE(started_at);
```

### 7.2 Топ услуг

```sql
-- View: dashboard.v_top_services
CREATE VIEW dashboard.v_top_services AS
SELECT 
  tenant_id,
  DATE(started_at) as day,
  service_name,
  COUNT(*) as booking_count,
  SUM(booking_amount) as total_revenue
FROM public.conversation_sessions_v2,
     jsonb_array_elements_text(meta->'services_mentioned') as service_name
WHERE booking_id IS NOT NULL
GROUP BY tenant_id, DATE(started_at), service_name
ORDER BY booking_count DESC;
```

---

## 8. Индексы для производительности

```sql
-- Composite indexes for common Dashboard queries

-- Sessions list with filters
CREATE INDEX idx_sessions_tenant_status_date 
  ON public.conversation_sessions_v2(tenant_id, final_status, started_at DESC);

-- Wishlist pending items
CREATE INDEX idx_wishlist_tenant_pending 
  ON public.wishlist_v2(tenant_id) 
  WHERE status = 'pending';

-- Recent history by session
CREATE INDEX idx_history_session_created 
  ON public.recent_history_v2(session_id, created_at);

-- Metrics lookup
CREATE INDEX idx_metrics_lookup 
  ON dashboard.metrics_dailies(tenant_id, day DESC);
```

---

## 9. Чеклист миграций

### Phase 1: MVP

- [ ] `001_create_dashboard_schema.sql`
- [ ] `002_create_dashboard_users.sql`
- [ ] `003_create_dashboard_metrics.sql`
- [ ] Добавить `status`, `processed_at` в `wishlist_v2` (если нет)
- [ ] Создать индексы для Dashboard queries

### Phase 2: Features

- [ ] `004_create_dashboard_alerts.sql`
- [ ] `005_create_dashboard_audits.sql`
- [ ] `006_create_dashboard_bookings.sql`
- [ ] SQL Views для аналитики
- [ ] RLS политики

---

## 10. Ссылки

- [publick_схемы.md](../publick_схемы.md) — Полная схема public
- [dasbord_схемы.md](../dasbord_схемы.md) — Полная схема dashboard
- [01_BACKEND.md](./01_BACKEND.md) — Data Access Layer
