"""
Betting Value Analysis Service

This module provides Kelly Criterion calculations and value betting analysis
for football match predictions. It helps determine optimal stake sizes and
identifies high-value betting opportunities.

Mathematical Foundation:
- Kelly Criterion: f* = (bp - q) / b
  Where: b = odds - 1, p = win probability, q = loss probability
  
- Expected Value: EV = probability × odds
  
- Value Levels:
  * HIGH: EV > 1.15 (15%+ edge)
  * MEDIUM: 1.05 ≤ EV ≤ 1.15 (5-15% edge)
  * NEUTRAL: EV < 1.05 (<5% edge)
"""

from typing import Dict, Optional
import math


def calculate_kelly_criterion(
    probability: float,
    decimal_odds: float,
    max_kelly: float = 0.25
) -> Dict[str, float]:
    """
    Calculate the optimal bet size using the Kelly Criterion formula.
    
    The Kelly Criterion determines the optimal fraction of bankroll to wager
    based on the probability of winning and the odds offered.
    
    Formula: f* = (bp - q) / b
    Where:
        b = decimal odds - 1 (net odds)
        p = probability of winning
        q = probability of losing (1 - p)
        f* = fraction of bankroll to bet
    
    Args:
        probability: AI predicted win probability (0.0 to 1.0)
        decimal_odds: Bookmaker decimal odds (e.g., 2.50)
        max_kelly: Maximum Kelly percentage to cap risk (default: 0.25 = 25%)
                   Using fractional Kelly for safety
    
    Returns:
        Dictionary with:
            - kelly_percentage: Recommended stake as percentage (0-25%)
            - kelly_raw: Raw uncapped Kelly value
            - is_positive: Whether there's a positive edge
            - risk_level: LOW/MEDIUM/HIGH based on Kelly %
    
    Examples:
        >>> calculate_kelly_criterion(0.60, 2.00)
        {'kelly_percentage': 20.0, 'kelly_raw': 0.20, 'is_positive': True, 'risk_level': 'HIGH'}
        
        >>> calculate_kelly_criterion(0.40, 2.00)
        {'kelly_percentage': 0.0, 'kelly_raw': -0.20, 'is_positive': False, 'risk_level': 'NONE'}
    """
    # Input validation
    if not 0 <= probability <= 1:
        raise ValueError("Probability must be between 0 and 1")
    if decimal_odds < 1.0:
        raise ValueError("Decimal odds must be >= 1.0")
    
    # Calculate Kelly Criterion
    b = decimal_odds - 1  # Net odds (profit per unit staked)
    p = probability
    q = 1 - probability  # Probability of losing
    
    # Kelly formula: f* = (bp - q) / b
    if b == 0:
        # Odds of 1.0 means no profit, no bet
        kelly_raw = 0.0
    else:
        kelly_raw = (b * p - q) / b
    
    # Determine if there's a positive edge
    is_positive = kelly_raw > 0
    
    # Cap at max_kelly for safety (fractional Kelly)
    # Negative Kelly means no value, set to 0
    kelly_capped = max(0, min(kelly_raw, max_kelly))
    kelly_percentage = kelly_capped * 100
    
    # Determine risk level based on Kelly percentage
    if kelly_percentage == 0:
        risk_level = "NONE"
    elif kelly_percentage < 5:
        risk_level = "LOW"
    elif kelly_percentage < 15:
        risk_level = "MEDIUM"
    else:
        risk_level = "HIGH"
    
    return {
        "kelly_percentage": round(kelly_percentage, 2),
        "kelly_raw": round(kelly_raw, 4),
        "is_positive": is_positive,
        "risk_level": risk_level
    }


def calculate_value_level(
    probability: float,
    decimal_odds: float
) -> Dict[str, any]:
    """
    Calculate the value level of a bet based on Expected Value (EV).
    
    Expected Value measures whether a bet offers good value by comparing
    the AI probability against the bookmaker's implied probability.
    
    Formula: EV = probability × decimal_odds
    
    Value Levels:
        - HIGH: EV > 1.15 (15%+ edge over bookmaker)
        - MEDIUM: 1.05 ≤ EV ≤ 1.15 (5-15% edge)
        - NEUTRAL: EV < 1.05 (<5% edge, not recommended)
    
    Args:
        probability: AI predicted win probability (0.0 to 1.0)
        decimal_odds: Bookmaker decimal odds (e.g., 2.50)
    
    Returns:
        Dictionary with:
            - level: "HIGH", "MEDIUM", or "NEUTRAL"
            - ev: Expected value (multiplier)
            - edge_percentage: Edge over bookmaker as percentage
            - implied_prob: Bookmaker's implied probability
            - recommendation: Human-readable recommendation
    
    Examples:
        >>> calculate_value_level(0.65, 2.00)
        {'level': 'HIGH', 'ev': 1.30, 'edge_percentage': 30.0, ...}
        
        >>> calculate_value_level(0.45, 2.00)
        {'level': 'NEUTRAL', 'ev': 0.90, 'edge_percentage': -10.0, ...}
    """
    # Input validation
    if not 0 <= probability <= 1:
        raise ValueError("Probability must be between 0 and 1")
    if decimal_odds < 1.0:
        raise ValueError("Decimal odds must be >= 1.0")
    
    # Calculate Expected Value
    ev = probability * decimal_odds
    edge_percentage = (ev - 1) * 100
    
    # Bookmaker's implied probability (including margin)
    implied_prob = 1 / decimal_odds if decimal_odds > 0 else 0
    
    # Determine value level
    if ev >= 1.15:
        level = "HIGH"
        recommendation = "Strong value bet - significant edge over bookmaker"
    elif ev >= 1.05:
        level = "MEDIUM"
        recommendation = "Moderate value - small edge over bookmaker"
    else:
        level = "NEUTRAL"
        recommendation = "No significant value - avoid or small stake only"
    
    return {
        "level": level,
        "ev": round(ev, 3),
        "edge_percentage": round(edge_percentage, 2),
        "implied_prob": round(implied_prob, 4),
        "recommendation": recommendation
    }


def estimate_bookmaker_odds(
    ai_probability: float,
    bookmaker_margin: float = 0.10
) -> float:
    """
    Estimate bookmaker decimal odds based on AI probability.
    
    This is a fallback function for when real bookmaker odds are unavailable.
    It applies a typical bookmaker margin to the fair odds.
    
    Formula: estimated_odds = 1 / (ai_probability × (1 - margin))
    
    Args:
        ai_probability: AI predicted probability (0.0 to 1.0)
        bookmaker_margin: Typical bookmaker margin (default: 0.10 = 10%)
    
    Returns:
        Estimated decimal odds
    
    Examples:
        >>> estimate_bookmaker_odds(0.50, margin=0.10)
        2.22  # Fair odds would be 2.00, margin increases to 2.22
        
        >>> estimate_bookmaker_odds(0.33, margin=0.10)
        3.33  # Fair odds ~3.00, margin increases to 3.33
    """
    # Input validation
    if not 0 < ai_probability <= 1:
        raise ValueError("AI probability must be between 0 and 1 (exclusive of 0)")
    if not 0 <= bookmaker_margin < 1:
        raise ValueError("Bookmaker margin must be between 0 and 1")
    
    # Calculate fair odds
    fair_odds = 1 / ai_probability
    
    # Apply bookmaker margin
    # Margin reduces the payout, so we divide by (1 - margin)
    # Equivalent to: 1 / (ai_probability × (1 - margin))
    adjusted_probability = ai_probability * (1 - bookmaker_margin)
    estimated_odds = 1 / adjusted_probability if adjusted_probability > 0 else 1.01
    
    return round(estimated_odds, 2)


def analyze_bet_value(
    ai_probability: float,
    decimal_odds: Optional[float] = None,
    market_name: str = "1X2",
    use_estimated_odds: bool = True
) -> Dict[str, any]:
    """
    Perform complete value analysis for a betting market.
    
    This is the main function that combines Kelly Criterion and value level
    calculations to provide a comprehensive betting recommendation.
    
    Args:
        ai_probability: AI predicted probability (0.0 to 1.0)
        decimal_odds: Bookmaker odds (if None, will estimate)
        market_name: Name of the betting market (e.g., "1X2", "Over 2.5")
        use_estimated_odds: Whether to estimate odds if not provided
    
    Returns:
        Dictionary with complete analysis:
            - kelly_percentage: Recommended stake %
            - value_level: HIGH/MEDIUM/NEUTRAL
            - ev: Expected value
            - edge_percentage: Edge %
            - odds_used: Actual or estimated odds
            - is_estimated_odds: Boolean flag
            - recommendation: Text recommendation
            - should_bet: Boolean recommendation
    
    Example:
        >>> analyze_bet_value(0.60, 2.50)
        {
            'kelly_percentage': 16.0,
            'value_level': 'HIGH',
            'ev': 1.50,
            'edge_percentage': 50.0,
            'should_bet': True,
            ...
        }
    """
    # Get or estimate odds
    if decimal_odds is None:
        if not use_estimated_odds:
            raise ValueError("Odds not provided and estimation is disabled")
        decimal_odds = estimate_bookmaker_odds(ai_probability)
        is_estimated = True
    else:
        is_estimated = False
    
    # Calculate Kelly Criterion
    kelly_result = calculate_kelly_criterion(ai_probability, decimal_odds)
    
    # Calculate Value Level
    value_result = calculate_value_level(ai_probability, decimal_odds)
    
    # Determine overall recommendation
    should_bet = (
        kelly_result["is_positive"] and
        value_result["level"] in ["HIGH", "MEDIUM"] and
        kelly_result["kelly_percentage"] >= 3.0  # Minimum 3% Kelly to recommend
    )
    
    # Combine results
    analysis = {
        "market": market_name,
        "ai_probability": round(ai_probability, 4),
        "odds_used": decimal_odds,
        "is_estimated_odds": is_estimated,
        
        # Kelly Criterion
        "kelly_percentage": kelly_result["kelly_percentage"],
        "kelly_raw": kelly_result["kelly_raw"],
        "risk_level": kelly_result["risk_level"],
        
        # Value Analysis
        "value_level": value_result["level"],
        "ev": value_result["ev"],
        "edge_percentage": value_result["edge_percentage"],
        "implied_prob": value_result["implied_prob"],
        
        # Recommendations
        "should_bet": should_bet,
        "recommendation": value_result["recommendation"]
    }
    
    return analysis


def analyze_prediction_markets(prediction_data: Dict) -> Dict[str, Dict]:
    """
    Analyze all available markets for a prediction.
    
    Args:
        prediction_data: Dictionary with prediction probabilities
            Example: {
                'prob_home_win': 0.55,
                'prob_draw': 0.25,
                'prob_away_win': 0.20,
                'prob_over_25': 0.60,
                'btts_probability': 0.65
            }
    
    Returns:
        Dictionary of market analyses, keyed by market name
    """
    analyses = {}
    
    # 1X2 Markets
    if 'prob_home_win' in prediction_data:
        analyses['home_win'] = analyze_bet_value(
            prediction_data['prob_home_win'],
            market_name="Home Win (1)"
        )
    
    if 'prob_draw' in prediction_data:
        analyses['draw'] = analyze_bet_value(
            prediction_data['prob_draw'],
            market_name="Draw (X)"
        )
    
    if 'prob_away_win' in prediction_data:
        analyses['away_win'] = analyze_bet_value(
            prediction_data['prob_away_win'],
            market_name="Away Win (2)"
        )
    
    # Over/Under Markets
    if 'prob_over_25' in prediction_data:
        analyses['over_25'] = analyze_bet_value(
            prediction_data['prob_over_25'],
            market_name="Over 2.5 Goals"
        )
    
    # BTTS
    if 'btts_probability' in prediction_data:
        analyses['btts'] = analyze_bet_value(
            prediction_data['btts_probability'],
            market_name="Both Teams To Score"
        )
    
    # Combo markets (if available)
    if 'combo_predictions' in prediction_data:
        for combo_key, combo_prob in prediction_data['combo_predictions'].items():
            if combo_prob > 0.10:  # Only analyze combos with >10% probability
                analyses[f'combo_{combo_key}'] = analyze_bet_value(
                    combo_prob,
                    market_name=f"Combo: {combo_key}"
                )
    
    return analyses


# Example usage and testing
if __name__ == "__main__":
    # Test Kelly Criterion
    print("=== Kelly Criterion Tests ===")
    print(calculate_kelly_criterion(0.60, 2.00))  # 20% Kelly
    print(calculate_kelly_criterion(0.40, 2.00))  # Negative edge, 0%
    print(calculate_kelly_criterion(0.70, 1.80))  # High probability, moderate odds
    
    print("\n=== Value Level Tests ===")
    print(calculate_value_level(0.65, 2.00))  # HIGH value
    print(calculate_value_level(0.52, 2.00))  # MEDIUM value
    print(calculate_value_level(0.45, 2.00))  # NEUTRAL (no value)
    
    print("\n=== Odds Estimation Tests ===")
    print(estimate_bookmaker_odds(0.50))  # Should be ~2.22
    print(estimate_bookmaker_odds(0.33))  # Should be ~3.33
    
    print("\n=== Complete Analysis ===")
    print(analyze_bet_value(0.60, 2.50, market_name="Home Win"))
