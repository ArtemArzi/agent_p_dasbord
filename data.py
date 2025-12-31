"""Data Access Layer for Supabase."""

from supabase import create_client, Client
from config import settings

# Singleton Supabase client
_supabase: Client | None = None


def get_supabase() -> Client:
    """Get Supabase client (singleton pattern)."""
    global _supabase
    if _supabase is None:
        # Debug: check if service key is being used (not anon)
        key = settings.supabase_service_key
        if "service_role" not in key:
            print("⚠️  WARNING: SUPABASE_SERVICE_KEY may be anon key, not service_role!")
            print(f"   Key preview: {key[:50]}...")
        else:
            print("✅ Using service_role key")
        
        _supabase = create_client(
            settings.supabase_url,
            settings.supabase_service_key
        )
    return _supabase


# ============================================================
# Auth Queries
# ============================================================

def get_user_by_email(email: str) -> dict | None:
    """Get user by email from dashboard.users via RPC function."""
    try:
        sb = get_supabase()
        # Use RPC function since direct schema access via .schema() has issues
        response = sb.rpc("get_dashboard_user_by_email", {"user_email": email}).execute()
        
        return response.data
    except Exception as e:
        print(f"Error fetching user: {e}")
        return None


def get_tenants() -> list[dict]:
    """Get all tenants for super_admin tenant selector.
    
    WARNING: This returns ALL tenants without filtering.
    Should only be called from layout.py tenant selector which
    already verifies user_role == 'super_admin'.
    """
    try:
        sb = get_supabase()
        print(f"DEBUG get_tenants: calling supabase...")
        response = sb.table("tenants_v2").select("id, name").order("name").execute()
        print(f"DEBUG get_tenants: response.data = {response.data}")
        return response.data or []
    except Exception as e:
        print(f"Error fetching tenants: {e}")
        import traceback
        traceback.print_exc()
        return []


def get_tenant_settings(tenant_id: str) -> dict | None:
    """Get tenant with full metadata for settings page."""
    try:
        print(f"DEBUG get_tenant_settings: tenant_id = {tenant_id}")
        sb = get_supabase()
        response = sb.table("tenants_v2") \
            .select("*") \
            .eq("id", tenant_id) \
            .single() \
            .execute()
        print(f"DEBUG get_tenant_settings: response.data = {response.data is not None}")
        return response.data
    except Exception as e:
        print(f"Error fetching tenant settings: {e}")
        import traceback
        traceback.print_exc()
        return None


def update_tenant_metadata(
    tenant_id: str, 
    metadata: dict, 
    user_role: str = "", 
    user_tenant_id: str | None = None
) -> bool:
    """Update tenant metadata.
    
    Args:
        tenant_id: ID of tenant to update
        metadata: New metadata dict
        user_role: Role of current user (for authorization)
        user_tenant_id: Tenant ID of current user (for authorization)
    
    Returns:
        True if update succeeded, False otherwise
    """
    # Authorization check: super_admin can update any, others only their own
    if user_role != "super_admin" and user_tenant_id != tenant_id:
        print(f"Authorization failed: user with role '{user_role}' cannot update tenant {tenant_id}")
        return False
    
    try:
        from datetime import datetime
        sb = get_supabase()
        response = sb.table("tenants_v2") \
            .update({
                "metadata": metadata,
                "updated_at": datetime.utcnow().isoformat()
            }) \
            .eq("id", tenant_id) \
            .execute()
        return len(response.data) > 0
    except Exception as e:
        print(f"Error updating tenant metadata: {e}")
        return False



# ============================================================
# Overview Queries
# ============================================================

def get_kpi_summary(tenant_id: str, date_from: str | None = None, date_to: str | None = None) -> dict:
    """Get KPI summary for date range.
    
    Args:
        tenant_id: Tenant UUID
        date_from: Start date (YYYY-MM-DD), defaults to 7 days ago
        date_to: End date (YYYY-MM-DD), defaults to today
    """
    try:
        from datetime import date, timedelta
        sb = get_supabase()
        
        # Default to last 7 days if not specified
        if not date_from:
            date_from = (date.today() - timedelta(days=7)).isoformat()
        if not date_to:
            date_to = date.today().isoformat()
        
        # Total sessions
        sessions = sb.table("conversation_sessions_v2") \
            .select("id", count="exact") \
            .eq("tenant_id", tenant_id) \
            .gte("started_at", date_from) \
            .lte("started_at", date_to + "T23:59:59") \
            .execute()
        
        # Bookings (booking_id NOT NULL)
        bookings = sb.table("conversation_sessions_v2") \
            .select("id, booking_amount", count="exact") \
            .eq("tenant_id", tenant_id) \
            .gte("started_at", date_from) \
            .lte("started_at", date_to + "T23:59:59") \
            .not_.is_("booking_id", "null") \
            .execute()
        
        total = sessions.count or 0
        booked = bookings.count or 0
        revenue = sum(float(b.get("booking_amount") or 0) for b in bookings.data)
        
        return {
            "sessions": total,
            "bookings": booked,
            "conversion": round(booked / total * 100, 1) if total else 0,
            "revenue": revenue,
        }
    except Exception as e:
        print(f"Error fetching KPI: {e}")
        return {"sessions": 0, "bookings": 0, "conversion": 0, "revenue": 0}


def get_funnel_data(tenant_id: str, date_from: str | None = None, date_to: str | None = None) -> dict:
    """Get conversion funnel stages count for date range."""
    try:
        from datetime import date, timedelta
        sb = get_supabase()
        
        # Default to last 7 days if not specified
        if not date_from:
            date_from = (date.today() - timedelta(days=7)).isoformat()
        if not date_to:
            date_to = date.today().isoformat()
        
        result = sb.table("conversation_sessions_v2") \
            .select("meta, final_status") \
            .eq("tenant_id", tenant_id) \
            .gte("started_at", date_from) \
            .lte("started_at", date_to + "T23:59:59") \
            .execute()
        
        # Initialize counters
        stages = {
            "started": 0,
            "service_selected": 0,
            "staff_selected": 0,
            "time_selected": 0,
            "done": 0
        }
        
        for row in result.data:
            stages["started"] += 1
            meta = row.get("meta") or {}
            drop = meta.get("drop_off_stage")
            status = row.get("final_status")
            
            # Count progression
            if status == "done" or drop is None:
                stages["done"] += 1
                stages["time_selected"] += 1
                stages["staff_selected"] += 1
                stages["service_selected"] += 1
            elif drop == "time_selection":
                stages["staff_selected"] += 1
                stages["service_selected"] += 1
            elif drop == "staff_selection":
                stages["service_selected"] += 1
            # service_selection = didn't pass service step
        
        return stages
    except Exception as e:
        print(f"Error fetching funnel: {e}")
        return {"started": 0, "service_selected": 0, "staff_selected": 0, "time_selected": 0, "done": 0}


# ============================================================
# Sessions Queries
# ============================================================

def get_sessions(
    tenant_id: str,
    limit: int = 20,
    offset: int = 0,
    status_filter: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
) -> tuple[list[dict], int]:
    """Get sessions with filters and pagination. Returns (data, total_count)."""
    try:
        sb = get_supabase()
        
        query = sb.table("conversation_sessions_v2") \
            .select("*, clients_v2(full_name)", count="exact") \
            .eq("tenant_id", tenant_id) \
            .order("started_at", desc=True) \
            .range(offset, offset + limit - 1)
        
        if status_filter and status_filter != "all":
            query = query.eq("final_status", status_filter)
        if date_from:
            query = query.gte("started_at", date_from)
        if date_to:
            query = query.lte("started_at", date_to)
        
        response = query.execute()
        return response.data or [], response.count or 0
    except Exception as e:
        print(f"Error fetching sessions: {e}")
        return [], 0


def get_session_history(session_id: str, tenant_id: str) -> list[dict]:
    """Get message history for a session. Filtered by tenant_id for security."""
    try:
        sb = get_supabase()
        
        # First verify session belongs to tenant
        session_check = sb.table("conversation_sessions_v2") \
            .select("id") \
            .eq("session_id", session_id) \
            .eq("tenant_id", tenant_id) \
            .maybe_single() \
            .execute()
        
        if not session_check.data:
            print(f"Session {session_id} not found for tenant {tenant_id}")
            return []
        
        response = sb.table("recent_history_v2") \
            .select("role, message, created_at") \
            .eq("session_id", session_id) \
            .order("created_at") \
            .execute()
        
        return response.data or []
    except Exception as e:
        print(f"Error fetching history: {e}")
        return []


# ============================================================
# Wishlist Queries
# ============================================================

def get_wishlist_items(
    tenant_id: str,
    status_filter: str = "pending",
    limit: int = 20,
    offset: int = 0,
) -> tuple[list[dict], int]:
    """Get wishlist items with client info. Returns (data, total_count)."""
    try:
        sb = get_supabase()
        
        query = sb.table("wishlist_v2") \
            .select("*, clients_v2(full_name, phone)", count="exact") \
            .eq("tenant_id", tenant_id) \
            .order("created_at", desc=True) \
            .range(offset, offset + limit - 1)
        
        if status_filter and status_filter != "all":
            query = query.eq("status", status_filter)
        
        response = query.execute()
        return response.data or [], response.count or 0
    except Exception as e:
        print(f"Error fetching wishlist: {e}")
        return [], 0


def update_wishlist_status(item_id: int, status: str, tenant_id: str, amount: float | None = None) -> bool:
    """Mark wishlist item as processed/cancelled with optional amount."""
    # Validate status
    valid_statuses = {"pending", "converted", "cancelled"}
    if status not in valid_statuses:
        print(f"Invalid status: {status}. Must be one of {valid_statuses}")
        return False
    
    try:
        from datetime import datetime
        sb = get_supabase()
        
        update_data = {"status": status}
        if status != "pending":
            update_data["processed_at"] = datetime.utcnow().isoformat()
        else:
            update_data["processed_at"] = None
        
        # Add amount if provided (for converted status)
        if amount is not None:
            update_data["amount"] = amount
        
        response = sb.table("wishlist_v2") \
            .update(update_data) \
            .eq("id", item_id) \
            .eq("tenant_id", tenant_id) \
            .execute()
        
        return len(response.data) > 0
    except Exception as e:
        print(f"Error updating wishlist status: {e}")
        return False


def delete_wishlist_item(item_id: int, tenant_id: str) -> bool:
    """Delete wishlist item."""
    try:
        sb = get_supabase()
        
        response = sb.table("wishlist_v2") \
            .delete() \
            .eq("id", item_id) \
            .eq("tenant_id", tenant_id) \
            .execute()
        
        return len(response.data) > 0
    except Exception as e:
        print(f"Error deleting wishlist item: {e}")
        return False


def get_wishlist_stats(tenant_id: str) -> dict:
    """Get wishlist KPI statistics."""
    try:
        sb = get_supabase()
        response = sb.table("wishlist_v2") \
            .select("status, amount") \
            .eq("tenant_id", tenant_id) \
            .execute()
        
        stats = {
            "converted": 0,
            "cancelled": 0,
            "pending": 0,
            "total_revenue": 0.0
        }
        
        for row in response.data:
            status = row.get("status", "pending")
            if status in stats:
                stats[status] += 1
            if status == "converted" and row.get("amount"):
                stats["total_revenue"] += float(row["amount"])
        
        return stats
    except Exception as e:
        print(f"Error fetching wishlist stats: {e}")
        return {"converted": 0, "cancelled": 0, "pending": 0, "total_revenue": 0.0}
