"""
API Football Client for fetching match data from football-data.org
"""
import httpx
import time
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from config import settings


class APIFootballClient:
    """Client for football-data.org API"""
    
    def __init__(self):
        self.base_url = "https://api.football-data.org/v4"
        self.headers = {}
        
        # Add auth token if available (optional for free tier)
        if settings.API_FOOTBALL_KEY:
            self.headers["X-Auth-Token"] = settings.API_FOOTBALL_KEY
        
        self.client = httpx.Client(timeout=30.0)
        self.last_request_time = 0
        self.min_request_interval = 6.0  # 10 req/min = 1 req every 6 seconds
    
    def _rate_limit(self):
        """Ensure we don't exceed rate limits"""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.min_request_interval:
            time.sleep(self.min_request_interval - elapsed)
        self.last_request_time = time.time()
    
    def _make_request(self, endpoint: str, params: Dict = None) -> Dict:
        """Make API request with rate limiting and error handling"""
        self._rate_limit()
        
        url = f"{self.base_url}/{endpoint}"
        
        try:
            response = self.client.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            data = response.json()
            return data
        except httpx.HTTPError as e:
            print(f"❌ HTTP Error: {e}")
            raise
        except Exception as e:
            print(f"❌ Request Error: {e}")
            raise
    
    def get_leagues(self, season: int = 2024) -> List[Dict]:
        """Get information about supported leagues"""
        results = []
        
        # football-data.org league codes
        league_codes = {
            "premier_league": "PL",
            "serie_a": "SA", 
            "la_liga": "PD",
            "bundesliga": "BL1",
            "ligue_1": "FL1"
        }
        
        for league_key, league_code in league_codes.items():
            try:
                data = self._make_request(f"competitions/{league_code}")
                
                if data:
                    # Transform to our format
                    league_data = {
                        "league": {
                            "id": data.get("id"),
                            "name": data.get("name"),
                            "code": data.get("code"),
                            "emblem": data.get("emblem")
                        },
                        "country": {
                            "name": data.get("area", {}).get("name"),
                            "code": data.get("area", {}).get("code")
                        }
                    }
                    results.append(league_data)
                    print(f"✅ Fetched league: {data.get('name')}")
            except Exception as e:
                league_name = settings.LEAGUES.get(league_key, {}).get("name", league_key)
                print(f"❌ Error fetching {league_name}: {e}")
        
        return results
    
    def get_teams(self, league_code: str, season: int = 2024) -> List[Dict]:
        """Get teams for a specific league"""
        try:
            data = self._make_request(f"competitions/{league_code}/teams", {"season": season})
            
            teams = data.get("teams", [])
            
            # Transform to our format
            formatted_teams = []
            for team in teams:
                formatted_teams.append({
                    "team": {
                        "id": team.get("id"),
                        "name": team.get("name"),
                        "code": team.get("tla"),
                        "country": team.get("area", {}).get("name"),
                        "logo": team.get("crest")
                    }
                })
            
            print(f"✅ Fetched {len(formatted_teams)} teams for {league_code}")
            return formatted_teams
        except Exception as e:
            print(f"❌ Error fetching teams: {e}")
            return []
    
    def get_fixtures(
        self, 
        league_code: str,
        season: int = 2024,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
        status: Optional[str] = None
    ) -> List[Dict]:
        """
        Get fixtures/matches for a league
        
        Args:
            league_code: League code (PL, SA, PD, BL1, FL1)
            season: Season year
            from_date: Start date (YYYY-MM-DD)
            to_date: End date (YYYY-MM-DD)
            status: Match status (SCHEDULED, FINISHED, etc.)
        """
        params = {}
        
        if from_date:
            params["dateFrom"] = from_date
        if to_date:
            params["dateTo"] = to_date
        if status:
            params["status"] = status
        
        try:
            data = self._make_request(f"competitions/{league_code}/matches", params)
            matches = data.get("matches", [])
            
            # Transform to our format
            formatted_matches = []
            for match in matches:
                formatted_matches.append({
                    "fixture": {
                        "id": match.get("id"),
                        "date": match.get("utcDate"),
                        "status": {
                            "short": self._map_status(match.get("status"))
                        }
                    },
                    "teams": {
                        "home": {
                            "id": match.get("homeTeam", {}).get("id"),
                            "name": match.get("homeTeam", {}).get("name"),
                            "logo": match.get("homeTeam", {}).get("crest")
                        },
                        "away": {
                            "id": match.get("awayTeam", {}).get("id"),
                            "name": match.get("awayTeam", {}).get("name"),
                            "logo": match.get("awayTeam", {}).get("crest")
                        }
                    },
                    "goals": {
                        "home": match.get("score", {}).get("fullTime", {}).get("home"),
                        "away": match.get("score", {}).get("fullTime", {}).get("away")
                    },
                    "score": {
                        "halftime": {
                            "home": match.get("score", {}).get("halfTime", {}).get("home"),
                            "away": match.get("score", {}).get("halfTime", {}).get("away")
                        }
                    }
                })
            
            print(f"✅ Fetched {len(formatted_matches)} fixtures for {league_code}")
            return formatted_matches
        except Exception as e:
            print(f"❌ Error fetching fixtures: {e}")
            return []
    
    def _map_status(self, status: str) -> str:
        """Map football-data.org status to our format"""
        status_map = {
            "SCHEDULED": "NS",
            "TIMED": "NS",
            "IN_PLAY": "LIVE",
            "PAUSED": "HT",
            "FINISHED": "FT",
            "POSTPONED": "PST",
            "SUSPENDED": "SUSP",
            "CANCELLED": "CANC"
        }
        return status_map.get(status, status)
    
    def get_fixture_by_id(self, fixture_id: int) -> Optional[Dict]:
        """
        Get a single fixture by its ID
        
        Args:
            fixture_id: The API ID of the fixture
            
        Returns:
            Fixture data in our format or None if not found
        """
        try:
            data = self._make_request(f"matches/{fixture_id}")
            match = data  # football-data.org returns the match directly
            
            # Transform to our format
            formatted_match = {
                "fixture": {
                    "id": match.get("id"),
                    "date": match.get("utcDate"),
                    "status": {
                        "short": self._map_status(match.get("status"))
                    }
                },
                "teams": {
                    "home": {
                        "id": match.get("homeTeam", {}).get("id"),
                        "name": match.get("homeTeam", {}).get("name"),
                        "logo": match.get("homeTeam", {}).get("crest")
                    },
                    "away": {
                        "id": match.get("awayTeam", {}).get("id"),
                        "name": match.get("awayTeam", {}).get("name"),
                        "logo": match.get("awayTeam", {}).get("crest")
                    }
                },
                "goals": {
                    "home": match.get("score", {}).get("fullTime", {}).get("home"),
                    "away": match.get("score", {}).get("fullTime", {}).get("away")
                },
                "score": {
                    "halftime": {
                        "home": match.get("score", {}).get("halfTime", {}).get("home"),
                        "away": match.get("score", {}).get("halfTime", {}).get("away")
                    }
                }
            }
            
            print(f"✅ Fetched fixture {fixture_id}")
            return formatted_match
        except Exception as e:
            print(f"❌ Error fetching fixture {fixture_id}: {e}")
            return None
    
    def get_fixture_statistics(self, fixture_id: int) -> Dict:
        """Get detailed statistics for a specific match"""
        # Note: football-data.org free tier doesn't provide detailed match statistics
        # This would require a premium subscription
        print(f"⚠️  Match statistics not available in free tier")
        return {}
    
    def get_upcoming_fixtures(self, league_code: str, days: int = 7) -> List[Dict]:
        """Get upcoming fixtures for next N days"""
        today = datetime.now().date()
        future_date = today + timedelta(days=days)
        
        return self.get_fixtures(
            league_code=league_code,
            from_date=today.strftime("%Y-%m-%d"),
            to_date=future_date.strftime("%Y-%m-%d"),
            status="SCHEDULED"
        )
    
    def get_finished_fixtures(
        self, 
        league_code: str,
        season: int = 2024,
        last_days: int = 30
    ) -> List[Dict]:
        """Get recently finished fixtures"""
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=last_days)
        
        return self.get_fixtures(
            league_code=league_code,
            from_date=start_date.strftime("%Y-%m-%d"),
            to_date=end_date.strftime("%Y-%m-%d"),
            status="FINISHED"
        )
    
    def close(self):
        """Close HTTP client"""
        self.client.close()


# Example usage
if __name__ == "__main__":
    client = APIFootballClient()
    
    print("\n🔍 Testing football-data.org API Client...\n")
    
    # Get leagues
    leagues = client.get_leagues()
    print(f"\n📊 Found {len(leagues)} leagues")
    
    # Get Premier League teams
    if leagues:
        print("\n⚽ Fetching Premier League teams...")
        teams = client.get_teams("PL", season=2024)
        print(f"Found {len(teams)} teams in Premier League")
        
        # Get upcoming fixtures
        print("\n📅 Fetching upcoming matches...")
        upcoming = client.get_upcoming_fixtures("PL", days=7)
        print(f"Found {len(upcoming)} upcoming matches")
        
        # Get recent matches
        print("\n🏁 Fetching recent matches...")
        recent = client.get_finished_fixtures("PL", last_days=7)
        print(f"Found {len(recent)} recent matches")
    
    client.close()
    print("\n✅ Test completed!\n")

    
    def _rate_limit(self):
        """Ensure we don't exceed rate limits"""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.min_request_interval:
            time.sleep(self.min_request_interval - elapsed)
        self.last_request_time = time.time()
    
    def _make_request(self, endpoint: str, params: Dict = None) -> Dict:
        """Make API request with rate limiting and error handling"""
        self._rate_limit()
        
        url = f"{self.base_url}/{endpoint}"
        
        try:
            response = self.client.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            data = response.json()
            
            if "errors" in data and data["errors"]:
                raise Exception(f"API Error: {data['errors']}")
            
            return data
        except httpx.HTTPError as e:
            print(f"❌ HTTP Error: {e}")
            raise
        except Exception as e:
            print(f"❌ Request Error: {e}")
            raise
    
    def get_leagues(self, season: int = 2024) -> List[Dict]:
        """Get information about supported leagues"""
        results = []
        
        for league_key, league_info in settings.LEAGUES.items():
            try:
                data = self._make_request("leagues", {
                    "id": league_info["id"],
                    "season": season
                })
                
                if data.get("response"):
                    results.append(data["response"][0])
                    print(f"✅ Fetched league: {league_info['name']}")
            except Exception as e:
                print(f"❌ Error fetching {league_info['name']}: {e}")
        
        return results
    
    def get_teams(self, league_id: int, season: int = 2024) -> List[Dict]:
        """Get teams for a specific league"""
        try:
            data = self._make_request("teams", {
                "league": league_id,
                "season": season
            })
            
            teams = data.get("response", [])
            print(f"✅ Fetched {len(teams)} teams for league {league_id}")
            return teams
        except Exception as e:
            print(f"❌ Error fetching teams: {e}")
            return []
    
    def get_fixtures(
        self, 
        league_id: int, 
        season: int = 2024,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
        status: Optional[str] = None
    ) -> List[Dict]:
        """
        Get fixtures/matches for a league
        
        Args:
            league_id: League ID
            season: Season year
            from_date: Start date (YYYY-MM-DD)
            to_date: End date (YYYY-MM-DD)
            status: Match status (NS=Not Started, LIVE, FT=Finished, etc.)
        """
        params = {
            "league": league_id,
            "season": season
        }
        
        if from_date:
            params["from"] = from_date
        if to_date:
            params["to"] = to_date
        if status:
            params["status"] = status
        
        try:
            data = self._make_request("fixtures", params)
            fixtures = data.get("response", [])
            print(f"✅ Fetched {len(fixtures)} fixtures for league {league_id}")
            return fixtures
        except Exception as e:
            print(f"❌ Error fetching fixtures: {e}")
            return []
    
    def get_fixture_statistics(self, fixture_id: int) -> Dict:
        """Get detailed statistics for a specific match"""
        try:
            data = self._make_request("fixtures/statistics", {
                "fixture": fixture_id
            })
            
            stats = data.get("response", [])
            print(f"✅ Fetched statistics for fixture {fixture_id}")
            return stats
        except Exception as e:
            print(f"❌ Error fetching fixture statistics: {e}")
            return {}
    
    def get_upcoming_fixtures(self, league_id: int, days: int = 7) -> List[Dict]:
        """Get upcoming fixtures for next N days"""
        today = datetime.now().date()
        future_date = today + timedelta(days=days)
        
        return self.get_fixtures(
            league_id=league_id,
            season=today.year,
            from_date=today.strftime("%Y-%m-%d"),
            to_date=future_date.strftime("%Y-%m-%d"),
            status="NS"  # Not Started
        )
    
    def get_finished_fixtures(
        self, 
        league_id: int, 
        season: int = 2024,
        last_days: int = 30
    ) -> List[Dict]:
        """Get recently finished fixtures"""
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=last_days)
        
        return self.get_fixtures(
            league_id=league_id,
            season=season,
            from_date=start_date.strftime("%Y-%m-%d"),
            to_date=end_date.strftime("%Y-%m-%d"),
            status="FT"  # Finished
        )
    
    def close(self):
        """Close HTTP client"""
        self.client.close()


# Example usage
if __name__ == "__main__":
    client = APIFootballClient()
    
    # Test: Get Premier League info
    print("\n🔍 Testing API Football Client...\n")
    
    # Get leagues
    leagues = client.get_leagues(season=2024)
    print(f"\n📊 Found {len(leagues)} leagues")
    
    # Get Premier League teams
    if leagues:
        premier_league_id = settings.LEAGUES["premier_league"]["id"]
        teams = client.get_teams(premier_league_id, season=2024)
        print(f"\n⚽ Found {len(teams)} teams in Premier League")
        
        # Get upcoming fixtures
        upcoming = client.get_upcoming_fixtures(premier_league_id, days=7)
        print(f"\n📅 Found {len(upcoming)} upcoming matches")
    
    client.close()
    print("\n✅ Test completed!")
