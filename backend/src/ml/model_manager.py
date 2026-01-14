"""
Model Manager for Loading and Managing ML Models
"""
import os
import json
import joblib
from typing import Optional, Dict
from datetime import datetime


class ModelManager:
    """Manage ML model loading and versioning"""
    
    def __init__(self, models_dir='models'):
        self.models_dir = models_dir
        self.current_model = None
        self.current_scaler = None
        self.current_encoder = None
        self.current_config = None
    
    def list_models(self) -> list:
        """List all available models"""
        if not os.path.exists(self.models_dir):
            return []
        
        models = []
        for filename in os.listdir(self.models_dir):
            if filename.endswith('.pkl') and '_scaler' not in filename and '_encoder' not in filename:
                model_path = os.path.join(self.models_dir, filename)
                config_path = model_path.replace('.pkl', '_config.json')
                
                if os.path.exists(config_path):
                    with open(config_path, 'r') as f:
                        config = json.load(f)
                    models.append({
                        'path': model_path,
                        'filename': filename,
                        **config
                    })
        
        # Sort by version (most recent first)
        models.sort(key=lambda x: x.get('version', ''), reverse=True)
        return models
    
    def get_best_model(self, model_type: Optional[str] = None):
        """Get path to best performing model"""
        models = self.list_models()
        
        if model_type:
            models = [m for m in models if m.get('model_type') == model_type]
        
        if not models:
            return None
        
        # Return most recent model (assumed to be best)
        return models[0]['path']
    
    def load_model(self, model_path: Optional[str] = None):
        """Load a model and its components"""
        if model_path is None:
            model_path = self.get_best_model()
        
        if model_path is None:
            raise ValueError("No models available")
        
        print(f"Loading model from {model_path}...")
        
        # Load model
        self.current_model = joblib.load(model_path)
        
        # Load scaler and encoder
        base_name = os.path.basename(model_path).replace('.pkl', '')
        directory = os.path.dirname(model_path)
        
        scaler_path = os.path.join(directory, f'{base_name}_scaler.pkl')
        encoder_path = os.path.join(directory, f'{base_name}_encoder.pkl')
        config_path = os.path.join(directory, f'{base_name}_config.json')
        
        self.current_scaler = joblib.load(scaler_path)
        self.current_encoder = joblib.load(encoder_path)
        
        with open(config_path, 'r') as f:
            self.current_config = json.load(f)
        
        print(f"✅ Loaded {self.current_config['model_type']} model version {self.current_config['version']}")
        
        return self
    
    def predict(self, features: Dict) -> Dict:
        """Make prediction for a match"""
        if self.current_model is None:
            raise ValueError("No model loaded. Call load_model() first.")
        
        # Prepare features in correct order
        feature_values = [features.get(f, 0) for f in self.current_config['feature_names']]
        
        # Scale
        import numpy as np
        X = np.array(feature_values).reshape(1, -1)
        X_scaled = self.current_scaler.transform(X)
        
        # Predict
        prediction = self.current_model.predict(X_scaled)[0]
        probas = self.current_model.predict_proba(X_scaled)[0]
        
        # Decode
        result = self.current_encoder.inverse_transform([prediction])[0]
        
        # Map probabilities to classes
        proba_dict = {}
        for i, class_name in enumerate(self.current_encoder.classes_):
            proba_dict[class_name] = float(probas[i])
        
        return {
            'predicted_result': result,
            'probabilities': proba_dict,
            'confidence': float(max(probas)),
            'model_version': self.current_config['version'],
            'model_type': self.current_config['model_type']
        }


if __name__ == "__main__":
    # Test model manager
    manager = ModelManager()
    
    print("\n📦 Available Models:")
    for model in manager.list_models():
        print(f"  - {model['model_type']} v{model['version']}")
    
    print("\n🔧 Loading best model...")
    manager.load_model()
    
    print("\n✅ Model manager ready!")
