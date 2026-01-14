"""
Accuracy Tracker for Model Monitoring
Compares predictions to actual results and tracks performance over time.
"""
import sys
import os
from datetime import datetime
from typing import Dict, List, Optional
import pandas as pd

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from src.models.database import SessionLocal, Match, Prediction


class AccuracyTracker:
    """Track and analyze prediction accuracy"""
    
    def __init__(self):
        self.db = SessionLocal()
    
    def get_finished_predictions(self) -> List[Dict]:
        """Get all predictions for finished matches"""
        predictions = self.db.query(Prediction).join(Match).filter(
            Match.status == 'FT',
            Match.home_goals.isnot(None),
            Match.away_goals.isnot(None)
        ).all()
        
        results = []
        for pred in predictions:
            match = pred.match
            
            # Actual result
            if match.home_goals > match.away_goals:
                actual = 'H'
            elif match.home_goals < match.away_goals:
                actual = 'A'
            else:
                actual = 'D'
            
            # Check if correct
            is_correct = pred.predicted_result == actual
            
            # BTTS actual
            actual_btts = match.home_goals > 0 and match.away_goals > 0
            btts_correct = pred.btts_prediction == (1 if actual_btts else 0)
            
            # Over 2.5 actual
            total_goals = match.home_goals + match.away_goals
            actual_over_25 = total_goals > 2.5
            over_25_correct = pred.over_25_prediction == (1 if actual_over_25 else 0)
            
            results.append({
                'match_id': match.id,
                'match_date': match.match_date,
                'predicted': pred.predicted_result,
                'actual': actual,
                'confidence': pred.confidence,
                'is_correct': is_correct,
                'btts_correct': btts_correct,
                'over_25_correct': over_25_correct,
                'total_goals': total_goals,
                'model_version': pred.model_version
            })
        
        return results
    
    def calculate_accuracy(self) -> Dict:
        """Calculate overall accuracy metrics"""
        results = self.get_finished_predictions()
        
        if not results:
            return {'error': 'No finished predictions found'}
        
        total = len(results)
        correct_1x2 = sum(1 for r in results if r['is_correct'])
        correct_btts = sum(1 for r in results if r['btts_correct'])
        correct_over25 = sum(1 for r in results if r['over_25_correct'])
        
        return {
            'total_predictions': total,
            '1x2_accuracy': correct_1x2 / total if total > 0 else 0,
            '1x2_correct': correct_1x2,
            'btts_accuracy': correct_btts / total if total > 0 else 0,
            'btts_correct': correct_btts,
            'over_25_accuracy': correct_over25 / total if total > 0 else 0,
            'over_25_correct': correct_over25
        }
    
    def accuracy_by_confidence(self, min_confidence: float = 0.4) -> Dict:
        """Group accuracy by confidence levels"""
        results = self.get_finished_predictions()
        
        confidence_bins = {
            'low (40-50%)': {'range': (0.4, 0.5), 'correct': 0, 'total': 0},
            'medium (50-60%)': {'range': (0.5, 0.6), 'correct': 0, 'total': 0},
            'high (60-70%)': {'range': (0.6, 0.7), 'correct': 0, 'total': 0},
            'very_high (70%+)': {'range': (0.7, 1.0), 'correct': 0, 'total': 0}
        }
        
        for r in results:
            conf = r['confidence']
            for bin_name, bin_data in confidence_bins.items():
                if bin_data['range'][0] <= conf < bin_data['range'][1]:
                    bin_data['total'] += 1
                    if r['is_correct']:
                        bin_data['correct'] += 1
                    break
        
        return {
            name: {
                'total': data['total'],
                'correct': data['correct'],
                'accuracy': data['correct'] / data['total'] if data['total'] > 0 else 0
            }
            for name, data in confidence_bins.items()
        }
    
    def accuracy_by_model_version(self) -> Dict:
        """Group accuracy by model version"""
        results = self.get_finished_predictions()
        
        by_version = {}
        for r in results:
            version = r['model_version'] or 'unknown'
            if version not in by_version:
                by_version[version] = {'correct': 0, 'total': 0}
            by_version[version]['total'] += 1
            if r['is_correct']:
                by_version[version]['correct'] += 1
        
        return {
            version: {
                'total': data['total'],
                'correct': data['correct'],
                'accuracy': data['correct'] / data['total'] if data['total'] > 0 else 0
            }
            for version, data in by_version.items()
        }
    
    def get_calibration(self) -> Dict:
        """
        Check if predictions are well-calibrated.
        E.g., predictions with 70% confidence should be correct ~70% of time.
        """
        results = self.get_finished_predictions()
        
        if not results:
            return {}
        
        # Group by rounded confidence
        calibration = {}
        for r in results:
            conf_bucket = round(r['confidence'], 1)  # Round to 10%
            if conf_bucket not in calibration:
                calibration[conf_bucket] = {'correct': 0, 'total': 0}
            calibration[conf_bucket]['total'] += 1
            if r['is_correct']:
                calibration[conf_bucket]['correct'] += 1
        
        return {
            conf: {
                'expected': conf,
                'actual': data['correct'] / data['total'] if data['total'] > 0 else 0,
                'sample_size': data['total'],
                'calibration_error': abs(conf - (data['correct'] / data['total'] if data['total'] > 0 else 0))
            }
            for conf, data in sorted(calibration.items())
        }
    
    def print_report(self):
        """Print a comprehensive accuracy report"""
        print("\n" + "="*60)
        print("📊 PREDICTION ACCURACY REPORT")
        print("="*60)
        
        # Overall accuracy
        accuracy = self.calculate_accuracy()
        if 'error' in accuracy:
            print(f"\n⚠️ {accuracy['error']}")
            return
        
        print(f"\n📈 Overall Performance ({accuracy['total_predictions']} predictions)")
        print(f"   1X2 Accuracy:    {accuracy['1x2_accuracy']:.1%} ({accuracy['1x2_correct']}/{accuracy['total_predictions']})")
        print(f"   BTTS Accuracy:   {accuracy['btts_accuracy']:.1%} ({accuracy['btts_correct']}/{accuracy['total_predictions']})")
        print(f"   Over 2.5:        {accuracy['over_25_accuracy']:.1%} ({accuracy['over_25_correct']}/{accuracy['total_predictions']})")
        
        # By confidence
        print("\n📊 Accuracy by Confidence Level:")
        by_conf = self.accuracy_by_confidence()
        for level, data in by_conf.items():
            if data['total'] > 0:
                print(f"   {level}: {data['accuracy']:.1%} ({data['correct']}/{data['total']})")
        
        # Calibration
        print("\n🎯 Calibration Check (is 60% confidence actually 60% correct?):")
        calibration = self.get_calibration()
        for conf, data in calibration.items():
            if data['sample_size'] >= 5:  # Only show if enough samples
                print(f"   {conf:.0%} confidence: {data['actual']:.1%} actual (n={data['sample_size']})")
        
        print("\n" + "="*60)
    
    def close(self):
        self.db.close()


if __name__ == "__main__":
    tracker = AccuracyTracker()
    tracker.print_report()
    tracker.close()
