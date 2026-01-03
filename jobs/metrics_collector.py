"""
Daily Metrics Collector Job.

This script should be scheduled to run daily (e.g., at 01:00 UTC) via cron or Prefect.
It calculates KPIs for the previous day for all tenants and stores them in `metrics_dailies`.
"""

import asyncio
from datetime import date, timedelta, datetime
import sys
import os

# Add parent dir to path to import config/data
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data import get_supabase, get_kpi_summary
from models import DailyMetrics

async def collect_metrics_for_tenant(tenant_id: str, target_date: date):
    """Calculate and save metrics for a single tenant."""
    try:
        # Get KPI summary for the specific date
        # Note: get_kpi_summary expects string dates YYYY-MM-DD
        date_str = target_date.isoformat()
        
        # Reuse existing logic from data.py
        kpi = get_kpi_summary(tenant_id, date_from=date_str, date_to=date_str)
        
        sb = get_supabase()
        
        # Prepare data for insertion
        metric_data = {
            "date": date_str,
            "tenant_id": tenant_id,
            "total_sessions": kpi["sessions"],
            "total_bookings": kpi["bookings"],
            "revenue": kpi["revenue"],
            "conversion_rate": kpi["conversion"],
            "updated_at": datetime.utcnow().isoformat()
        }
        
        # Upsert into metrics_dailies
        # Assuming there is a unique constraint on (tenant_id, date)
        result = sb.table("metrics_dailies") \
            .upsert(metric_data, on_conflict="tenant_id, date") \
            .execute()
        
        print(f"✅ Saved metrics for tenant {tenant_id}: {metric_data}")
        return True
        
    except Exception as e:
        print(f"❌ Error processing tenant {tenant_id}: {e}")
        return False

async def main():
    """Main execution flow."""
    print(f"🚀 Starting Metrics Collector for date: {date.today() - timedelta(days=1)}")
    
    sb = get_supabase()
    
    # 1. Get all tenants
    try:
        # We need all tenants using service role
        response = sb.table("tenants_v2").select("id").execute()
        tenants = response.data
        if not tenants:
            print("⚠️ No tenants found.")
            return
            
        print(f"found {len(tenants)} tenants to process.")
        
    except Exception as e:
        print(f"❌ Failed to fetch tenants: {e}")
        return

    # 2. Process each tenant
    target_date = date.today() - timedelta(days=1)
    
    success_count = 0
    for tenant in tenants:
        if await collect_metrics_for_tenant(tenant["id"], target_date):
            success_count += 1
            
    print(f"\n🏁 Finished. Successfully processed: {success_count}/{len(tenants)}")

if __name__ == "__main__":
    asyncio.run(main())
