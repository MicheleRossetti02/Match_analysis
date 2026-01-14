"""
Update Specific Matches
Update the 34 matches that have predictions
"""
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from src.models.database import SessionLocal, Match, Prediction
from src.data_collection.api_client import APIFootballClient
from src.services.prediction_accuracy_service import PredictionAccuracyService

def update_predicted_matches():
    """Update all matches that have predictions"""
    
    print("=" * 80)
    print("🔄 UPDATING MATCHES WITH PREDICTIONS")
    print("=" * 80)
    
    db = SessionLocal()
    api_client = APIFootballClient()
    accuracy_service = PredictionAccuracyService(db)
    
    try:
        # Get all matches that have predictions
        predictions = db.query(Prediction).all()
        print(f"\nFound {len(predictions)} predictions")
        
        match_ids = list(set([p.match_id for p in predictions]))
        print(f"For {len(match_ids)} unique matches\n")
        
        updated_count = 0
        
        for match_id in match_ids:
            match = db.query(Match).filter(Match.id == match_id).first()
            
            if not match:
                print(f"⚠️  Match ID {match_id} not found")
                continue
            
            print(f"\n📊 Processing Match ID {match_id}:")
            print(f"   {match.home_team.name if match.home_team else 'Home'} vs {match.away_team.name if match.away_team else 'Away'}")
            print(f"   Date: {match.match_date}")
            print(f"   API ID: {match.api_id}")
            print(f"   Current Status: {match.status}")
            
            try:
                # Fetch match details from API
                fixture_data = api_client.get_fixture_by_id(match.api_id)
                
                if not fixture_data:
                    print(f"   ❌ No data from API")
                    continue
                
                # Get score data
                home_goals = fixture_data.get("goals", {}).get("home")
                away_goals = fixture_data.get("goals", {}).get("away")
                new_status = fixture_data.get("fixture", {}).get("status", {}).get("short", "NS")
                
                print(f"   API Status: {new_status}")
                
                if home_goals is not None and away_goals is not None:
                    match.home_goals = home_goals
                    match.away_goals = away_goals
                    match.status = new_status
                    
                    # Also update halftime score if available
                    halftime = fixture_data.get("score", {}).get("halftime", {})
                    if halftime:
                        match.home_goals_halftime = halftime.get("home")
                        match.away_goals_halftime = halftime.get("away")
                    
                    print(f"   ✅ Updated: {home_goals}-{away_goals}")
                    updated_count += 1
                else:
                    print(f"   ⏳ Match not played yet")
                    
            except Exception as e:
                print(f"   ❌ Error: {e}")
                continue
        
        # Commit updates
        db.commit()
        print(f"\n{'='*80}")
        print(f"✅ Updated {updated_count}/{len(match_ids)} matches")
        print(f"{'='*80}\n")
        
        # Now update predictions
        if updated_count > 0:
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
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        api_client.close()
        db.close()
    
    print("\n✅ Update complete!\n")

if __name__ == "__main__":
    update_predicted_matches()
