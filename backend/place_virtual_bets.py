"""
Place Virtual Bets for the 10 Value Opportunities

This script places virtual bets for all the opportunities
identified by the scanner, simulating real bet placement.
"""

import sys
import os
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.models.database import SessionLocal, Prediction
from src.services.performance_service import record_bet
from colorama import Fore, Style, init

init(autoreset=True)

print(f"\n{Fore.CYAN}{'=' * 80}")
print(f"{Fore.CYAN}{'PLACING VIRTUAL BETS - 10 VALUE OPPORTUNITIES'.center(80)}")
print(f"{Fore.CYAN}{'=' * 80}{Style.RESET_ALL}\n")

# The 10 opportunities from our scan (using prediction IDs from simulation)
opportunities = [
    {"prediction_id": 34, "market": "H", "market_name": "Home Win", "kelly": 21.9, "odds": 1.52, "ai_prob": 0.733, "ev": 1.114, "edge": 11.4, "value": "MEDIUM"},
    {"prediction_id": 33, "market": "A", "market_name": "Away Win", "kelly": 13.5, "odds": 1.84, "ai_prob": 0.605, "ev": 1.113, "edge": 11.3, "value": "MEDIUM"},
    {"prediction_id": 32, "market": "A", "market_name": "Away Win", "kelly": 5.2, "odds": 3.17, "ai_prob": 0.351, "ev": 1.113, "edge": 11.3, "value": "MEDIUM"},
    {"prediction_id": 31, "market": "H", "market_name": "Home Win", "kelly": 7.0, "odds": 2.61, "ai_prob": 0.426, "ev": 1.113, "edge": 11.3, "value": "MEDIUM"},
    {"prediction_id": 30, "market": "A", "market_name": "Away Win", "kelly": 2.3, "odds": 5.81, "ai_prob": 0.191, "ev": 1.112, "edge": 11.2, "value": "MEDIUM"},
    {"prediction_id": 29, "market": "H", "market_name": "Home Win", "kelly": 5.7, "odds": 2.95, "ai_prob": 0.377, "ev": 1.112, "edge": 11.2, "value": "MEDIUM"},
    {"prediction_id": 28, "market": "A", "market_name": "Away Win", "kelly": 6.7, "odds": 2.68, "ai_prob": 0.415, "ev": 1.112, "edge": 11.2, "value": "MEDIUM"},
    {"prediction_id": 27, "market": "D", "market_name": "Draw", "kelly": 5.4, "odds": 3.09, "ai_prob": 0.360, "ev": 1.112, "edge": 11.2, "value": "MEDIUM"},
    {"prediction_id": 26, "market": "A", "market_name": "Away Win", "kelly": 3.3, "odds": 4.41, "ai_prob": 0.252, "ev": 1.111, "edge": 11.1, "value": "MEDIUM"},
    {"prediction_id": 25, "market": "A", "market_name": "Away Win", "kelly": 3.4, "odds": 4.26, "ai_prob": 0.261, "ev": 1.111, "edge": 11.1, "value": "MEDIUM"},
]

db = SessionLocal()
bankroll = 1000.0  # Starting bankroll

print(f"{Fore.YELLOW}💼 Initial Bankroll: ${bankroll:,.2f}{Style.RESET_ALL}\n")

successful_bets = 0
total_stake = 0

for idx, opp in enumerate(opportunities, 1):
    print(f"{Fore.CYAN}[{idx}/10]{Style.RESET_ALL} Placing bet on prediction #{opp['prediction_id']}...")
    
    try:
        bet = record_bet(
            db=db,
            prediction_id=opp['prediction_id'],
            market=opp['market'],
            market_name=opp['market_name'],
            bankroll=bankroll,
            kelly_percent=opp['kelly'],
            odds=opp['odds'],
            ai_probability=opp['ai_prob'],
            expected_value=opp['ev'],
            edge_percentage=opp['edge'],
            value_level=opp['value'],
            is_estimated_odds=True,
            notes=f"Value opportunity from scan - {opp['value']} value ({opp['edge']:+.1f}% edge)"
        )
        
        stake = bet.stake_amount
        total_stake += stake
        
        print(f"   ✅ {Fore.GREEN}Bet Placed:{Style.RESET_ALL}")
        print(f"      Market: {opp['market_name']} ({opp['market']})")
        print(f"      Stake: ${stake:.2f} ({opp['kelly']:.1f}% Kelly)")
        print(f"      Odds: {opp['odds']:.2f}")
        print(f"      Expected Value: {opp['ev']:.3f}x ({opp['edge']:+.1f}%)")
        print(f"      {Fore.CYAN}Value Level: {opp['value']}{Style.RESET_ALL}\n")
        
        successful_bets += 1
        
    except Exception as e:
        print(f"   {Fore.RED}❌ Error: {str(e)}{Style.RESET_ALL}\n")

db.close()

print(f"{Fore.CYAN}{'=' * 80}{Style.RESET_ALL}")
print(f"{Fore.GREEN}✅ Virtual Bets Placement Complete!{Style.RESET_ALL}\n")

print(f"{Fore.YELLOW}📊 Summary:{Style.RESET_ALL}")
print(f"   Bets Placed: {successful_bets}/10")
print(f"   Total Stake: ${total_stake:.2f}")
print(f"   Remaining Bankroll: ${bankroll - total_stake:.2f}")
print(f"   Average Kelly%: {sum(o['kelly'] for o in opportunities) / len(opportunities):.1f}%\n")

print(f"{Fore.MAGENTA}🌐 View Dashboard:{Style.RESET_ALL}")
print(f"   http://localhost:5175/bet-tracker\n")

print(f"{Fore.CYAN}{'=' * 80}{Style.RESET_ALL}\n")
