"""
Real Weekend Fixture Import with Automatic Team Creation
Imports upcoming matches AND creates teams on-the-fly
"""
import sys
import os
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv

sys.path.append(os.path.dirname(__file__))
from src.models.database import SessionLocal, Match, League, Team

load_dotenv()

FOOTBALL_DATA_API_KEY = os.getenv('FOOTBALL_DATA_API_KEY')
BASE_URL = "https://api.football-data.org/v4"

# Football-Data.org league codes
LEAGUES = {
    'PL': ('Premier League', 2021),
    'SA': ('Serie A', 2019),
    'PD': ('La Liga', 2014),
    'BL1': ('Bundesliga', 2002),
    'FL1': ('Ligue 1', 2015)
}

print("\n" + "="*80)
print("🏟️  REAL WEEKEND FIXTURE IMPORT - WITH TEAM CREATION")
print("="*80 + "\n")

if not FOOTBALL_DATA_API_KEY:
    print("❌ API Key not found")
    sys.exit(1)

db = SessionLocal()
headers = {'X-Auth-Token': FOOTBALL_DATA_API_KEY}

# Date range
now = datetime.utcnow()
date_from = now.strftime('%Y-%m-%d')
date_to = (now + timedelta(hours=72)).strftime('%Y-%m-%d')

print(f"📅 Fetching: {date_from} to {date_to}\n")

total_imported = 0
total_teams_created = 0

try:
    for league_code, (league_name, league_api_id) in LEAGUES.items():
        print(f"\n🔍 {league_name}...")
       
        league = db.query(League).filter(League.api_id == league_api_id).first()
        if not league:
            print(f"   ⚠️  League not in DB, skipping")
            continue
        
        url = f"{BASE_URL}/competitions/{league_code}/matches"
        params = {'dateFrom': date_from, 'dateTo': date_to}
        
        try:
            response = requests.get(url, headers=headers, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                matches = data.get('matches', [])
                print(f"   Found {len(matches)} matches")
                
                for match_data in matches:
                    # Get or create home team
                    home_team_data = match_data['homeTeam']
                    home_team = db.query(Team).filter(Team.name == home_team_data['name']).first()
                    if not home_team:
                        home_team = Team(
                            api_id=home_team_data.get('id', 0),
                            name=home_team_data['name'],
                            code=home_team_data.get('tla', home_team_data['name'][:3]),
                            country=league_name.split()[-1] if ' ' in league_name else league_name,
                            league_id=league.id
                        )
                        db.add(home_team)
                        db.flush()
                        total_teams_created += 1
                        print(f"   ✅ Created team: {home_team.name}")
                    
                    # Get or create away team
                    away_team_data = match_data['awayTeam']
                    away_team = db.query(Team).filter(Team.name == away_team_data['name']).first()
                    if not away_team:
                        away_team = Team(
                            api_id=away_team_data.get('id', 0),
                            name=away_team_data['name'],
                            code=away_team_data.get('tla', away_team_data['name'][:3]),
                            country=league_name.split()[-1] if ' ' in league_name else league_name,
                            league_id=league.id
                        )
                        db.add(away_team)
                        db.flush()
                        total_teams_created += 1
                        print(f"   ✅ Created team: {away_team.name}")
                    
                    # Check if match exists
                    match_id = match_data['id']
                    existing = db.query(Match).filter(Match.api_id == match_id).first()
                    
                    if not existing:
                        # Create match
                        match = Match(
                            api_id=match_id,
                            league_id=league.id,
                            season=2024,
                            match_date=datetime.fromisoformat(match_data['utcDate'].replace('Z', '+00:00')),
                            round=match_data.get('matchday', 'Unknown'),
                            status=match_data['status'],
                            home_team_id=home_team.id,
                            away_team_id=away_team.id
                        )
                        db.add(match)
                        total_imported += 1
                        print(f"   📅 Imported: {home_team.name} vs {away_team.name}")
                
                db.commit()
                
            elif response.status_code == 429:
                print(f"   ⚠️  Rate limit - waiting...")
            else:
                print(f"   ❌ Error: {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ {e}")
            continue
    
    print(f"\n{'='*80}")
    print(f"✅ IMPORT COMPLETE")
    print(f"   New teams: {total_teams_created}")
    print(f"   New matches: {total_imported}")
    print(f"{'='*80}\n")

except Exception as e:
    print(f"\n❌ Fatal error: {e}")
    import traceback
    traceback.print_exc()
    db.rollback()
    
finally:
    db.close()
