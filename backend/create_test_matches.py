"""
Create Test Matches for Weekend Demo
Creates 3 upcoming matches with 'NS' status for testing predictions
"""
import sys
import os
sys.path.append(os.path.dirname(__file__))

from src.models.database import SessionLocal, Match, Team, League
from datetime import datetime, timedelta

print("\n" + "="*80)
print("🎯 CREATING TEST MATCHES FOR DEMO")
print("="*80 + "\n")

db = SessionLocal()

try:
    # Get a league (Serie A)
    league = db.query(League).filter(League.name.like('%Serie A%')).first()
    if not league:
        print("❌ No league found")
        sys.exit(1)
    
    # Get some teams
    teams = db.query(Team).filter(Team.league_id == league.id).limit(6).all()
    
    if len(teams) < 6:
        print(f"❌ Not enough teams found (need 6, found {len(teams)})")
        sys.exit(1)
    
    # Create 3 test matches for this weekend
    now = datetime.utcnow()
    weekend_start = now + timedelta(days=2)
    
    test_matches = [
        {
            'home': teams[0],
            'away': teams[1],
            'date': weekend_start,
            'round': 'Test Round 1'
        },
        {
            'home': teams[2],
            'away': teams[3],
            'date': weekend_start + timedelta(hours=3),
            'round': 'Test Round 1'
        },
        {
            'home': teams[4],
            'away': teams[5],
            'date': weekend_start + timedelta(hours=6),
            'round': 'Test Round 1'
        }
    ]
    
    created_matches = []
    
    for i, match_data in enumerate(test_matches, 1):
        # Create unique API ID
        api_id = 999000 + i
        
        # Check if exists
        existing = db.query(Match).filter(Match.api_id == api_id).first()
        if existing:
            print(f"   Match {i}: Already exists (ID: {existing.id})")
            created_matches.append(existing)
            continue
        
        match = Match(
            api_id=api_id,
            league_id=league.id,
            season=2024,
            match_date=match_data['date'],
            round=match_data['round'],
            status='NS',  # Not Started
            home_team_id=match_data['home'].id,
            away_team_id=match_data['away'].id
        )
        
        db.add(match)
        db.flush()
        created_matches.append(match)
        
        print(f"   ✅ Match {i}: {match_data['home'].name} vs {match_data['away'].name}")
        print(f"      Date: {match_data['date'].strftime('%Y-%m-%d %H:%M')}")
        print(f"      Match ID: {match.id}")
    
    db.commit()
    
    print(f"\n{'='*80}")
    print(f"✅ CREATED {len([m for m in created_matches if m.id])} TEST MATCHES")
    print(f"   Match IDs: {[m.id for m in created_matches]}")
    print(f"{'='*80}\n")
    
    # Return match IDs for prediction generation
    return [m.id for m in created_matches]

except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
    db.rollback()
    raise

finally:
    db.close()

if __name__ == "__main__":
    create_test_matches()
