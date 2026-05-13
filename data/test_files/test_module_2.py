
# Test Module 2 - Machine Learning utilities
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, precision_score, recall_score

class MLModel:
    """Machine Learning model wrapper for classification tasks.
    
    This class provides a unified interface for:
    - Model training and evaluation
    - Hyperparameter tuning
    - Cross-validation
    - Feature engineering
    
    Attributes:
        model: The underlying ML model
        scaler: Feature scaling transformer
        feature_names: List of feature column names
    """
    
    def __init__(self, model_type: str = 'random_forest'):
        self.model_type = model_type
        self.model = self._initialize_model()
        self.scaler = StandardScaler()
        self.feature_names = []
        
    def _initialize_model(self):
        """Initialize the ML model based on type."""
        from sklearn.ensemble import RandomForestClassifier
        from sklearn.linear_model import LogisticRegression
        
        models = {
            'random_forest': RandomForestClassifier(n_estimators=100),
            'logistic': LogisticRegression(max_iter=1000)
        }
        return models.get(self.model_type, RandomForestClassifier())
    
    def train(self, X: np.ndarray, y: np.ndarray) -> Dict:
        """Train the model on provided data."""
        X_scaled = self.scaler.fit_transform(X)
        self.model.fit(X_scaled, y)
        return {'status': 'trained', 'samples': len(X)}
    
    def predict(self, X: np.ndarray) -> np.ndarray:
        """Make predictions on new data."""
        X_scaled = self.scaler.transform(X)
        return self.model.predict(X_scaled)
    
    def evaluate(self, X: np.ndarray, y: np.ndarray) -> Dict:
        """Evaluate model performance."""
        predictions = self.predict(X)
        return {
            'accuracy': accuracy_score(y, predictions),
            'precision': precision_score(y, predictions, average='weighted'),
            'recall': recall_score(y, predictions, average='weighted')
        }
