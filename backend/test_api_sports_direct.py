import httpx
import os
import sys

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from config import settings

def test_api_sports():
    url = "https://v3.football.api-sports.io/status"
    headers = {
        "x-apisports-key": "cb8f75203548f8f7f622809b60e87ca3"
    }
    
    print(f"Testing API-Sports Direct")
    print(f"URL: {url}")
    print(f"Key: cb8f...3ca3\n")
    
    try:
        response = httpx.get(url, headers=headers, timeout=10.0)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Success!")
            print(f"Response: {data}\n")
            
            # Test getting leagues
            print("Testing /leagues endpoint...")
            leagues_url = "https://v3.football.api-sports.io/leagues"
            params = {"id": 39, "season": 2024}  # Premier League
            
            response2 = httpx.get(leagues_url, headers=headers, params=params, timeout=10.0)
            print(f"Status Code: {response2.status_code}")
            
            if response2.status_code == 200:
                data2 = response2.json()
                if data2.get("response"):
                    league = data2["response"][0]
                    print(f"✅ League found: {league['league']['name']}")
                print(f"\n🎉 API-Sports is working perfectly!")
            else:
                print(f"❌ Error: {response2.text}")
        else:
            print(f"❌ Error: {response.text}")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_api_sports()
