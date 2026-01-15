"""
Kelly Criterion Simulation & Test Script

This script creates realistic betting scenarios to test the Kelly Criterion
and Value Betting Analysis system. It simulates three different scenarios:
- Scenario A: HIGH VALUE (AI edge over bookmaker)
- Scenario B: NO VALUE (bookmaker edge over AI)
- Scenario C: FAIR VALUE (aligned probabilities)

The script updates predictions in the database with simulated odds and
calculates Kelly Criterion, Expected Value, and value levels.
"""

import sys
import os
from datetime import datetime
from tabulate import tabulate
from colorama import Fore, Style, init

# Initialize colorama for colored output
init(autoreset=True)

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.models.database import SessionLocal, Prediction, Match
from src.services.betting_analysis_service import (
    calculate_kelly_criterion,
    calculate_value_level,
    estimate_bookmaker_odds,
    analyze_bet_value
)


def get_test_predictions(db, limit=3):
    """
    Get recent predictions with match data for testing.
    
    Args:
        db: Database session
        limit: Number of predictions to retrieve
    
    Returns:
        List of prediction objects with match data
    """
    predictions = (
        db.query(Prediction)
        .join(Match)
        .filter(Prediction.prob_home_win.isnot(None))
        .filter(Prediction.prob_draw.isnot(None))
        .filter(Prediction.prob_away_win.isnot(None))
        .order_by(Prediction.created_at.desc())
        .limit(limit)
        .all()
    )
    
    return predictions


def create_scenario_a_high_value(prediction):
    """
    Scenario A: HIGH VALUE
    AI predicts 60% chance, Bookmaker offers 2.50 odds
    This represents significant value (EV = 1.50, 50% edge)
    """
    # Use home win as example
    ai_prob = 0.60
    bookmaker_odds = 2.50
    
    # Update prediction
    prediction.prob_home_win = ai_prob
    
    # Calculate analysis
    analysis = analyze_bet_value(ai_prob, bookmaker_odds, market_name="Home Win")
    
    # Update prediction with analysis
    prediction.kelly_percentage = analysis['kelly_percentage']
    prediction.kelly_raw = analysis['kelly_raw']
    prediction.value_level = analysis['value_level']
    prediction.expected_value = analysis['ev']
    prediction.edge_percentage = analysis['edge_percentage']
    prediction.estimated_odds = {
        "1": bookmaker_odds,
        "X": estimate_bookmaker_odds(prediction.prob_draw or 0.25),
        "2": estimate_bookmaker_odds(prediction.prob_away_win or 0.15)
    }
    prediction.has_value_analysis = True
    prediction.is_estimated_odds = True
    
    return {
        'scenario': 'A - HIGH VALUE',
        'ai_prob': ai_prob,
        'bookmaker_odds': bookmaker_odds,
        'analysis': analysis,
        'match_id': prediction.match_id
    }


def create_scenario_b_no_value(prediction):
    """
    Scenario B: NO VALUE
    AI predicts 40% chance, Bookmaker offers 1.80 odds
    This represents negative value (EV = 0.72, -28% edge)
    """
    # Use home win as example
    ai_prob = 0.40
    bookmaker_odds = 1.80
    
    # Update prediction
    prediction.prob_home_win = ai_prob
    
    # Calculate analysis
    analysis = analyze_bet_value(ai_prob, bookmaker_odds, market_name="Home Win")
    
    # Update prediction with analysis
    prediction.kelly_percentage = analysis['kelly_percentage']
    prediction.kelly_raw = analysis['kelly_raw']
    prediction.value_level = analysis['value_level']
    prediction.expected_value = analysis['ev']
    prediction.edge_percentage = analysis['edge_percentage']
    prediction.estimated_odds = {
        "1": bookmaker_odds,
        "X": estimate_bookmaker_odds(prediction.prob_draw or 0.30),
        "2": estimate_bookmaker_odds(prediction.prob_away_win or 0.30)
    }
    prediction.has_value_analysis = True
    prediction.is_estimated_odds = True
    
    return {
        'scenario': 'B - NO VALUE',
        'ai_prob': ai_prob,
        'bookmaker_odds': bookmaker_odds,
        'analysis': analysis,
        'match_id': prediction.match_id
    }


def create_scenario_c_fair_value(prediction):
    """
    Scenario C: FAIR VALUE
    AI predicts 50% chance, Bookmaker offers 2.00 odds (perfectly fair)
    This represents zero edge (EV = 1.00, 0% edge)
    """
    # Use home win as example
    ai_prob = 0.50
    bookmaker_odds = 2.00
    
    # Update prediction
    prediction.prob_home_win = ai_prob
    
    # Calculate analysis
    analysis = analyze_bet_value(ai_prob, bookmaker_odds, market_name="Home Win")
    
    # Update prediction with analysis
    prediction.kelly_percentage = analysis['kelly_percentage']
    prediction.kelly_raw = analysis['kelly_raw']
    prediction.value_level = analysis['value_level']
    prediction.expected_value = analysis['ev']
    prediction.edge_percentage = analysis['edge_percentage']
    prediction.estimated_odds = {
        "1": bookmaker_odds,
        "X": estimate_bookmaker_odds(prediction.prob_draw or 0.25),
        "2": estimate_bookmaker_odds(prediction.prob_away_win or 0.25)
    }
    prediction.has_value_analysis = True
    prediction.is_estimated_odds = True
    
    return {
        'scenario': 'C - FAIR VALUE',
        'ai_prob': ai_prob,
        'bookmaker_odds': bookmaker_odds,
        'analysis': analysis,
        'match_id': prediction.match_id
    }


def print_scenario_analysis(scenario_data):
    """
    Print detailed analysis for a scenario with color coding.
    
    Args:
        scenario_data: Dictionary with scenario information
    """
    analysis = scenario_data['analysis']
    
    # Header
    print(f"\n{Fore.CYAN}{'=' * 80}")
    print(f"{Fore.CYAN}{scenario_data['scenario'].center(80)}")
    print(f"{Fore.CYAN}{'=' * 80}{Style.RESET_ALL}")
    
    print(f"\n{Fore.YELLOW}Match ID:{Style.RESET_ALL} {scenario_data['match_id']}")
    
    # Input data
    print(f"\n{Fore.MAGENTA}📊 Input Data:{Style.RESET_ALL}")
    input_table = [
        ["AI Probability", f"{scenario_data['ai_prob'] * 100:.1f}%"],
        ["Bookmaker Odds", f"{scenario_data['bookmaker_odds']:.2f}"],
        ["Implied Probability", f"{analysis['implied_prob'] * 100:.1f}%"]
    ]
    print(tabulate(input_table, tablefmt="simple"))
    
    # Calculations
    print(f"\n{Fore.MAGENTA}🧮 Calculations:{Style.RESET_ALL}")
    
    # Expected Value
    ev_color = Fore.GREEN if analysis['ev'] >= 1.15 else Fore.YELLOW if analysis['ev'] >= 1.05 else Fore.RED
    ev_text = f"{ev_color}{analysis['ev']:.3f}x{Style.RESET_ALL}"
    edge_text = f"{ev_color}{analysis['edge_percentage']:+.1f}%{Style.RESET_ALL}"
    
    # Kelly Criterion
    kelly_color = Fore.GREEN if analysis['kelly_percentage'] >= 15 else Fore.YELLOW if analysis['kelly_percentage'] >= 8 else Fore.RED
    kelly_text = f"{kelly_color}{analysis['kelly_percentage']:.1f}%{Style.RESET_ALL}"
    
    # Value Level
    level_color = Fore.GREEN if analysis['value_level'] == 'HIGH' else Fore.YELLOW if analysis['value_level'] == 'MEDIUM' else Fore.RED
    level_text = f"{level_color}{analysis['value_level']}{Style.RESET_ALL}"
    
    calc_table = [
        ["Expected Value (EV)", ev_text],
        ["Edge Percentage", edge_text],
        ["Kelly Criterion", kelly_text],
        ["Kelly Raw (uncapped)", f"{analysis['kelly_raw']:.4f}"],
        ["Value Level", level_text],
        ["Risk Level", analysis['risk_level']],
        ["Should Bet?", f"{Fore.GREEN}YES{Style.RESET_ALL}" if analysis['should_bet'] else f"{Fore.RED}NO{Style.RESET_ALL}"]
    ]
    print(tabulate(calc_table, tablefmt="simple"))
    
    # Recommendation
    print(f"\n{Fore.MAGENTA}💡 Recommendation:{Style.RESET_ALL}")
    print(f"   {analysis['recommendation']}")
    
    # Formula breakdown
    print(f"\n{Fore.MAGENTA}📐 Kelly Formula Breakdown:{Style.RESET_ALL}")
    b = scenario_data['bookmaker_odds'] - 1
    p = scenario_data['ai_prob']
    q = 1 - p
    print(f"   f* = (bp - q) / b")
    print(f"   f* = ({b:.2f} × {p:.2f} - {q:.2f}) / {b:.2f}")
    print(f"   f* = ({b * p:.3f} - {q:.2f}) / {b:.2f}")
    print(f"   f* = {analysis['kelly_raw']:.4f} = {analysis['kelly_raw'] * 100:.1f}%")
    if analysis['kelly_raw'] > 0.25:
        print(f"   {Fore.YELLOW}⚠️  Capped at 25% (Fractional Kelly for safety){Style.RESET_ALL}")


def print_summary_table(all_scenarios):
    """
    Print a summary table comparing all scenarios.
    
    Args:
        all_scenarios: List of scenario data dictionaries
    """
    print(f"\n\n{Fore.CYAN}{'=' * 100}")
    print(f"{Fore.CYAN}{'SUMMARY TABLE'.center(100)}")
    print(f"{Fore.CYAN}{'=' * 100}{Style.RESET_ALL}\n")
    
    headers = ["Scenario", "Match ID", "AI Prob", "Odds", "EV", "Edge %", "Kelly %", "Value", "Bet?"]
    rows = []
    
    for scenario in all_scenarios:
        analysis = scenario['analysis']
        
        # Color-code the row
        ev_color = "green" if analysis['ev'] >= 1.15 else "yellow" if analysis['ev'] >= 1.05 else "red"
        
        row = [
            scenario['scenario'],
            scenario['match_id'],
            f"{scenario['ai_prob'] * 100:.0f}%",
            f"{scenario['bookmaker_odds']:.2f}",
            f"{analysis['ev']:.3f}",
            f"{analysis['edge_percentage']:+.1f}%",
            f"{analysis['kelly_percentage']:.1f}%",
            analysis['value_level'],
            "✓" if analysis['should_bet'] else "✗"
        ]
        rows.append(row)
    
    print(tabulate(rows, headers=headers, tablefmt="grid"))
    
    # Expected results verification
    print(f"\n{Fore.MAGENTA}✅ Expected Results Verification:{Style.RESET_ALL}")
    expectations = [
        ["Scenario A (High Value)", "EV > 1.15", "Kelly > 15%", "VALUE: HIGH", "Should bet"],
        ["Scenario B (No Value)", "EV < 1.05", "Kelly = 0%", "VALUE: NEUTRAL", "Should NOT bet"],
        ["Scenario C (Fair Value)", "EV ≈ 1.00", "Kelly = 0%", "VALUE: NEUTRAL", "Should NOT bet"]
    ]
    print(tabulate(expectations, headers=["Scenario", "EV", "Kelly", "Badge", "Decision"], tablefmt="simple"))


def main():
    """
    Main function to run the simulation.
    """
    print(f"\n{Fore.CYAN}{'=' * 80}")
    print(f"{Fore.CYAN}{'KELLY CRITERION SIMULATION & STRESS TEST'.center(80)}")
    print(f"{Fore.CYAN}{'=' * 80}{Style.RESET_ALL}\n")
    
    print(f"{Fore.YELLOW}🎯 Objective:{Style.RESET_ALL} Test Value Betting logic with realistic scenarios")
    print(f"{Fore.YELLOW}📊 Scenarios:{Style.RESET_ALL} 3 matches with different value levels")
    print(f"{Fore.YELLOW}⏰ Time:{Style.RESET_ALL} {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # Database session
    db = SessionLocal()
    
    try:
        # Get test predictions
        print(f"{Fore.GREEN}📥 Fetching predictions from database...{Style.RESET_ALL}")
        predictions = get_test_predictions(db, limit=3)
        
        if len(predictions) < 3:
            print(f"{Fore.RED}❌ Error: Need at least 3 predictions in database. Found: {len(predictions)}{Style.RESET_ALL}")
            return
        
        print(f"{Fore.GREEN}✓ Found {len(predictions)} predictions{Style.RESET_ALL}\n")
        
        # Create scenarios
        all_scenarios = []
        
        print(f"{Fore.GREEN}🔧 Creating scenarios...{Style.RESET_ALL}\n")
        
        # Scenario A: HIGH VALUE
        scenario_a = create_scenario_a_high_value(predictions[0])
        all_scenarios.append(scenario_a)
        print_scenario_analysis(scenario_a)
        
        # Scenario B: NO VALUE
        scenario_b = create_scenario_b_no_value(predictions[1])
        all_scenarios.append(scenario_b)
        print_scenario_analysis(scenario_b)
        
        # Scenario C: FAIR VALUE
        scenario_c = create_scenario_c_fair_value(predictions[2])
        all_scenarios.append(scenario_c)
        print_scenario_analysis(scenario_c)
        
        # Commit changes to database
        print(f"\n{Fore.GREEN}💾 Saving scenarios to database...{Style.RESET_ALL}")
        db.commit()
        print(f"{Fore.GREEN}✓ Database updated successfully{Style.RESET_ALL}")
        
        # Print summary table
        print_summary_table(all_scenarios)
        
        # Frontend testing instructions
        print(f"\n\n{Fore.CYAN}{'=' * 80}")
        print(f"{Fore.CYAN}{'FRONTEND TESTING INSTRUCTIONS'.center(80)}")
        print(f"{Fore.CYAN}{'=' * 80}{Style.RESET_ALL}\n")
        
        print(f"{Fore.YELLOW}1. Start servers:{Style.RESET_ALL}")
        print(f"   Backend:  cd backend && source venv/bin/activate && python -m uvicorn src.api.main:app --reload --port 8000")
        print(f"   Frontend: cd frontend && npm run dev")
        
        print(f"\n{Fore.YELLOW}2. Navigate to these matches:{Style.RESET_ALL}")
        for i, scenario in enumerate(all_scenarios):
            print(f"   {chr(65 + i)}. http://localhost:5173/prediction/{scenario['match_id']}")
        
        print(f"\n{Fore.YELLOW}3. Verify in UI:{Style.RESET_ALL}")
        verify_table = [
            ["Match A", "🟢 VALUE: HIGH badge (green)", "Kelly bar at ~25% (full/near-full)", "EV: 1.500x (+50.0%)"],
            ["Match B", "🔴 VALUE: NEUTRAL/NONE (gray)", "Kelly bar at 0% (empty)", "EV: 0.720x (-28.0%)"],
            ["Match C", "🟡 VALUE: NEUTRAL (gray/yellow)", "Kelly bar at 0% (empty)", "EV: 1.000x (0.0%)"]
        ]
        print(tabulate(verify_table, headers=["Match", "Badge Color", "Kelly Bar", "Expected Value"], tablefmt="simple"))
        
        print(f"\n{Fore.GREEN}✅ Simulation complete! Database updated with test scenarios.{Style.RESET_ALL}")
        print(f"{Fore.GREEN}✅ Ready for frontend validation.{Style.RESET_ALL}\n")
        
    except Exception as e:
        print(f"\n{Fore.RED}❌ Error during simulation: {str(e)}{Style.RESET_ALL}")
        db.rollback()
        raise
    
    finally:
        db.close()


if __name__ == "__main__":
    main()
