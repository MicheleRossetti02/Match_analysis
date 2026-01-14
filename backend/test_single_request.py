import httpx
import os
import sys

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from config import settings

def test_single():
    url = "https://api-football-v1.p.rapidapi.com/v3/status"
    headers = {
        "X-RapidAPI-Key": settings.API_FOOTBALL_KEY,
        "X-RapidAPI-Host": settings.API_FOOTBALL_HOST
    }
    
    print(f"Testing URL: {url}")
    print(f"Key: {settings.API_FOOTBALL_KEY[:5]}...{settings.API_FOOTBALL_KEY[-5:]}")
    
    try:
        response = httpx.get(url, headers=headers)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_single()
