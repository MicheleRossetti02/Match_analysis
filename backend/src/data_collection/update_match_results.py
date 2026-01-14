"""
Update Match Results
Fetch finished match results from API and update predictions with actual outcomes
"""
import sys
import os
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from src.models.database import SessionLocal, Match, League
from src.data_collection.api_client import APIFootballClient
from src.services.prediction_accuracy_service import PredictionAccuracyService
from config import settings


def update_match_results(days_back: int = 7):
    """
    Fetch results for finished matches and update predictions with actual outcomes
    
    Args:
        days_back: Number of days to look back for finished matches
    """
    print(f"\n🔄 Updating match results for last {days_back} days...\n")
    
    db = SessionLocal()
    api_client = APIFootballClient()
    accuracy_service = PredictionAccuracyService(db)
    
    try:
        # Get all leagues
        leagues = db.query(League).all()
        print(f"Found {len(leagues)} leagues to check\n")
        
        updated_matches = 0
        
        # League code mapping (football-data.org uses codes)
        league_codes = {
            "Premier League": "PL",
            "Serie A": "SA",
            "La Liga": "PD",
            "Bundesliga": "BL1",
            "Ligue 1": "FL1"
        }
        
        for league in leagues:
            league_code = league_codes.get(league.name)
            if not league_code:
                print(f"⚠️  Skipping {league.name} - no code mapping")
                continue
            
            print(f"📊 Checking {league.name}...")
            
            try:
                # Fetch finished fixtures from API
                finished_fixtures = api_client.get_finished_fixtures(
                    league_code=league_code,
                    season=league.season,
                    last_days=days_back
                )
                
                print(f"  Found {len(finished_fixtures)} finished matches from API")
                
                # Update each match in database
                for fixture_data in finished_fixtures:
                    fixture_id = fixture_data.get("fixture", {}).get("id")
                    
                    if not fixture_id:
                        continue
                    
                    # Find match in database
                    match = db.query(Match).filter(Match.api_id == fixture_id).first()
                    
                    if not match:
                        continue
                    
                    # Get score data
                    home_goals = fixture_data.get("goals", {}).get("home")
                    away_goals = fixture_data.get("goals", {}).get("away")
                    
                    # Skip if no score data
                    if home_goals is None or away_goals is None:
                        continue
                    
                    # Update match with results if not already set
                    if match.home_goals is None or match.away_goals is None:
                        match.home_goals = home_goals
                        match.away_goals = away_goals
                        match.status = fixture_data.get("fixture", {}).get("status", {}).get("short", "FT")
                        
                        # Also update halftime score if available
                        halftime = fixture_data.get("score", {}).get("halftime", {})
                        if halftime:
                            match.home_goals_halftime = halftime.get("home")
                            match.away_goals_halftime = halftime.get("away")
                        
                        updated_matches += 1
                        print(f"  ✅ Updated: {match.home_team.name if match.home_team else 'Home'} {home_goals}-{away_goals} {match.away_team.name if match.away_team else 'Away'}")
                
            except Exception as e:
                print(f"  ❌ Error processing {league.name}: {e}")
                continue
        
        # Commit match updates
        db.commit()
        print(f"\n✅ Updated {updated_matches} matches with results\n")
        
        # Now update all predictions with actual outcomes
        print("🎯 Updating prediction accuracy...\n")
        result = accuracy_service.update_all_finished_matches()
        
        print(f"✅ Processed {result['matches_processed']} matches")
        print(f"✅ Updated {result['predictions_updated']} predictions\n")
        
        # Show accuracy stats
        print("📊 Current Accuracy Statistics:\n")
        stats = accuracy_service.get_accuracy_stats()
        
        print(f"Total Predictions: {stats['total_predictions']}")
        print(f"1X2 Accuracy: {stats['accuracy_1x2']['percentage']}% ({stats['accuracy_1x2']['correct']}/{stats['accuracy_1x2']['total']})")
        print(f"BTTS Accuracy: {stats['accuracy_btts']['percentage']}% ({stats['accuracy_btts']['correct']}/{stats['accuracy_btts']['total']})")
        print(f"Over 1.5 Accuracy: {stats['accuracy_over_15']['percentage']}% ({stats['accuracy_over_15']['correct']}/{stats['accuracy_over_15']['total']})")
        print(f"Over 2.5 Accuracy: {stats['accuracy_over_25']['percentage']}% ({stats['accuracy_over_25']['correct']}/{stats['accuracy_over_25']['total']})")
        print(f"Over 3.5 Accuracy: {stats['accuracy_over_35']['percentage']}% ({stats['accuracy_over_35']['correct']}/{stats['accuracy_over_35']['total']})")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        db.rollback()
    finally:
        api_client.close()
        db.close()
    
    print("\n✅ Update complete!\n")


if __name__ == "__main__":
    # Update results for last 7 days by default
    # Can be run daily via cron job
    update_match_results(days_back=7)
