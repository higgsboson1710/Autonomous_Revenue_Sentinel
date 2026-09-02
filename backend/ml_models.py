import numpy as np
import xgboost as xgb
import pandas as pd
from typing import Dict, List

class CMABOptimizer:
    """
    Contextual Multi-Armed Bandit using Thompson Sampling.
    Used for determining the optimal retry timing (arms) for soft declines.
    """
    def __init__(self, n_arms: int = 3, n_features: int = 4):
        self.n_arms = n_arms
        self.n_features = n_features
        # Initialize Bayesian priors (means and covariance matrices for each arm)
        self.m = np.zeros((n_arms, n_features))
        self.q = np.ones((n_arms, n_features)) # simplified variance

    def choose_arm(self, context_vector: np.ndarray) -> int:
        """
        Choose the best retry window using Thompson Sampling.
        Arms might represent: [24_hours, 72_hours, 168_hours]
        """
        sampled_rewards = np.zeros(self.n_arms)
        for arm in range(self.n_arms):
            # Sample coefficients from normal distribution defined by priors
            theta_sample = np.random.normal(self.m[arm], 1.0 / np.sqrt(self.q[arm]))
            sampled_rewards[arm] = np.dot(theta_sample, context_vector)
            
        return int(np.argmax(sampled_rewards))

    def update(self, arm: int, context_vector: np.ndarray, reward: float):
        """
        Update the Bayesian posteriors after observing the result of a retry.
        """
        # Simplified update rule
        self.q[arm] += context_vector ** 2
        self.m[arm] += (reward - np.dot(self.m[arm], context_vector)) * context_vector / self.q[arm]


import os

class ChurnPredictor:
    """
    XGBoost classifier to predict probability of involuntary churn.
    """
    def __init__(self):
        self.model = xgb.Booster()
        model_path = os.path.join(os.path.dirname(__file__), 'xgboost_churn_model.json')
        if os.path.exists(model_path):
            self.model.load_model(model_path)
            self.is_trained = True
        else:
            self.is_trained = False
            print("Warning: xgboost_churn_model.json not found. Run train_model.py first! Falling back to heuristic.")

    def predict_churn_probability(self, user_features: Dict[str, float]) -> float:
        """
        Predicts churn risk. High risk (>0.7) skips silent retries and sends a discounted Payment Link.
        """
        if not self.is_trained:
            # Fallback heuristic logic if the model isn't trained yet
            hist_failure_rate = user_features.get("SupportTicketsPerMonth", 0.0) / 10.0
            return min(hist_failure_rate * 1.5, 0.99)
            
        # Ensure all expected features are present in the correct order for the model
        expected_features = ['AccountAge', 'MonthlyCharges', 'ViewingHoursPerWeek', 'SupportTicketsPerMonth', 'UserRating']
        for feat in expected_features:
            if feat not in user_features:
                user_features[feat] = 0.0 # Default value if missing
                
        df = pd.DataFrame([user_features])[expected_features]
        dmatrix = xgb.DMatrix(df)
        prob = self.model.predict(dmatrix)[0]
        return float(prob)

# Singleton instances to be used by the LangGraph agents
retry_optimizer = CMABOptimizer()
churn_model = ChurnPredictor()
