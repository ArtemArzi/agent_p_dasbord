# Интеграции

## 1. Обзор

Dashboard интегрируется с:
- **Supabase** — Database + Auth + Realtime  
- **Agent P Bot** — Communication через Supabase
- **YClients API** — Read-only для аналитики (Phase 2)

---

## 2. Supabase Client

### 2.1 Инициализация

```python
from supabase import create_client, Client
from config import settings

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

### 2.2 Работа со схемами

```python
# Чтение из public.* (bot data)
sb.table("conversation_sessions_v2").select("*").execute()

# Чтение/запись в dashboard.*
sb.schema("dashboard").table("users").select("*").execute()
```

---

## 3. Авторизация

Dashboard использует **собственную таблицу `dashboard.users`**.

### 3.1 Login Flow

```python
import bcrypt

async def authenticate(email: str, password: str) -> User | None:
    sb = get_supabase()
    
    response = sb.schema("dashboard").table("users") \
        .select("*").eq("email", email).eq("active", True).single().execute()
    
    if not response.data:
        return None
    
    if not bcrypt.checkpw(password.encode(), response.data["encrypted_password"].encode()):
        return None
    
    return User(**response.data)
```

### 3.2 Session (NiceGUI)

```python
from nicegui import app

# При логине
app.storage.user.update({
    "authenticated": True,
    "user_id": user.id,
    "role": user.role,
    "tenant_id": str(user.tenant_id),
})

# При логауте
app.storage.user.clear()
```

---

## 4. Supabase Realtime

### 4.1 Подписка

```python
def setup_realtime(tenant_id: str, on_change: callable):
    sb = get_supabase()
    channel = sb.channel(f"wishlist-{tenant_id}")
    
    channel.on_postgres_changes(
        event="INSERT",
        schema="public",
        table="wishlist_v2",
        filter=f"tenant_id=eq.{tenant_id}",
        callback=lambda p: on_change("insert", p["new"])
    )
    
    channel.subscribe()
    return channel
```

---

## 5. Bot Communication

Dashboard общается с ботом через Supabase (Event-Driven).

### 5.1 Таблица `bot_commands`

```sql
CREATE TABLE dashboard.bot_commands (
  id BIGSERIAL PRIMARY KEY,
  tenant_id UUID NOT NULL,
  command_type TEXT NOT NULL,
  payload JSONB NOT NULL,
  status TEXT DEFAULT 'pending',
  created_at TIMESTAMP DEFAULT now()
);
```

### 5.2 Пример

```python
# Dashboard ставит команду в очередь
await sb.schema("dashboard").table("bot_commands").insert({
    "tenant_id": tenant_id,
    "command_type": "send_message",
    "payload": {"client_id": "123", "message": "Привет!"},
}).execute()

# Bot обрабатывает команды (polling)
```

---

## 6. YClients API (Phase 2)

```python
class YClientsClient:
    BASE_URL = "https://api.yclients.com/api/v1"
    
    async def get_records(self, date_from: str, date_to: str):
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.BASE_URL}/records/{self.company_id}",
                headers=self.headers,
                params={"start_date": date_from, "end_date": date_to}
            )
            return response.json()["data"]
```

---

## 7. Чеклист

### Phase 1
- [ ] Supabase Client
- [ ] Custom Auth
- [ ] Session management

### Phase 2
- [ ] Realtime subscriptions
- [ ] bot_commands
- [ ] YClients client
