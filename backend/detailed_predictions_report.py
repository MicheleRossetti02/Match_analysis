"""
Detailed Predictions Report
Shows all predictions and their match status
"""
import sqlite3
import os
from datetime import datetime

DB_PATH = "football_predictions.db"

def detailed_report():
    """Generate detailed predictions report"""
    
    if not os.path.exists(DB_PATH):
        print(f"❌ Database not found: {DB_PATH}")
        return
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    print("=" * 80)
    print("🎯 DETAILED PREDICTIONS REPORT")
    print("=" * 80)
    
    # Get all predictions with their match details
    cursor.execute("""
        SELECT 
            p.id,
            p.match_id,
            m.match_date,
            l.name as league,
            t1.name as home_team,
            t2.name as away_team,
            m.home_goals,
            m.away_goals,
            m.status,
            p.predicted_result,
            p.confidence,
            p.actual_result,
            p.is_correct,
            p.created_at
        FROM predictions p
        JOIN matches m ON p.match_id = m.id
        LEFT JOIN teams t1 ON m.home_team_id = t1.id
        LEFT JOIN teams t2 ON m.away_team_id = t2.id
        LEFT JOIN leagues l ON m.league_id = l.id
        ORDER BY m.match_date DESC
    """)
    
    predictions = cursor.fetchall()
    
    if not predictions:
        print("\n⚠️  No predictions found in database")
        conn.close()
        return
    
    print(f"\nTotal Predictions: {len(predictions)}\n")
    
    finished_count = 0
    upcoming_count = 0
    correct_count = 0
    incorrect_count = 0
    
    for pred in predictions:
        (pred_id, match_id, match_date, league, home, away, 
         home_goals, away_goals, status, predicted, confidence, 
         actual, is_correct, created_at) = pred
        
        print(f"{'='*80}")
        print(f"Prediction ID: {pred_id} | Match ID: {match_id}")
        print(f"League: {league}")
        print(f"Match: {home} vs {away}")
        print(f"Date: {match_date}")
        print(f"Status: {status}")
        print(f"Predicted: {predicted} (Confidence: {confidence:.1%})")
        
        if status == 'FT' and home_goals is not None:
            finished_count += 1
            print(f"Score: {home} {home_goals}-{away_goals} {away}")
            
            # Determine actual result
            if home_goals > away_goals:
                match_result = 'H'
            elif home_goals < away_goals:
                match_result = 'A'
            else:
                match_result = 'D'
            
            if actual:
                print(f"Actual Result: {actual}")
                if is_correct:
                    print(f"✅ CORRECT")
                    correct_count += 1
                else:
                    print(f"❌ INCORRECT")
                    incorrect_count += 1
            else:
                print(f"⚠️  Actual result NOT SET (should be: {match_result})")
        else:
            upcoming_count += 1
            print(f"⏳ Match not played yet or score not available")
        
        print(f"Prediction created: {created_at}")
        print()
    
    print("=" * 80)
    print("📊 SUMMARY")
    print("=" * 80)
    print(f"Total Predictions: {len(predictions)}")
    print(f"Finished Matches: {finished_count}")
    print(f"Upcoming Matches: {upcoming_count}")
    if finished_count > 0:
        print(f"Evaluated: {correct_count + incorrect_count}")
        print(f"✅ Correct: {correct_count}")
        print(f"❌ Incorrect: {incorrect_count}")
        if correct_count + incorrect_count > 0:
            accuracy = (correct_count / (correct_count + incorrect_count)) * 100
            print(f"Accuracy: {accuracy:.1f}%")
    print("=" * 80)
    
    conn.close()

if __name__ == "__main__":
    detailed_report()
