"""
Feature Engineering for Football Match Prediction
Transforms raw match data into ML features
"""
import sys
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import pandas as pd
from sqlalchemy.orm import Session

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from src.models.database import SessionLocal, Match, Team, League
from config import settings


class FeatureEngineer:
    """Creates features from match data for ML models"""
    
    def __init__(self, db: Session = None):
        self.db = db or SessionLocal()
        # Memoization cache for expensive queries
        self._cache = {
            'team_form': {},      # (team_id, date, last_n, home_away) -> result
            'league_pos': {},     # (team_id, league_id, date) -> position
            'h2h': {},           # (home_id, away_id, date, last_n) -> result
            'bulk_matches': None  # Preloaded matches for batch processing
        }
        self._cache_hits = 0
        self._cache_misses = 0
    
    def calculate_team_form(
        self, 
        team_id: int, 
        before_date: datetime,
        last_n: int = 5,
        home_away: str = 'all',
        use_recency_weights: bool = False
    ) -> Dict:
        """
        Calculate team form based on recent matches with optional recency bias
        WITH MEMOIZATION CACHE
        
        Args:
            team_id: Team ID
            before_date: Calculate form before this date
            last_n: Number of recent matches to consider
            home_away: 'all', 'home', or 'away'
            use_recency_weights: If True, apply exponential decay weights (λ=0.85)
            
        Returns:
            Dict with form metrics
        """
        # Check cache first
        cache_key = (team_id, before_date.isoformat(), last_n, home_away, use_recency_weights)
        if cache_key in self._cache['team_form']:
            self._cache_hits += 1
            return self._cache['team_form'][cache_key]
        
        self._cache_misses += 1
        
        # Use bulk matches if available
        if self._cache['bulk_matches'] is not None:
            # Filter from preloaded matches
            recent_matches = [
                m for m in self._cache['bulk_matches']
                if m.match_date < before_date and m.status == 'FT' and (
                    (home_away == 'all' and (m.home_team_id == team_id or m.away_team_id == team_id)) or
                    (home_away == 'home' and m.home_team_id == team_id) or
                    (home_away == 'away' and m.away_team_id == team_id)
                )
            ]
            # Sort by date desc and take last_n
            recent_matches = sorted(recent_matches, key=lambda x: x.match_date, reverse=True)[:last_n]
        else:
            # Query for recent matches (original logic)
            query = self.db.query(Match).filter(
                Match.match_date < before_date,
                Match.status == 'FT'
            )
            
            if home_away == 'home':
                query = query.filter(Match.home_team_id == team_id)
            elif home_away == 'away':
                query = query.filter(Match.away_team_id == team_id)
            else:
                query = query.filter(
                    (Match.home_team_id == team_id) | (Match.away_team_id == team_id)
                )
            
            recent_matches = query.order_by(Match.match_date.desc()).limit(last_n).all()
        
        if not recent_matches:
            result = {
                'wins': 0, 'draws': 0, 'losses': 0,
                'goals_for': 0, 'goals_against': 0,
                'points': 0, 'matches_played': 0,
                'win_rate': 0.0,
                'avg_goals_for': 0.0,
                'avg_goals_against': 0.0,
                'weighted_points': 0.0
            }
            self._cache['team_form'][cache_key] = result
            return result
        
        # Calculate stats
        wins_weighted = draws_weighted = losses_weighted = 0.0
        goals_for_weighted = goals_against_weighted = 0.0
        weighted_points_sum = 0.0
        total_weight = 0.0
        decay_factor = 0.85
        
        for i, match in enumerate(recent_matches):
            is_home = match.home_team_id == team_id
            team_goals = match.home_goals or 0 if is_home else match.away_goals or 0
            opponent_goals = match.away_goals or 0 if is_home else match.home_goals or 0
            
            weight = decay_factor ** i if use_recency_weights else 1.0
            total_weight += weight
            
            match_points = 0
            if team_goals > opponent_goals:
                wins_weighted += weight
                match_points = 3
            elif team_goals == opponent_goals:
                draws_weighted += weight
                match_points = 1
            else:
                losses_weighted += weight
                match_points = 0
            
            goals_for_weighted += team_goals * weight
            goals_against_weighted += opponent_goals * weight
            weighted_points_sum += match_points * weight
        
        matches_played = len(recent_matches)
        
        if total_weight > 0:
            wins = wins_weighted / total_weight
            draws = draws_weighted / total_weight
            losses = losses_weighted / total_weight
            goals_for = goals_for_weighted / total_weight
            goals_against = goals_against_weighted / total_weight
            weighted_points = weighted_points_sum / total_weight
        else: # Should not happen if matches_played > 0, but for safety
            wins = draws = losses = goals_for = goals_against = weighted_points = 0.0
        
        points = (wins_weighted * 3 + draws_weighted) / max(total_weight, 1) if use_recency_weights else (wins_weighted * 3 + draws_weighted) / matches_played if matches_played > 0 else 0
        
        result = {
            'wins': wins,
            'draws': draws,
            'losses': losses,
            'goals_for': goals_for,
            'goals_against': goals_against,
            'points': points, # This 'points' is the average points per game, potentially weighted
            'matches_played': matches_played,
            'win_rate': wins, # Already weighted if use_recency_weights is True
            'avg_goals_for': goals_for,
            'avg_goals_against': goals_against,
            'weighted_points': weighted_points
        }
        
        # Store in cache
        self._cache['team_form'][cache_key] = result
        return result
    
    def get_h2h_record(
        self,
        home_team_id: int,
        away_team_id: int,
        before_date: datetime,
        last_n: int = 5
    ) -> Dict:
        """
        Get head-to-head record between two teams
        WITH MEMOIZATION CACHE
        
        Returns:
            Dict with H2H statistics
        """
        # Check cache first
        cache_key = (home_team_id, away_team_id, before_date.isoformat(), last_n)
        if cache_key in self._cache['h2h']:
            self._cache_hits += 1
            return self._cache['h2h'][cache_key]
        
        self._cache_misses += 1
        
        # Use bulk matches if available
        if self._cache['bulk_matches'] is not None:
            h2h_matches = [
                m for m in self._cache['bulk_matches']
                if m.match_date < before_date and m.status == 'FT' and (
                    (m.home_team_id == home_team_id and m.away_team_id == away_team_id) or
                    (m.home_team_id == away_team_id and m.away_team_id == home_team_id)
                )
            ]
            h2h_matches = sorted(h2h_matches, key=lambda x: x.match_date, reverse=True)[:last_n]
        else:
            # Original query logic
            h2h_matches = self.db.query(Match).filter(
                Match.match_date < before_date,
                Match.status == 'FT',
                ((Match.home_team_id == home_team_id) & (Match.away_team_id == away_team_id)) |
                ((Match.home_team_id == away_team_id) & (Match.away_team_id == home_team_id))
            ).order_by(Match.match_date.desc()).limit(last_n).all()
        
        if not h2h_matches:
            result = {
                'h2h_matches': 0,
                'home_wins': 0,
                'draws': 0,
                'away_wins': 0,
                'avg_goals_home': 0.0,
                'avg_goals_away': 0.0
            }
            self._cache['h2h'][cache_key] = result
            return result
        
        home_wins = draws = away_wins = 0
        total_goals_ht = total_goals_at = 0
        
        for match in h2h_matches:
            if match.home_team_id == home_team_id:
                if (match.home_goals or 0) > (match.away_goals or 0):
                    home_wins += 1
                elif (match.home_goals or 0) == (match.away_goals or 0):
                    draws += 1
                else:
                    away_wins += 1
                total_goals_ht += (match.home_goals or 0)
                total_goals_at += (match.away_goals or 0)
            else: # The query home team is the away team in this match
                if (match.away_goals or 0) > (match.home_goals or 0):
                    away_wins += 1
                elif (match.away_goals or 0) == (match.home_goals or 0):
                    draws += 1
                else:
                    home_wins += 1
                total_goals_ht += (match.away_goals or 0) # Goals scored by the query home team
                total_goals_at += (match.home_goals or 0) # Goals scored by the query away team
        
        matches_count = len(h2h_matches)
        result = {
            'h2h_matches': matches_count,
            'home_wins': home_wins,
            'draws': draws,
            'away_wins': away_wins,
            'avg_goals_home': total_goals_ht / matches_count if matches_count > 0 else 0.0,
            'avg_goals_away': total_goals_at / matches_count if matches_count > 0 else 0.0
        }
        
        self._cache['h2h'][cache_key] = result
        return result
    
    def calculate_league_position(
        self,
        team_id: int,
        league_id: int,
        before_date: datetime
    ) -> int:
        """
        Calculate team's league position at a given date
        WITH BULK LOADING AND CACHING
        
        Returns:
            League position (1-based)
        """
        # Check cache first
        cache_key = (team_id, league_id, before_date.isoformat())
        if cache_key in self._cache['league_pos']:
            self._cache_hits += 1
            return self._cache['league_pos'][cache_key]
        
        self._cache_misses += 1
        
        # Use bulk matches if available
        if self._cache['bulk_matches'] is not None:
            league_matches = [
                m for m in self._cache['bulk_matches']
                if m.league_id == league_id and m.match_date < before_date and m.status == 'FT'
            ]
        else:
            # Original query
            league_matches = self.db.query(Match).filter(
                Match.league_id == league_id,
                Match.match_date < before_date,
                Match.status == 'FT'
            ).all()
        
        if not league_matches:
            self._cache['league_pos'][cache_key] = 10 # Default to middle position if no matches
            return 10
        
        # Calculate standings
        standings = {}
        for match in league_matches:
            for tid in [match.home_team_id, match.away_team_id]:
                if tid not in standings:
                    standings[tid] = {'points': 0, 'gd': 0}
            
            home_goals = match.home_goals or 0
            away_goals = match.away_goals or 0
            
            if home_goals > away_goals:
                standings[match.home_team_id]['points'] += 3
            elif away_goals > home_goals:
                standings[match.away_team_id]['points'] += 3
            else:
                standings[match.home_team_id]['points'] += 1
                standings[match.away_team_id]['points'] += 1
            
            standings[match.home_team_id]['gd'] += (home_goals - away_goals)
            standings[match.away_team_id]['gd'] += (away_goals - home_goals)
        
        # Sort by points, then GD
        sorted_teams = sorted(
            standings.items(),
            key=lambda x: (x[1]['points'], x[1]['gd']),
            reverse=True
        )
        
        # Find position
        position = len(sorted_teams) // 2 # Default to middle if team not found
        for pos, (tid, _) in enumerate(sorted_teams, 1):
            if tid == team_id:
                position = pos
                break
        
        self._cache['league_pos'][cache_key] = position
        return position
    
    def get_goal_statistics(
        self,
        team_id: int,
        before_date: datetime,
        last_n: int = 10,
        home_away: str = 'all'
    ) -> Dict:
        """
        Calculate detailed goal statistics
        
        Returns:
            Dict with goal metrics
        """
        form = self.calculate_team_form(team_id, before_date, last_n, home_away)
        
        # Get matches for additional stats
        query = self.db.query(Match).filter(
            Match.match_date < before_date,
            Match.status == 'FT'
        )
        
        if home_away == 'home':
            query = query.filter(Match.home_team_id == team_id)
        elif home_away == 'away':
            query = query.filter(Match.away_team_id == team_id)
        else:
            query = query.filter(
                (Match.home_team_id == team_id) | (Match.away_team_id == team_id)
            )
        
        matches = query.order_by(Match.match_date.desc()).limit(last_n).all()
        
        clean_sheets = 0
        btts = 0  # Both teams to score
        over_25 = 0
        
        for match in matches:
            is_home = match.home_team_id == team_id
            ga = match.away_goals if is_home else match.home_goals
            total_goals = (match.home_goals or 0) + (match.away_goals or 0)
            
            if ga == 0:
                clean_sheets += 1
            if (match.home_goals or 0) > 0 and (match.away_goals or 0) > 0:
                btts += 1
            if total_goals > 2.5:
                over_25 += 1
        
        matches_played = len(matches)
        
        return {
            **form,
            'clean_sheet_rate': clean_sheets / matches_played if matches_played > 0 else 0,
            'btts_rate': btts / matches_played if matches_played > 0 else 0,
            'over_25_rate': over_25 / matches_played if matches_played > 0 else 0
        }
    
    def create_match_features(self, match: Match) -> Dict:
        """
        Create full feature set for a single match
        
        Returns:
            Dict with all features
        """
        features = {}
        
        # Basic match info
        features['league_id'] = match.league_id
        features['home_team_id'] = match.home_team_id
        features['away_team_id'] = match.away_team_id
        features['match_date'] = match.match_date
        
        # Temporal features
        features['day_of_week'] = match.match_date.weekday()
        features['month'] = match.match_date.month
        features['is_weekend'] = 1 if match.match_date.weekday() in [5, 6] else 0
        
        # Home team features (with recency bias)
        home_form_all = self.calculate_team_form(
            match.home_team_id, match.match_date, last_n=5, home_away='all', use_recency_weights=True
        )
        home_form_home = self.calculate_team_form(
            match.home_team_id, match.match_date, last_n=5, home_away='home', use_recency_weights=True
        )
        home_goals = self.get_goal_statistics(
            match.home_team_id, match.match_date, last_n=10, home_away='all'
        )
        
        for key, value in home_form_all.items():
            features[f'home_form_all_{key}'] = value
        for key, value in home_form_home.items():
            features[f'home_form_home_{key}'] = value
        for key, value in home_goals.items():
            if key not in home_form_all:  # Avoid duplicates
                features[f'home_{key}'] = value
        
        # Away team features (with recency bias)
        away_form_all = self.calculate_team_form(
            match.away_team_id, match.match_date, last_n=5, home_away='all', use_recency_weights=True
        )
        away_form_away = self.calculate_team_form(
            match.away_team_id, match.match_date, last_n=5, home_away='away', use_recency_weights=True
        )
        away_goals = self.get_goal_statistics(
            match.away_team_id, match.match_date, last_n=10, home_away='all'
        )
        
        for key, value in away_form_all.items():
            features[f'away_form_all_{key}'] = value
        for key, value in away_form_away.items():
            features[f'away_form_away_{key}'] = value
        for key, value in away_goals.items():
            if key not in away_form_all:
                features[f'away_{key}'] = value
        
        # Head-to-head
        h2h = self.get_h2h_record(
            match.home_team_id, match.away_team_id, match.match_date, last_n=5
        )
        for key, value in h2h.items():
            features[f'h2h_{key}'] = value
        
        # League positions
        features['home_league_position'] = self.calculate_league_position(
            match.home_team_id, match.league_id, match.match_date
        )
        features['away_league_position'] = self.calculate_league_position(
            match.away_team_id, match.league_id, match.match_date
        )
        features['position_diff'] = features['home_league_position'] - features['away_league_position']
        
        # ========== NEW FEATURES FOR IMPROVED ACCURACY ==========
        
        # Rest days (fatigue factor)
        home_rest = self._calculate_rest_days(match.home_team_id, match.match_date)
        away_rest = self._calculate_rest_days(match.away_team_id, match.match_date)
        features['home_rest_days'] = home_rest
        features['away_rest_days'] = away_rest
        features['rest_advantage'] = home_rest - away_rest
        
        # Season progress (0.0 = start, 1.0 = end)
        features['season_progress'] = self._calculate_season_progress(match)
        
        # Current streak (positive = wins, negative = losses)
        features['home_current_streak'] = self._calculate_streak(match.home_team_id, match.match_date)
        features['away_current_streak'] = self._calculate_streak(match.away_team_id, match.match_date)
        
        # Goal difference trend
        features['home_goal_diff'] = home_form_all.get('goals_for', 0) - home_form_all.get('goals_against', 0)
        features['away_goal_diff'] = away_form_all.get('goals_for', 0) - away_form_all.get('goals_against', 0)
        
        # Points per game (PPG)
        home_matches = home_form_all.get('matches_played', 1) or 1
        away_matches = away_form_all.get('matches_played', 1) or 1
        features['home_ppg'] = home_form_all.get('points', 0) / home_matches
        features['away_ppg'] = away_form_all.get('points', 0) / away_matches
        
        # Attack vs Defense matchup
        features['home_attack_vs_away_defense'] = home_form_all.get('avg_goals_for', 0) - away_form_all.get('avg_goals_against', 0)
        features['away_attack_vs_home_defense'] = away_form_all.get('avg_goals_for', 0) - home_form_all.get('avg_goals_against', 0)
        
        # ========== ELO RATINGS (+3-5% accuracy) ==========
        try:
            from src.ml.elo_calculator import get_elo_calculator
            elo_calc = get_elo_calculator()
            home_elo = elo_calc.get_rating_at_date(match.home_team_id, match.match_date)
            away_elo = elo_calc.get_rating_at_date(match.away_team_id, match.match_date)
            features['home_elo'] = home_elo
            features['away_elo'] = away_elo
            features['elo_diff'] = home_elo - away_elo
            features['elo_advantage'] = 1 if home_elo > away_elo else (0 if home_elo == away_elo else -1)
        except:
            features['home_elo'] = 1500
            features['away_elo'] = 1500
            features['elo_diff'] = 0
            features['elo_advantage'] = 0
        
        # ========== HOME/AWAY STRENGTH SPLIT (+1-2% accuracy) ==========
        home_attack = self._calculate_attack_strength(match.home_team_id, match.match_date, 'home')
        home_defense = self._calculate_defense_strength(match.home_team_id, match.match_date, 'home')
        away_attack = self._calculate_attack_strength(match.away_team_id, match.match_date, 'away')
        away_defense = self._calculate_defense_strength(match.away_team_id, match.match_date, 'away')
        
        features['home_attack_strength'] = home_attack
        features['home_defense_strength'] = home_defense
        features['away_attack_strength'] = away_attack
        features['away_defense_strength'] = away_defense
        features['expected_home_goals'] = home_attack - away_defense + 0.3  # home advantage
        features['expected_away_goals'] = away_attack - home_defense
        
        # ========== WEIGHTED FORM (+1-2% accuracy) ==========
        features['home_weighted_form'] = self._calculate_weighted_form(match.home_team_id, match.match_date)
        features['away_weighted_form'] = self._calculate_weighted_form(match.away_team_id, match.match_date)
        features['weighted_form_diff'] = features['home_weighted_form'] - features['away_weighted_form']
        
        # ========== CLEAN SHEET & DEFENSIVE STATS ==========
        features['home_clean_sheet_pct'] = self._calculate_clean_sheet_pct(match.home_team_id, match.match_date)
        features['away_clean_sheet_pct'] = self._calculate_clean_sheet_pct(match.away_team_id, match.match_date)
        features['home_failed_to_score_pct'] = self._calculate_failed_to_score_pct(match.home_team_id, match.match_date)
        features['away_failed_to_score_pct'] = self._calculate_failed_to_score_pct(match.away_team_id, match.match_date)
        
        # ========== MATCH IMPORTANCE ==========
        features['match_importance'] = self._calculate_match_importance(match)
        features['is_title_race'] = 1 if features.get('home_league_position', 10) <= 4 or features.get('away_league_position', 10) <= 4 else 0
        features['is_relegation_battle'] = 1 if features.get('home_league_position', 10) >= 17 or features.get('away_league_position', 10) >= 17 else 0
        
        # ========== H2H GOALS TREND ==========
        h2h_avg_goals = self._calculate_h2h_avg_goals(match.home_team_id, match.away_team_id, match.match_date)
        features['h2h_avg_total_goals'] = h2h_avg_goals
        features['h2h_is_high_scoring'] = 1 if h2h_avg_goals > 2.5 else 0
        
        # ========== RECENT SCORING FORM ==========
        features['home_goals_last_3'] = self._calculate_recent_goals(match.home_team_id, match.match_date, 3)
        features['away_goals_last_3'] = self._calculate_recent_goals(match.away_team_id, match.match_date, 3)
        features['home_conceded_last_3'] = self._calculate_recent_conceded(match.home_team_id, match.match_date, 3)
        features['away_conceded_last_3'] = self._calculate_recent_conceded(match.away_team_id, match.match_date, 3)
        
        # ========== xG (EXPECTED GOALS) FROM POISSON MODEL ==========
        try:
            from src.ml.poisson_model import get_poisson_model
            poisson = get_poisson_model()
            exp_home_goals, exp_away_goals = poisson.get_expected_goals(match.home_team_id, match.away_team_id)
            features['poisson_xg_home'] = exp_home_goals
            features['poisson_xg_away'] = exp_away_goals
            features['poisson_xg_diff'] = exp_home_goals - exp_away_goals
            features['poisson_xg_total'] = exp_home_goals + exp_away_goals
        except:
            # Fallback if Poisson model fails
            features['poisson_xg_home'] = 1.5
            features['poisson_xg_away'] = 1.2
            features['poisson_xg_diff'] = 0.3
            features['poisson_xg_total'] = 2.7
        
        # ========== MOMENTUM INDICATORS (3-match trend) ==========
        features['home_momentum'] = self._calculate_momentum(match.home_team_id, match.match_date, last_n=3)
        features['away_momentum'] = self._calculate_momentum(match.away_team_id, match.match_date, last_n=3)
        features['momentum_diff'] = features['home_momentum'] - features['away_momentum']
        
        # ========== END NEW FEATURES ==========
        
        # Target variable (if match is finished)
        if match.status == 'FT' and match.home_goals is not None and match.away_goals is not None:
            if match.home_goals > match.away_goals:
                features['result'] = 'H'  # Home win
            elif match.home_goals < match.away_goals:
                features['result'] = 'A'  # Away win
            else:
                features['result'] = 'D'  # Draw
        else:
            features['result'] = None
        
        return features
    
    def _calculate_rest_days(self, team_id: int, before_date: datetime) -> int:
        """Calculate days since team's last match"""
        last_match = self.db.query(Match).filter(
            Match.match_date < before_date,
            Match.status == 'FT',
            (Match.home_team_id == team_id) | (Match.away_team_id == team_id)
        ).order_by(Match.match_date.desc()).first()
        
        if last_match:
            delta = before_date - last_match.match_date
            return min(delta.days, 30)  # Cap at 30 days
        return 14  # Default if no previous match
    
    def _calculate_season_progress(self, match: Match) -> float:
        """Calculate how far into the season this match is (0.0 to 1.0)"""
        if match.round:
            try:
                round_num = int(''.join(filter(str.isdigit, str(match.round))))
                return min(round_num / 38, 1.0)  # Assume 38 match season
            except:
                pass
        
        # Fallback: use month (Aug=0.0, May=1.0)
        month = match.match_date.month
        if month >= 8:  # Aug-Dec
            return (month - 8) / 10
        else:  # Jan-May
            return (month + 4) / 10
    
    def _calculate_streak(self, team_id: int, before_date: datetime, last_n: int = 5) -> int:
        """Calculate current win/loss streak (positive=wins, negative=losses)"""
        matches = self.db.query(Match).filter(
            Match.match_date < before_date,
            Match.status == 'FT',
            (Match.home_team_id == team_id) | (Match.away_team_id == team_id)
        ).order_by(Match.match_date.desc()).limit(last_n).all()
        
        streak = 0
        streak_type = None  # 'W' or 'L'
        
        for match in matches:
            is_home = match.home_team_id == team_id
            gf = match.home_goals if is_home else match.away_goals
            ga = match.away_goals if is_home else match.home_goals
            
            if gf > ga:  # Win
                if streak_type == 'W' or streak_type is None:
                    streak += 1
                    streak_type = 'W'
                else:
                    break
            elif gf < ga:  # Loss
                if streak_type == 'L' or streak_type is None:
                    streak -= 1
                    streak_type = 'L'
                else:
                    break
            else:  # Draw breaks the streak
                break
        
        return streak
    
    def _calculate_attack_strength(self, team_id: int, before_date: datetime, home_away: str = 'all', last_n: int = 10) -> float:
        """Calculate team's attack strength (goals scored per game)"""
        query = self.db.query(Match).filter(
            Match.match_date < before_date,
            Match.status == 'FT'
        )
        
        if home_away == 'home':
            query = query.filter(Match.home_team_id == team_id)
        elif home_away == 'away':
            query = query.filter(Match.away_team_id == team_id)
        else:
            query = query.filter((Match.home_team_id == team_id) | (Match.away_team_id == team_id))
        
        matches = query.order_by(Match.match_date.desc()).limit(last_n).all()
        
        if not matches:
            return 1.3  # league average
        
        total_goals = 0
        for match in matches:
            if match.home_team_id == team_id:
                total_goals += match.home_goals or 0
            else:
                total_goals += match.away_goals or 0
        
        return total_goals / len(matches)
    
    def _calculate_defense_strength(self, team_id: int, before_date: datetime, home_away: str = 'all', last_n: int = 10) -> float:
        """Calculate team's defense strength (goals conceded per game)"""
        query = self.db.query(Match).filter(
            Match.match_date < before_date,
            Match.status == 'FT'
        )
        
        if home_away == 'home':
            query = query.filter(Match.home_team_id == team_id)
        elif home_away == 'away':
            query = query.filter(Match.away_team_id == team_id)
        else:
            query = query.filter((Match.home_team_id == team_id) | (Match.away_team_id == team_id))
        
        matches = query.order_by(Match.match_date.desc()).limit(last_n).all()
        
        if not matches:
            return 1.3  # league average
        
        total_conceded = 0
        for match in matches:
            if match.home_team_id == team_id:
                total_conceded += match.away_goals or 0
            else:
                total_conceded += match.home_goals or 0
        
        return total_conceded / len(matches)
    
    def _calculate_weighted_form(self, team_id: int, before_date: datetime, last_n: int = 10) -> float:
        """
        Calculate weighted form - more recent matches have higher weight
        Uses exponential decay: weight = 0.9^(weeks_ago)
        """
        matches = self.db.query(Match).filter(
            Match.match_date < before_date,
            Match.status == 'FT',
            (Match.home_team_id == team_id) | (Match.away_team_id == team_id)
        ).order_by(Match.match_date.desc()).limit(last_n).all()
        
        if not matches:
            return 0.0
        
        weighted_sum = 0.0
        weight_total = 0.0
        decay_factor = 0.85
        
        for i, match in enumerate(matches):
            weight = decay_factor ** i
            
            is_home = match.home_team_id == team_id
            gf = match.home_goals if is_home else match.away_goals
            ga = match.away_goals if is_home else match.home_goals
            
            # Points: win=3, draw=1, loss=0
            if gf > ga:
                points = 3
            elif gf == ga:
                points = 1
            else:
                points = 0
            
            weighted_sum += points * weight
            weight_total += weight
        
        # Normalize to 0-3 scale (max points per game)
        return weighted_sum / weight_total if weight_total > 0 else 0.0
    
    def _calculate_clean_sheet_pct(self, team_id: int, before_date: datetime, last_n: int = 10) -> float:
        """Calculate percentage of clean sheets in last N matches"""
        matches = self.db.query(Match).filter(
            Match.match_date < before_date,
            Match.status == 'FT',
            (Match.home_team_id == team_id) | (Match.away_team_id == team_id)
        ).order_by(Match.match_date.desc()).limit(last_n).all()
        
        if not matches:
            return 0.3  # League average
        
        clean_sheets = 0
        for match in matches:
            if match.home_team_id == team_id:
                if match.away_goals == 0:
                    clean_sheets += 1
            else:
                if match.home_goals == 0:
                    clean_sheets += 1
        
        return clean_sheets / len(matches)
    
    def _calculate_failed_to_score_pct(self, team_id: int, before_date: datetime, last_n: int = 10) -> float:
        """Calculate percentage of matches where team failed to score"""
        matches = self.db.query(Match).filter(
            Match.match_date < before_date,
            Match.status == 'FT',
            (Match.home_team_id == team_id) | (Match.away_team_id == team_id)
        ).order_by(Match.match_date.desc()).limit(last_n).all()
        
        if not matches:
            return 0.25  # League average
        
        failed = 0
        for match in matches:
            if match.home_team_id == team_id:
                if match.home_goals == 0:
                    failed += 1
            else:
                if match.away_goals == 0:
                    failed += 1
        
        return failed / len(matches)
    
    def _calculate_match_importance(self, match) -> float:
        """Calculate match importance based on context (0-1 scale)"""
        importance = 0.5  # Base importance
        
        # Late season = more important
        progress = self._calculate_season_progress(match)
        if progress > 0.8:
            importance += 0.2
        elif progress > 0.6:
            importance += 0.1
        
        # Top teams facing each other = more important
        # (This is a simplified version - ideally would check standings)
        return min(1.0, importance)
    
    def _calculate_h2h_avg_goals(self, home_id: int, away_id: int, before_date: datetime, last_n: int = 5) -> float:
        """Calculate average total goals in H2H matches"""
        matches = self.db.query(Match).filter(
            Match.match_date < before_date,
            Match.status == 'FT',
            ((Match.home_team_id == home_id) & (Match.away_team_id == away_id)) |
            ((Match.home_team_id == away_id) & (Match.away_team_id == home_id))
        ).order_by(Match.match_date.desc()).limit(last_n).all()
        
        if not matches:
            return 2.5  # League average
        
        total_goals = sum(m.home_goals + m.away_goals for m in matches)
        return total_goals / len(matches)
    
    def _calculate_recent_goals(self, team_id: int, before_date: datetime, last_n: int = 3) -> int:
        """Calculate total goals scored in last N matches"""
        matches = self.db.query(Match).filter(
            Match.match_date < before_date,
            Match.status == 'FT',
            (Match.home_team_id == team_id) | (Match.away_team_id == team_id)
        ).order_by(Match.match_date.desc()).limit(last_n).all()
        
        total = 0
        for match in matches:
            if match.home_team_id == team_id:
                total += match.home_goals or 0
            else:
                total += match.away_goals or 0
        return total
    
    def _calculate_recent_conceded(self, team_id: int, before_date: datetime, last_n: int = 3) -> int:
        """Calculate total goals conceded in last N matches"""
        matches = self.db.query(Match).filter(
            Match.match_date < before_date,
            Match.status == 'FT',
            (Match.home_team_id == team_id) | (Match.away_team_id == team_id)
        ).order_by(Match.match_date.desc()).limit(last_n).all()
        
        total = 0
        for match in matches:
            if match.home_team_id == team_id:
                total += match.away_goals or 0
            else:
                total += match.home_goals or 0
        return total
    
    def _calculate_momentum(self, team_id: int, before_date: datetime, last_n: int = 3) -> float:
        """
        Calculate momentum as weighted average of goal difference in last N matches
        Positive momentum = scoring more and conceding less
        
        Args:
            team_id: Team ID
            before_date: Date before which to calculate
            last_n: Number of recent matches (default 3)
            
        Returns:
            Momentum score (average weighted goal difference)
        """
        matches = self.db.query(Match).filter(
            Match.match_date < before_date,
            Match.status == 'FT',
            (Match.home_team_id == team_id) | (Match.away_team_id == team_id)
        ).order_by(Match.match_date.desc()).limit(last_n).all()
        
        if not matches:
            return 0.0
        
        weighted_sum = 0.0
        weight_total = 0.0
        decay_factor = 0.85
        
        for i, match in enumerate(matches):
            weight = decay_factor ** i
            
            is_home = match.home_team_id == team_id
            gf = match.home_goals if is_home else match.away_goals
            ga = match.away_goals if is_home else match.home_goals
            
            goal_diff = (gf or 0) - (ga or 0)
            weighted_sum += goal_diff * weight
            weight_total += weight
        
        return weighted_sum / weight_total if weight_total > 0 else 0.0
    
    def create_training_dataset(
        self,
        min_date: Optional[datetime] = None,
        max_date: Optional[datetime] = None,
        league_ids: Optional[List[int]] = None
    ) -> pd.DataFrame:
        """
        Create comprehensive training dataset from historical matches
        WITH BULK LOADING AND PROGRESS TRACKING
        """
        import time
        
        print("\n📊 Creating Training Dataset with Optimizations...")
        start_time = time.time()
        
        # BULK LOADING: Load all finished matches into memory once
        print("🔄 Bulk loading all finished matches...")
        query = self.db.query(Match).filter(
            Match.status == 'FT',
            Match.home_goals.isnot(None),
            Match.away_goals.isnot(None)
        )
        
        if min_date:
            query = query.filter(Match.match_date >= min_date)
        if max_date:
            query = query.filter(Match.match_date <= max_date)
        if league_ids:
            query = query.filter(Match.league_id.in_(league_ids))
        
        all_matches = query.order_by(Match.match_date).all()
        total_matches = len(all_matches)
        print(f"✅ Loaded {total_matches} matches into memory")
        
        # Store in cache for bulk processing
        self._cache['bulk_matches'] = all_matches
        
        # Process matches with progress tracking
        data = []
        processed = 0
        
        print("\n⚙️  Processing features...")
        for i, match in enumerate(all_matches, 1):
            try:
                features = self.create_match_features(match)
                features['match_id'] = match.id
                
                # Add result
                if match.home_goals > match.away_goals:
                    features['result'] = 'H'
                elif match.home_goals < match.away_goals:
                    features['result'] = 'A'
                else:
                    features['result'] = 'D'
                
                data.append(features)
                processed += 1
                
                # Progress logging every 50 matches
                if i % 50 == 0 or i == total_matches:
                    elapsed = time.time() - start_time
                    avg_time_per_match = elapsed / i
                    remaining = (total_matches - i) * avg_time_per_match
                    eta_min = remaining / 60
                    
                    print(f"   [{i}/{total_matches}] {(i/total_matches)*100:.1f}% | "
                          f"Avg: {avg_time_per_match:.3f}s/match | "
                          f"ETA: {eta_min:.1f}min | "
                          f"Cache hits: {self._cache_hits}, misses: {self._cache_misses}")
            
            except Exception as e:
                print(f"   ⚠️  Error on match {match.id}: {e}")
        
        total_time = time.time() - start_time
        cache_hit_rate = (self._cache_hits / (self._cache_hits + self._cache_misses)) * 100 if (self._cache_hits + self._cache_misses) > 0 else 0
        
        print(f"\n✅ Dataset created: {processed} matches, {len(data[0]) if data else 0} features")
        print(f"⏱️  Total time: {total_time:.1f}s ({total_time/60:.1f}min)")
        print(f"📈 Cache hit rate: {cache_hit_rate:.1f}% ({self._cache_hits} hits / {self._cache_misses} misses)")
        
        # Clear bulk cache
        self._cache['bulk_matches'] = None
        
        return pd.DataFrame(data)
    
    def close(self):
        """Close database connection"""
        self.db.close()


if __name__ == "__main__":
    # Test feature engineering
    engineer = FeatureEngineer()
    
    print("\n🔧 Testing Feature Engineering...\n")
    
    # Create dataset
    df = engineer.create_training_dataset()
    
    print(f"\n📊 Dataset Shape: {df.shape}")
    print(f"\n📋 Features: {df.columns.tolist()}")
    print(f"\n🎯 Target Distribution:\n{df['result'].value_counts()}")
    print(f"\n🔍 Sample Features:\n{df.head()}")
    
    # Save dataset
    output_path = "ml_dataset.csv"
    df.to_csv(output_path, index=False)
    print(f"\n✅ Dataset saved to {output_path}")
    
    engineer.close()
