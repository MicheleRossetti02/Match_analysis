"""
Prediction Accuracy Service
Compares predictions with actual match results and calculates accuracy metrics
"""
from typing import Optional
from sqlalchemy.orm import Session
from src.models.database import Match, Prediction


class PredictionAccuracyService:
    """Service to update predictions with actual results and calculate accuracy"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def calculate_bet_outcomes(self, home_goals: int, away_goals: int) -> dict:
        """
        Calculate actual outcomes for all bet types based on match score
        
        Args:
            home_goals: Number of goals scored by home team
            away_goals: Number of goals scored by away team
            
        Returns:
            Dictionary with actual outcomes for all bet types
        """
        total_goals = home_goals + away_goals
        
        # Determine match result (1X2)
        if home_goals > away_goals:
            result_1x2 = 'H'  # Home win
        elif home_goals < away_goals:
            result_1x2 = 'A'  # Away win
        else:
            result_1x2 = 'D'  # Draw
        
        # Calculate other bet outcomes
        btts = home_goals > 0 and away_goals > 0  # Both teams scored
        over_15 = total_goals > 1.5  # Over 1.5 goals
        over_25 = total_goals > 2.5  # Over 2.5 goals
        over_35 = total_goals > 3.5  # Over 3.5 goals
        
        return {
            'result_1x2': result_1x2,
            'btts': btts,
            'over_15': over_15,
            'over_25': over_25,
            'over_35': over_35,
            'total_goals': total_goals
        }
    
    def update_prediction_accuracy(self, prediction: Prediction, match: Match) -> Prediction:
        """
        Update a prediction with actual results and calculate accuracy
        
        Args:
            prediction: Prediction object to update
            match: Match object with actual results
            
        Returns:
            Updated prediction object
        """
        # Ensure match has results
        if match.home_goals is None or match.away_goals is None:
            return prediction
        
        # Calculate actual outcomes
        outcomes = self.calculate_bet_outcomes(match.home_goals, match.away_goals)
        
        # Update 1X2 prediction accuracy
        prediction.actual_result = outcomes['result_1x2']
        prediction.is_correct = (prediction.predicted_result == outcomes['result_1x2'])
        
        # Update BTTS accuracy
        if prediction.btts_prediction is not None:
            prediction.btts_actual = outcomes['btts']
            prediction.btts_correct = (prediction.btts_prediction == outcomes['btts'])
        
        # Update Over/Under 1.5 accuracy
        if prediction.over_15_prediction is not None:
            prediction.over_15_actual = outcomes['over_15']
            prediction.over_15_correct = (prediction.over_15_prediction == outcomes['over_15'])
        
        # Update Over/Under 2.5 accuracy
        if prediction.over_25_prediction is not None:
            prediction.over_25_actual = outcomes['over_25']
            prediction.over_25_correct = (prediction.over_25_prediction == outcomes['over_25'])
        
        # Update Over/Under 3.5 accuracy
        if prediction.over_35_prediction is not None:
            prediction.over_35_actual = outcomes['over_35']
            prediction.over_35_correct = (prediction.over_35_prediction == outcomes['over_35'])
        
        return prediction
    
    def update_all_finished_matches(self) -> dict:
        """
        Update all predictions for finished matches that don't have actual results yet
        
        Returns:
            Dictionary with update statistics
        """
        # Find all finished matches with predictions that don't have actual results
        from sqlalchemy import and_
        
        matches_to_update = (
            self.db.query(Match)
            .join(Prediction, Match.id == Prediction.match_id)
            .filter(
                and_(
                    Match.status == 'FT',  # Match is finished
                    Match.home_goals.isnot(None),  # Has score data
                    Match.away_goals.isnot(None),
                    Prediction.actual_result.is_(None)  # Prediction not yet updated
                )
            )
            .distinct()
            .all()
        )
        
        updated_count = 0
        for match in matches_to_update:
            # Get all predictions for this match
            predictions = (
                self.db.query(Prediction)
                .filter(Prediction.match_id == match.id)
                .all()
            )
            
            for prediction in predictions:
                self.update_prediction_accuracy(prediction, match)
                updated_count += 1
        
        # Commit all updates
        self.db.commit()
        
        return {
            'matches_processed': len(matches_to_update),
            'predictions_updated': updated_count
        }
    
    def get_accuracy_stats(self) -> dict:
        """
        Calculate overall accuracy statistics across all predictions
        
        Returns:
            Dictionary with accuracy metrics for each bet type
        """
        # Get all predictions with actual results
        predictions = (
            self.db.query(Prediction)
            .filter(Prediction.actual_result.isnot(None))
            .all()
        )
        
        if not predictions:
            return {
                'total_predictions': 0,
                'accuracy_1x2': 0,
                'accuracy_btts': 0,
                'accuracy_over_15': 0,
                'accuracy_over_25': 0,
                'accuracy_over_35': 0
            }
        
        # Calculate 1X2 accuracy
        total_1x2 = len(predictions)
        correct_1x2 = sum(1 for p in predictions if p.is_correct)
        
        # Calculate BTTS accuracy
        btts_predictions = [p for p in predictions if p.btts_prediction is not None]
        total_btts = len(btts_predictions)
        correct_btts = sum(1 for p in btts_predictions if p.btts_correct)
        
        # Calculate Over/Under 1.5 accuracy
        over_15_predictions = [p for p in predictions if p.over_15_prediction is not None]
        total_over_15 = len(over_15_predictions)
        correct_over_15 = sum(1 for p in over_15_predictions if p.over_15_correct)
        
        # Calculate Over/Under 2.5 accuracy
        over_25_predictions = [p for p in predictions if p.over_25_prediction is not None]
        total_over_25 = len(over_25_predictions)
        correct_over_25 = sum(1 for p in over_25_predictions if p.over_25_correct)
        
        # Calculate Over/Under 3.5 accuracy
        over_35_predictions = [p for p in predictions if p.over_35_prediction is not None]
        total_over_35 = len(over_35_predictions)
        correct_over_35 = sum(1 for p in over_35_predictions if p.over_35_correct)
        
        return {
            'total_predictions': total_1x2,
            'accuracy_1x2': {
                'correct': correct_1x2,
                'total': total_1x2,
                'percentage': round((correct_1x2 / total_1x2 * 100) if total_1x2 > 0 else 0, 2)
            },
            'accuracy_btts': {
                'correct': correct_btts,
                'total': total_btts,
                'percentage': round((correct_btts / total_btts * 100) if total_btts > 0 else 0, 2)
            },
            'accuracy_over_15': {
                'correct': correct_over_15,
                'total': total_over_15,
                'percentage': round((correct_over_15 / total_over_15 * 100) if total_over_15 > 0 else 0, 2)
            },
            'accuracy_over_25': {
                'correct': correct_over_25,
                'total': total_over_25,
                'percentage': round((correct_over_25 / total_over_25 * 100) if total_over_25 > 0 else 0, 2)
            },
            'accuracy_over_35': {
                'correct': correct_over_35,
                'total': total_over_35,
                'percentage': round((correct_over_35 / total_over_35 * 100) if total_over_35 > 0 else 0, 2)
            }
        }
