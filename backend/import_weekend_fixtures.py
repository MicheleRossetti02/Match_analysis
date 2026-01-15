"""
Weekend Fixture Import Script
Fetches upcoming matches for top 5 leagues and generates v4-ultra predictions
"""
import sys
import os
sys.path.append(os.path.dirname(__file__))

from src.models.database import SessionLocal, Match, League
from src.data_collection.api_client import APIFootballClient
from datetime import datetime, timedelta
import time

print("\n" + "="*80)
print("🏟️  WEEKEND FIXTURE IMPORT")
print("   Fetching upcoming matches for top 5 leagues")
print("="*80 + "\n")

# Initialize
db = SessionLocal()
api_client = APIFootballClient()

# Top 5 leagues (API-FOOTBALL IDs)
LEAGUES = {
    39: "Premier League",
    135: "Serie A",
    140: "La Liga",
    78: "Bundesliga",
    61: "Ligue 1"
}

total_imported = 0

try:
    for league_api_id, league_name in LEAGUES.items():
        print(f"\n📅 Fetching {league_name}...")
        
        # Get league from DB
        league = db.query(League).filter(League.api_id == league_api_id).first()
        if not league:
            print(f"   ⚠️  League not found in database, skipping")
            continue
        
        # Fetch upcoming fixtures (next 14 days)
        try:
            fixtures = api_client.get_fixtures(
                league_id=league_api_id,
                season=2024,
                next=10  # Next 10 matches
            )
            
            if not fixtures:
                print(f"   ℹ️  No upcoming fixtures found")
                continue
            
            imported_count = 0
            
            for fixture in fixtures:
                # Check if already exists
                existing = db.query(Match).filter(Match.api_id == fixture['fixture']['id']).first()
                
                if existing:
                    # Update if needed
                    existing.status = fixture['fixture']['status']['short']
                    existing.match_date = datetime.fromisoformat(fixture['fixture']['date'].replace('Z', '+00:00'))
                else:
                    # Create new match
                    match = Match(
                        api_id=fixture['fixture']['id'],
                        league_id=league.id,
                        season=2024,
                        match_date=datetime.fromisoformat(fixture['fixture']['date'].replace('Z', '+00:00')),
                        status=fixture['fixture']['status']['short'],
                        home_team_id=fixture['teams']['home']['id'],
                        away_team_id=fixture['teams']['away']['id'],
                        round=fixture['league']['round']
                    )
                    db.add(match)
                    imported_count += 1
            
            db.commit()
            total_imported += imported_count
            print(f"   ✅ Imported {imported_count} new matches")
            
            # Rate limiting
            time.sleep(1)
            
        except Exception as e:
            print(f"   ❌ Error: {e}")
            db.rollback()
            continue
    
    print(f"\n{"="*80}")
    print(f"✅ IMPORT COMPLETE")
    print(f"   Total new matches imported: {total_imported}")
    print(f"{"="*80}\n")
    
except Exception as e:
    print(f"\n❌ Fatal error: {e}")
    db.rollback()
    raise

finally:
    db.close()
    api_client.close()
