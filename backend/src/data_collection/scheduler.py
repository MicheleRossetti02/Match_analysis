"""
Automated Data Collection Scheduler
Runs periodic tasks to update football data
"""
import sys
import os
from datetime import datetime, timedelta
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from data_collector import DataCollector
from config import settings


class DataScheduler:
    """Schedules automatic data collection tasks"""
    
    def __init__(self):
        self.scheduler = BlockingScheduler()
        self.collector = None
    
    def daily_update(self):
        """Daily task: Update recent matches and upcoming fixtures"""
        print(f"\n{'='*60}")
        print(f"🌅 DAILY UPDATE - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*60}\n")
        
        self.collector = DataCollector()
        
        try:
            # Collect leagues for current season
            leagues = self.collector.collect_leagues(season=2024)
            
            # For each league
            for league in leagues:
                print(f"\n📊 Updating {league.name}...")
                
                # Update teams (in case of transfers)
                self.collector.collect_teams(league)
                
                # Get matches from last 7 days (in case we missed any)
                end_date = datetime.now()
                start_date = end_date - timedelta(days=7)
                
                # Finished matches
                self.collector.collect_matches(
                    league=league,
                    from_date=start_date.strftime("%Y-%m-%d"),
                    to_date=end_date.strftime("%Y-%m-%d"),
                    status="FT"
                )
                
                # Upcoming matches (next 14 days)
                future_date = end_date + timedelta(days=14)
                self.collector.collect_matches(
                    league=league,
                    from_date=end_date.strftime("%Y-%m-%d"),
                    to_date=future_date.strftime("%Y-%m-%d"),
                    status="NS"
                )
            
            self.collector.print_stats()
            
        except Exception as e:
            print(f"❌ Error in daily update: {e}")
        finally:
            if self.collector:
                self.collector.close()
    
    def weekly_statistics_update(self):
        """Weekly task: Collect detailed statistics for recent matches"""
        print(f"\n{'='*60}")
        print(f"📈 WEEKLY STATISTICS UPDATE - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*60}\n")
        
        self.collector = DataCollector()
        
        try:
            from src.models.database import Match, MatchStatistics
            
            # Get finished matches from last 7 days without statistics
            end_date = datetime.now()
            start_date = end_date - timedelta(days=7)
            
            matches = (
                self.collector.db.query(Match)
                .outerjoin(MatchStatistics)
                .filter(Match.status == "FT")
                .filter(Match.match_date >= start_date)
                .filter(Match.match_date <= end_date)
                .filter(MatchStatistics.id.is_(None))
                .limit(50)  # Limit to 50 to avoid API quota issues
                .all()
            )
            
            print(f"Found {len(matches)} matches needing statistics")
            
            for match in matches:
                self.collector.collect_match_statistics(match)
            
            self.collector.print_stats()
            
        except Exception as e:
            print(f"❌ Error in weekly statistics update: {e}")
        finally:
            if self.collector:
                self.collector.close()
    
    def start(self):
        """Start the scheduler"""
        print("🚀 Starting Data Collection Scheduler")
        print("="*60)
        
        # Daily update at 3:00 AM
        self.scheduler.add_job(
            self.daily_update,
            CronTrigger(hour=3, minute=0),
            id='daily_update',
            name='Daily Match Data Update',
            replace_existing=True
        )
        print("✅ Scheduled: Daily update at 3:00 AM")
        
        # Weekly statistics update on Sunday at 2:00 AM
        self.scheduler.add_job(
            self.weekly_statistics_update,
            CronTrigger(day_of_week='sun', hour=2, minute=0),
            id='weekly_statistics',
            name='Weekly Statistics Update',
            replace_existing=True
        )
        print("✅ Scheduled: Weekly statistics update on Sunday at 2:00 AM")
        
        print("="*60)
        print("📅 Scheduler is running. Press Ctrl+C to stop.")
        print("="*60 + "\n")
        
        try:
            self.scheduler.start()
        except (KeyboardInterrupt, SystemExit):
            print("\n⚠️  Scheduler stopped by user")


def main():
    """Main function"""
    scheduler = DataScheduler()
    scheduler.start()


if __name__ == "__main__":
    main()
