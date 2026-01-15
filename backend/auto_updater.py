"""
Automated Bet Result Updater - Background Worker

Automatically monitors pending bets and updates results when matches finish.
Runs every 60 minutes to check for completed matches and settle bets.

Features:
- Automatic bet settlement (WON/LOST)
- P&L calculation and bankroll tracking
- Real-time ROI and statistics updates
- Comprehensive logging system
"""

import sys
import os
import time
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
import logging
from colorama import Fore, Style, init

init(autoreset=True)

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.models.database import SessionLocal, BetHistory, Prediction, Match
from src.services.performance_service import update_bet_results, get_performance_stats

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bet_updater.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('BetUpdater')


class BetResultUpdater:
    """Background worker for automated bet result updates"""
    
    def __init__(self, update_interval_minutes=60):
        self.update_interval = update_interval_minutes
        self.scheduler = BackgroundScheduler()
        self.is_running = False
        
    def check_and_update_bets(self):
        """Main update logic - checks pending bets and settles finished matches"""
        
        logger.info(f"{Fore.CYAN}{'=' * 80}{Style.RESET_ALL}")
        logger.info(f"{Fore.CYAN}BET RESULT UPDATE CYCLE - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{Style.RESET_ALL}")
        logger.info(f"{Fore.CYAN}{'=' * 80}{Style.RESET_ALL}")
        
        db = SessionLocal()
        
        try:
            # Get pending bets count
            pending_bets = (
                db.query(BetHistory)
                .filter(BetHistory.status == 'PENDING')
                .all()
            )
            
            pending_count = len(pending_bets)
            logger.info(f"{Fore.YELLOW}📊 Found {pending_count} pending bets{Style.RESET_ALL}")
            
            if pending_count == 0:
                logger.info(f"{Fore.GREEN}✓ No pending bets to process{Style.RESET_ALL}")
                db.close()
                return
            
            # Check match statuses
            logger.info(f"{Fore.YELLOW}🔍 Checking match statuses...{Style.RESET_ALL}")
            
            finished_matches = 0
            pending_matches = 0
            
            for bet in pending_bets:
                prediction = bet.prediction
                match = prediction.match
                
                if match.status == 'FT':
                    finished_matches += 1
                    logger.info(f"   Match #{match.id} ({match.home_team.name} vs {match.away_team.name}): FINISHED")
                else:
                    pending_matches += 1
                    logger.info(f"   Match #{match.id} ({match.home_team.name} vs {match.away_team.name}): {match.status}")
            
            logger.info(f"\n{Fore.YELLOW}📈 Match Status Summary:{Style.RESET_ALL}")
            logger.info(f"   Finished (FT): {finished_matches}")
            logger.info(f"   Still Pending: {pending_matches}")
            
            if finished_matches == 0:
                logger.info(f"\n{Fore.GREEN}✓ No finished matches to settle{Style.RESET_ALL}")
                db.close()
                return
            
            # Get stats before update
            stats_before = get_performance_stats(db)
            
            # Update bet results
            logger.info(f"\n{Fore.YELLOW}💰 Settling finished bets...{Style.RESET_ALL}")
            result = update_bet_results(db)
            
            # Log results
            logger.info(f"\n{Fore.CYAN}{'=' * 80}{Style.RESET_ALL}")
            logger.info(f"{Fore.GREEN}✅ UPDATE COMPLETE{Style.RESET_ALL}")
            logger.info(f"{Fore.CYAN}{'=' * 80}{Style.RESET_ALL}")
            
            logger.info(f"\n{Fore.YELLOW}📊 Settlement Summary:{Style.RESET_ALL}")
            logger.info(f"   Total Updated: {result['updated']}")
            logger.info(f"   {Fore.GREEN}Won: {result['won']}{Style.RESET_ALL}")
            logger.info(f"   {Fore.RED}Lost: {result['lost']}{Style.RESET_ALL}")
            
            # Get stats after update
            stats_after = get_performance_stats(db)
            
            # Log performance changes
            logger.info(f"\n{Fore.YELLOW}📈 Performance Update:{Style.RESET_ALL}")
            
            roi_change = stats_after['roi_percent'] - stats_before.get('roi_percent', 0)
            pnl_change = stats_after['total_pnl'] - stats_before.get('total_pnl', 0)
            
            logger.info(f"   Total Bets: {stats_before.get('total_bets', 0)} → {stats_after['total_bets']}")
            logger.info(f"   Win Rate: {stats_before.get('win_rate', 0):.2f}% → {stats_after['win_rate']:.2f}%")
            
            roi_color = Fore.GREEN if roi_change >= 0 else Fore.RED
            logger.info(f"   ROI: {stats_before.get('roi_percent', 0):.2f}% → {roi_color}{stats_after['roi_percent']:.2f}% ({roi_change:+.2f}%){Style.RESET_ALL}")
            
            pnl_color = Fore.GREEN if pnl_change >= 0 else Fore.RED
            logger.info(f"   Total P&L: ${stats_before.get('total_pnl', 0):.2f} → {pnl_color}${stats_after['total_pnl']:.2f} ({pnl_change:+.2f}){Style.RESET_ALL}")
            
            # Log individual bet results
            if result['updated'] > 0:
                logger.info(f"\n{Fore.YELLOW}🎯 Individual Bet Results:{Style.RESET_ALL}")
                
                # Get recently settled bets
                settled_bets = (
                    db.query(BetHistory)
                    .filter(BetHistory.status.in_(['WON', 'LOST']))
                    .filter(BetHistory.settled_at.isnot(None))
                    .order_by(BetHistory.settled_at.desc())
                    .limit(result['updated'])
                    .all()
                )
                
                for bet in settled_bets:
                    prediction = bet.prediction
                    match = prediction.match
                    
                    if bet.is_winner:
                        status_color = Fore.GREEN
                        status_icon = "✅ WON"
                    else:
                        status_color = Fore.RED
                        status_icon = "❌ LOST"
                    
                    logger.info(f"\n   {status_color}{status_icon}{Style.RESET_ALL}")
                    logger.info(f"   Match: {match.home_team.name} {match.home_goals}-{match.away_goals} {match.away_team.name}")
                    logger.info(f"   Market: {bet.market_name} ({bet.market})")
                    logger.info(f"   Actual Result: {bet.actual_result}")
                    logger.info(f"   Stake: ${bet.stake_amount:.2f} @ {bet.odds:.2f}")
                    
                    pnl_color = Fore.GREEN if bet.pnl >= 0 else Fore.RED
                    logger.info(f"   P&L: {pnl_color}{bet.pnl:+.2f}${Style.RESET_ALL} ({bet.roi_percent:+.1f}% ROI)")
                    logger.info(f"   Bankroll: ${bet.bankroll_at_bet:.2f} → ${bet.bankroll_after:.2f}")
            
            logger.info(f"\n{Fore.CYAN}{'=' * 80}{Style.RESET_ALL}\n")
            
        except Exception as e:
            logger.error(f"{Fore.RED}❌ Error during update: {str(e)}{Style.RESET_ALL}")
            db.rollback()
            raise
        
        finally:
            db.close()
    
    def start(self):
        """Start the background scheduler"""
        
        print(f"\n{Fore.CYAN}{'=' * 80}")
        print(f"{Fore.CYAN}{'AUTOMATED BET RESULT UPDATER'.center(80)}")
        print(f"{Fore.CYAN}{'=' * 80}{Style.RESET_ALL}\n")
        
        print(f"{Fore.YELLOW}⚙️  Configuration:{Style.RESET_ALL}")
        print(f"   Update Interval: {self.update_interval} minutes")
        print(f"   Log File: bet_updater.log")
        print(f"   Status: Starting...\n")
        
        # Add job to scheduler
        self.scheduler.add_job(
            func=self.check_and_update_bets,
            trigger=IntervalTrigger(minutes=self.update_interval),
            id='bet_updater',
            name='Bet Result Update',
            replace_existing=True
        )
        
        # Start scheduler
        self.scheduler.start()
        self.is_running = True
        
        print(f"{Fore.GREEN}✅ Background worker started successfully!{Style.RESET_ALL}")
        print(f"{Fore.GREEN}   Next update: {datetime.now().replace(second=0, microsecond=0).replace(minute=(datetime.now().minute + self.update_interval) % 60).strftime('%H:%M:%S')}{Style.RESET_ALL}\n")
        
        # Run first check immediately
        print(f"{Fore.YELLOW}🚀 Running initial check...{Style.RESET_ALL}\n")
        self.check_and_update_bets()
        
        print(f"\n{Fore.CYAN}{'=' * 80}")
        print(f"{Fore.CYAN}{'WORKER ACTIVE - Press Ctrl+C to stop'.center(80)}")
        print(f"{Fore.CYAN}{'=' * 80}{Style.RESET_ALL}\n")
    
    def stop(self):
        """Stop the background scheduler"""
        if self.is_running:
            self.scheduler.shutdown()
            self.is_running = False
            logger.info(f"{Fore.YELLOW}⏹  Background worker stopped{Style.RESET_ALL}")


def main():
    """Main entry point"""
    
    # Create updater instance (update every 60 minutes)
    updater = BetResultUpdater(update_interval_minutes=60)
    
    try:
        # Start the worker
        updater.start()
        
        # Keep the script running
        while True:
            time.sleep(60)
            
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}⏹  Shutting down...{Style.RESET_ALL}")
        updater.stop()
        print(f"{Fore.GREEN}✅ Worker stopped successfully{Style.RESET_ALL}\n")
    
    except Exception as e:
        logger.error(f"{Fore.RED}❌ Fatal error: {str(e)}{Style.RESET_ALL}")
        updater.stop()
        raise


if __name__ == "__main__":
    main()
