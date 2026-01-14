"""
Check Database Status
Quick script to check matches and predictions status
"""
import sqlite3
import os
from datetime import datetime, timedelta

DB_PATH = "football_predictions.db"

def check_status():
    """Check database status"""
    
    if not os.path.exists(DB_PATH):
        print(f"❌ Database not found: {DB_PATH}")
        return
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    print("=" * 60)
    print("📊 DATABASE STATUS REPORT")
    print("=" * 60)
    
    # Count total matches
    cursor.execute("SELECT COUNT(*) FROM matches")
    total_matches = cursor.fetchone()[0]
    print(f"\n📋 Total Matches: {total_matches}")
    
    # Count finished matches
    cursor.execute("SELECT COUNT(*) FROM matches WHERE status = 'FT' AND home_goals IS NOT NULL")
    finished_matches = cursor.fetchone()[0]
    print(f"✅ Finished Matches: {finished_matches}")
    
    # Count upcoming matches
    cursor.execute("SELECT COUNT(*) FROM matches WHERE status NOT IN ('FT', 'AET', 'PEN')")
    upcoming_matches = cursor.fetchone()[0]
    print(f"⏳ Upcoming Matches: {upcoming_matches}")
    
    # Count total predictions
    cursor.execute("SELECT COUNT(*) FROM predictions")
    total_predictions = cursor.fetchone()[0]
    print(f"\n🎯 Total Predictions: {total_predictions}")
    
    # Count predictions with actual results
    cursor.execute("SELECT COUNT(*) FROM predictions WHERE actual_result IS NOT NULL")
    predictions_with_results = cursor.fetchone()[0]
    print(f"✅ Predictions with Results: {predictions_with_results}")
    
    # Count predictions without actual results but match is finished
    cursor.execute("""
        SELECT COUNT(*) 
        FROM predictions p
        JOIN matches m ON p.match_id = m.id
        WHERE m.status = 'FT' 
        AND m.home_goals IS NOT NULL 
        AND p.actual_result IS NULL
    """)
    predictions_needing_update = cursor.fetchone()[0]
    print(f"⚠️  Predictions Needing Update: {predictions_needing_update}")
    
    # Recent finished matches
    print(f"\n📅 Recent Finished Matches (Last 7 days):")
    cursor.execute("""
        SELECT m.id, m.match_date, t1.name, m.home_goals, m.away_goals, t2.name, m.status
        FROM matches m
        LEFT JOIN teams t1 ON m.home_team_id = t1.id
        LEFT JOIN teams t2 ON m.away_team_id = t2.id
        WHERE m.status = 'FT' 
        AND m.home_goals IS NOT NULL
        AND m.match_date >= datetime('now', '-7 days')
        ORDER BY m.match_date DESC
        LIMIT 10
    """)
    
    recent_matches = cursor.fetchall()
    if recent_matches:
        for match in recent_matches:
            match_id, match_date, home, home_goals, away_goals, away, status = match
            print(f"  {match_date}: {home} {home_goals}-{away_goals} {away}")
            
            # Check if this match has a prediction
            cursor.execute("SELECT id, predicted_result, actual_result FROM predictions WHERE match_id = ?", (match_id,))
            pred = cursor.fetchone()
            if pred:
                pred_id, predicted, actual = pred
                print(f"    Prediction: {predicted} | Actual: {actual or 'NOT SET'}")
            else:
                print(f"    ⚠️  No prediction found")
    else:
        print("  No recent finished matches found")
    
    # Upcoming matches with predictions
    print(f"\n📅 Upcoming Matches with Predictions:")
    cursor.execute("""
        SELECT m.id, m.match_date, t1.name, t2.name, p.predicted_result, p.confidence
        FROM predictions p
        JOIN matches m ON p.match_id = m.id
        LEFT JOIN teams t1 ON m.home_team_id = t1.id
        LEFT JOIN teams t2 ON m.away_team_id = t2.id
        WHERE m.status NOT IN ('FT', 'AET', 'PEN')
        AND m.match_date >= datetime('now')
        ORDER BY m.match_date ASC
        LIMIT 10
    """)
    
    upcoming_with_predictions = cursor.fetchall()
    if upcoming_with_predictions:
        for match in upcoming_with_predictions:
            match_id, match_date, home, away, predicted, confidence = match
            print(f"  {match_date}: {home} vs {away} - Prediction: {predicted} ({confidence:.1%})")
    else:
        print("  No upcoming matches with predictions found")
    
    print("\n" + "=" * 60)
    
    conn.close()

if __name__ == "__main__":
    check_status()
