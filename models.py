"""Pydantic models for Agent P Dashboard."""

from pydantic import BaseModel, EmailStr, ConfigDict
from uuid import UUID
from datetime import datetime, date
from typing import Optional, Literal


class User(BaseModel):
    """Dashboard user model."""
    id: int
    email: EmailStr
    role: Literal["super_admin", "admin", "staff"]
    tenant_id: Optional[UUID] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    active: bool = True
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class DailyMetrics(BaseModel):
    """Daily metrics for Overview page."""
    day: date
    tenant_id: UUID
    dialogs_started: int = 0
    bookings: int = 0
    conversion: float = 0.0
    avg_response_ms: int = 0


class ConversationSession(BaseModel):
    """Conversation session for Sessions page."""
    id: int
    session_id: UUID
    tenant_id: UUID
    user_id: UUID
    channel: str
    started_at: datetime
    ended_at: Optional[datetime] = None
    duration_sec: Optional[int] = None
    final_status: str
    final_intent: Optional[str] = None
    booking_id: Optional[str] = None
    messages_count: Optional[int] = None
    meta: dict = {}
    
    # Computed / Joined
    client_name: Optional[str] = None
    sentiment: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)


class WishlistItem(BaseModel):
    """Wishlist item model."""
    id: int
    tenant_id: UUID
    user_id: UUID
    item_type: str
    item_id: str
    source: Optional[str] = None
    comment: Optional[str] = None
    status: str = "pending"
    meta: dict = {}
    created_at: datetime
    processed_at: Optional[datetime] = None
    
    # Joined from clients_v2
    client_name: Optional[str] = None
    client_phone: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)


class Client(BaseModel):
    """Client model."""
    id: UUID
    tenant_id: UUID
    telegram_chat_id: Optional[int] = None
    phone: Optional[str] = None
    full_name: Optional[str] = None
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class UserCreate(BaseModel):
    """Payload for creating a new user."""
    email: EmailStr
    password: str
    role: Literal["super_admin", "admin", "staff"]
    tenant_id: Optional[UUID] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None

