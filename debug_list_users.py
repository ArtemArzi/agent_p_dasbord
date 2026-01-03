
import httpx
from config import settings

def debug_list_users():
    print(f"DEBUG: Supabase URL: {settings.supabase_url}")
    
    url = f"{settings.supabase_url}/rest/v1/rpc/get_all_dashboard_users"
    headers = {
        "apikey": settings.supabase_service_key,
        "Authorization": f"Bearer {settings.supabase_service_key}",
    }
    
    print(f"\n--- Fetching Users from {url} ---")
    try:
        with httpx.Client() as client:
            # Try POST first (standard for RPC)
            resp = client.post(url, headers=headers)
            print(f"POST Status: {resp.status_code}")
            print(f"POST Text: {resp.text[:500]}") # Truncate if long
            
            # Try GET if POST failed
            if resp.status_code != 200:
                print("\nTrying GET...")
                resp = client.get(url, headers=headers)
                print(f"GET Status: {resp.status_code}")
                print(f"GET Text: {resp.text[:500]}")
                
    except Exception as e:
        print(f"Request Failed: {e}")

if __name__ == "__main__":
    debug_list_users()
