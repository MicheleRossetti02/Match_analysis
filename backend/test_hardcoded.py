import httpx

def test_direct():
    url = "https://v3.football.api-sports.io/leagues"
    headers = {
        "x-apisports-key": "cb8f75203548f8f7f622809b60e87ca3"
    }
    params = {"id": 39, "season": 2024}
    
    print("Testing with hardcoded key:")
    print(f"Headers: {headers}\n")
    
    try:
        response = httpx.get(url, headers=headers, params=params, timeout=10.0)
        print(f"Status: {response.status_code}")
        data = response.json()
        
        if data.get("errors"):
            print(f"Errors: {data['errors']}")
        
        if data.get("response"):
            league = data["response"][0]
            print(f"✅ Success! Found: {league['league']['name']}")
        else:
            print(f"Response: {data}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_direct()
