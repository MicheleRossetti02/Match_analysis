"""
Performance Tracking Service

Handles bet recording, result updates, ROI calculations, and equity curve generation.
"""

from datetime import datetime
from typing import Dict, List, Optional
from sqlalchemy import func
from sqlalchemy.orm import Session

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from src.models.database import BetHistory, Prediction, Match


def record_bet(
    db: Session,
    prediction_id: int,
    market: str,
    market_name: str,
    bankroll: float,
    kelly_percent: float,
    odds: float,
    ai_probability: float,
    expected_value: float,
    edge_percentage: float,
    value_level: str,
    is_estimated_odds: bool = True,
    notes: Optional[str] = None
) -> BetHistory:
    """
    Record a new bet in the database.
    
    Args:
        db: Database session
        prediction_id: ID of the prediction
        market: Market code (H, D, A, Over2.5, etc.)
        market_name: Human-readable market name
        bankroll: Current bankroll size
        kelly_percent: Kelly Criterion percentage (0-25%)
        odds: Decimal odds
        ai_probability: AI predicted probability
        expected_value: Expected value (probability × odds)
        edge_percentage: Edge percentage
        value_level: HIGH, MEDIUM, NEUTRAL
        is_estimated_odds: Whether odds are estimated or live
        notes: Optional notes
    
    Returns:
        BetHistory object
    """
    # Calculate stake amount based on Kelly %
    stake_amount = (kelly_percent / 100) * bankroll
    
    # Determine confidence level based on Kelly %
    if kelly_percent >= 15:
        confidence_level = "HIGH"
    elif kelly_percent >= 8:
        confidence_level = "MEDIUM"
    else:
        confidence_level = "LOW"
    
    # Create bet record
    bet = BetHistory(
        prediction_id=prediction_id,
        market=market,
        market_name=market_name,
        stake_kelly_percent=kelly_percent,
        stake_amount=stake_amount,
        bankroll_at_bet=bankroll,
        odds=odds,
        is_estimated_odds=is_estimated_odds,
        ai_probability=ai_probability,
        expected_value=expected_value,
        edge_percentage=edge_percentage,
        value_level=value_level,
        status='PENDING',
        notes=notes,
        confidence_level=confidence_level,
        placed_at=datetime.utcnow()
    )
    
    db.add(bet)
    db.commit()
    db.refresh(bet)
    
    return bet


def update_bet_results(db: Session) -> Dict[str, int]:
    """
    Worker function to update bet results for finished matches.
    
    Checks all PENDING bets, finds finished matches, and settles bets
    """
    # Get all pending bets with their matches
    pending_bets = (
        db.query(BetHistory)
        .join(Prediction, BetHistory.prediction_id == Prediction.id)
        .join(Match, Prediction.match_id == Match.id)
        .filter(BetHistory.status == 'PENDING')
        .filter(Match.status == 'FT')  # Finished matches
        .all()
    )
    
    updated_count = 0
    won_count = 0
    lost_count = 0
    
    for bet in pending_bets:
        prediction = bet.prediction
        match = prediction.match
        
        # Determine actual result
        if match.home_goals > match.away_goals:
            actual_result = 'H'
        elif match.home_goals < match.away_goals:
            actual_result = 'A'
        else:
            actual_result = 'D'
        
        # Check if bet won
        is_winner = (bet.market == actual_result)
        
        # Calculate P&L
        if is_winner:
            pnl = (bet.stake_amount * bet.odds) - bet.stake_amount
            status = 'WON'
            won_count += 1
        else:
            pnl = -bet.stake_amount
            status = 'LOST'
            lost_count += 1
        
        # Calculate ROI
        roi_percent = (pnl / bet.stake_amount) * 100 if bet.stake_amount > 0 else 0
        
        # Calculate bankroll after
        bankroll_after = bet.bankroll_at_bet + pnl
        
        # Update bet
        bet.status = status
        bet.actual_result = actual_result
        bet.is_winner = is_winner
        bet.pnl = pnl
        bet.roi_percent = roi_percent
        bet.bankroll_after = bankroll_after
        bet.settled_at = datetime.utcnow()
        
        updated_count += 1
    
    db.commit()
    
    return {
        'updated': updated_count,
        'won': won_count,
        'lost': lost_count
    }


def get_performance_stats(db: Session) -> Dict:
    """
    Calculate aggregate performance statistics.
    
    Returns:
        Dictionary with ROI, win rate, total bets, etc.
    """
    # Get all settled bets
    settled_bets = (
        db.query(BetHistory)
        .filter(BetHistory.status.in_(['WON', 'LOST']))
        .all()
    )
    
    if not settled_bets:
        return {
            'total_bets': 0,
            'pending_bets': db.query(BetHistory).filter(BetHistory.status == 'PENDING').count(),
            'total_staked': 0,
            'total_pnl': 0,
            'roi_percent': 0,
            'win_rate': 0,
            'avg_odds': 0,
            'avg_stake': 0,
            'best_win': 0,
            'worst_loss': 0
        }
    
    # Calculate totals
    total_bets = len(settled_bets)
    total_staked = sum(bet.stake_amount for bet in settled_bets)
    total_pnl = sum(bet.pnl for bet in settled_bets)
    won_bets = sum(1 for bet in settled_bets if bet.is_winner)
    
    # Calculate metrics
    roi_percent = (total_pnl / total_staked * 100) if total_staked > 0 else 0
    win_rate = (won_bets / total_bets * 100) if total_bets > 0 else 0
    avg_odds = sum(bet.odds for bet in settled_bets) / total_bets if total_bets > 0 else 0
    avg_stake = total_staked / total_bets if total_bets > 0 else 0
    
    # Best/worst
    best_win = max((bet.pnl for bet in settled_bets if bet.is_winner), default=0)
    worst_loss = min((bet.pnl for bet in settled_bets if not bet.is_winner), default=0)
    
    # Pending bets
    pending_count = db.query(BetHistory).filter(BetHistory.status == 'PENDING').count()
    
    # Value level breakdown
    high_value_bets = sum(1 for bet in settled_bets if bet.value_level == 'HIGH')
    medium_value_bets = sum(1 for bet in settled_bets if bet.value_level == 'MEDIUM')
    
    high_value_won = sum(1 for bet in settled_bets if bet.value_level == 'HIGH' and bet.is_winner)
    medium_value_won = sum(1 for bet in settled_bets if bet.value_level == 'MEDIUM' and bet.is_winner)
    
    return {
        'total_bets': total_bets,
        'pending_bets': pending_count,
        'won_bets': won_bets,
        'lost_bets': total_bets - won_bets,
        'total_staked': round(total_staked, 2),
        'total_pnl': round(total_pnl, 2),
        'roi_percent': round(roi_percent, 2),
        'win_rate': round(win_rate, 2),
        'avg_odds': round(avg_odds, 2),
        'avg_stake': round(avg_stake, 2),
        'best_win': round(best_win, 2),
        'worst_loss': round(worst_loss, 2),
        'high_value_bets': high_value_bets,
        'medium_value_bets': medium_value_bets,
        'high_value_win_rate': round((high_value_won / high_value_bets * 100) if high_value_bets > 0 else 0, 2),
        'medium_value_win_rate': round((medium_value_won / medium_value_bets * 100) if medium_value_bets > 0 else 0, 2)
    }


def get_equity_curve(db: Session, initial_bankroll: float = 1000.0) -> List[Dict]:
    """
    Generate equity curve data showing bankroll growth over time.
    
    Args:
        db: Database session
        initial_bankroll: Starting bankroll amount
    
    Returns:
        List of dictionaries with date, bankroll, cumulative_pnl
    """
    # Get all settled bets ordered by settled date
    settled_bets = (
        db.query(BetHistory)
        .filter(BetHistory.status.in_(['WON', 'LOST']))
        .filter(BetHistory.settled_at.isnot(None))
        .order_by(BetHistory.settled_at)
        .all()
    )
    
    if not settled_bets:
        return [{
            'date': datetime.utcnow().isoformat(),
            'bankroll': initial_bankroll,
            'cumulative_pnl': 0,
            'bet_count': 0
        }]
    
    equity_curve = [{
        'date': settled_bets[0].placed_at.isoformat(),
        'bankroll': initial_bankroll,
        'cumulative_pnl': 0,
        'bet_count': 0
    }]
    
    current_bankroll = initial_bankroll
    cumulative_pnl = 0
    
    for idx, bet in enumerate(settled_bets, 1):
        cumulative_pnl += bet.pnl
        current_bankroll = initial_bankroll + cumulative_pnl
        
        equity_curve.append({
            'date': bet.settled_at.isoformat(),
            'bankroll': round(current_bankroll, 2),
            'cumulative_pnl': round(cumulative_pnl, 2),
            'bet_count': idx,
            'bet_result': 'WON' if bet.is_winner else 'LOST',
            'pnl': round(bet.pnl, 2)
        })
    
    return equity_curve


def get_bet_history(
    db: Session,
    value_level: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 50
) -> List[BetHistory]:
    """
    Get bet history with optional filters.
    
    Args:
        db: Database session
        value_level: Filter by value level (HIGH, MEDIUM, NEUTRAL)
        status: Filter by status (PENDING, WON, LOST)
        limit: Maximum number of records
    
    Returns:
        List of BetHistory objects
    """
    query = db.query(BetHistory).order_by(BetHistory.placed_at.desc())
    
    if value_level:
        query = query.filter(BetHistory.value_level == value_level)
    
    if status:
        query = query.filter(BetHistory.status == status)
    
    return query.limit(limit).all()


# Example usage and testing
if __name__ == "__main__":
    from src.models.database import SessionLocal
    
    db = SessionLocal()
    
    print("=== Performance Tracking Service Test ===\n")
    
    # Get stats
    stats = get_performance_stats(db)
    print(f"📊 Performance Stats:")
    for key, value in stats.items():
        print(f"   {key}: {value}")
    
    # Get equity curve
    print(f"\n📈 Equity Curve:")
    curve = get_equity_curve(db, initial_bankroll=1000)
    print(f"   Total points: {len(curve)}")
    if curve:
        print(f"   Start: ${curve[0]['bankroll']:.2f}")
        print(f"   End: ${curve[-1]['bankroll']:.2f}")
        print(f"   P&L: ${curve[-1]['cumulative_pnl']:.2f}")
    
    db.close()
