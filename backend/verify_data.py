#!/usr/bin/env python3
"""
Verify collected data in the database
"""
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.models.database import SessionLocal, League, Team, Match, MatchStatistics
from datetime import datetime, timedelta


def print_section(title):
    """Print formatted section header"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")


def verify_database():
    """Check what data exists in the database"""
    db = SessionLocal()
    
    try:
        print_section("📊 DATABASE VERIFICATION")
        
        # Count leagues
        leagues_count = db.query(League).count()
        print(f"✅ Leagues: {leagues_count}")
        
        if leagues_count > 0:
            leagues = db.query(League).all()
            for league in leagues:
                print(f"   - {league.name} ({league.country}) - Season {league.season}")
        
        # Count teams
        teams_count = db.query(Team).count()
        print(f"\n✅ Teams: {teams_count}")
        
        if teams_count > 0:
            # Show teams per league
            for league in leagues:
                league_teams = db.query(Team).filter(Team.league_id == league.id).count()
                print(f"   - {league.name}: {league_teams} teams")
        
        # Count matches
        matches_count = db.query(Match).count()
        print(f"\n✅ Matches: {matches_count}")
        
        if matches_count > 0:
            # Show matches per league
            for league in leagues:
                league_matches = db.query(Match).filter(Match.league_id == league.id).count()
                finished = db.query(Match).filter(
                    Match.league_id == league.id,
                    Match.status == "FT"
                ).count()
                upcoming = db.query(Match).filter(
                    Match.league_id == league.id,
                    Match.status == "NS"
                ).count()
                print(f"   - {league.name}: {league_matches} total ({finished} finished, {upcoming} upcoming)")
            
            # Recent matches
            print("\n📅 Recent Matches:")
            recent = (
                db.query(Match)
                .order_by(Match.match_date.desc())
                .limit(5)
                .all()
            )
            for match in recent:
                home = db.query(Team).filter(Team.id == match.home_team_id).first()
                away = db.query(Team).filter(Team.id == match.away_team_id).first()
                score = f"{match.home_goals}-{match.away_goals}" if match.home_goals is not None else "TBD"
                print(f"   - {home.name if home else 'Unknown'} vs {away.name if away else 'Unknown'}: {score}")
                print(f"     Date: {match.match_date.strftime('%Y-%m-%d %H:%M')} | Status: {match.status}")
            
            # Upcoming matches
            print("\n🔮 Upcoming Matches:")
            upcoming_matches = (
                db.query(Match)
                .filter(Match.status == "NS")
                .filter(Match.match_date >= datetime.utcnow())
                .order_by(Match.match_date)
                .limit(5)
                .all()
            )
            
            if upcoming_matches:
                for match in upcoming_matches:
                    home = db.query(Team).filter(Team.id == match.home_team_id).first()
                    away = db.query(Team).filter(Team.id == match.away_team_id).first()
                    print(f"   - {home.name if home else 'Unknown'} vs {away.name if away else 'Unknown'}")
                    print(f"     Date: {match.match_date.strftime('%Y-%m-%d %H:%M')}")
            else:
                print("   No upcoming matches found")
        
        # Count statistics
        stats_count = db.query(MatchStatistics).count()
        print(f"\n✅ Match Statistics: {stats_count}")
        
        if stats_count > 0:
            # Sample statistics
            sample_stat = db.query(MatchStatistics).first()
            match = db.query(Match).filter(Match.id == sample_stat.match_id).first()
            if match:
                home = db.query(Team).filter(Team.id == match.home_team_id).first()
                away = db.query(Team).filter(Team.id == match.away_team_id).first()
                print(f"\n📊 Sample Statistics ({home.name if home else 'Unknown'} vs {away.name if away else 'Unknown'}):")
                print(f"   Possession: {sample_stat.home_possession}% - {sample_stat.away_possession}%")
                print(f"   Shots: {sample_stat.home_shots_total} - {sample_stat.away_shots_total}")
                print(f"   Corners: {sample_stat.home_corners} - {sample_stat.away_corners}")
        
        print_section("✅ VERIFICATION COMPLETE")
        
        # Summary
        if leagues_count == 0:
            print("⚠️  No data found. Run data collection:")
            print("   python run_data_collection.py --quick\n")
        elif matches_count == 0:
            print("⚠️  Leagues and teams found, but no matches.")
            print("   This might be normal if no matches in the selected date range.\n")
        else:
            print(f"✨ Database contains {matches_count} matches across {leagues_count} leagues!")
            print(f"   Ready for ML model training!\n")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    verify_database()
