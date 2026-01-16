#!/usr/bin/env python3
"""Admin script to clear database via production API endpoint."""

import requests

def clear_database_via_api():
    """Clear database via API call to production."""
    try:
        # Make request to clear database
        response = requests.post('https://bitoki.onrender.com/api/admin/clear-db', 
                               data={'confirm': 'yes'},
                               timeout=30)
        
        if response.status_code == 200:
            print("SUCCESS: Database cleared successfully!")
            return True
        else:
            print(f"ERROR: API returned {response.status_code}: {response.text}")
            return False
            
    except Exception as e:
        print(f"ERROR: {e}")
        return False

if __name__ == "__main__":
    print("BITOKI Database Clear via API")
    print("=" * 40)
    clear_database_via_api()