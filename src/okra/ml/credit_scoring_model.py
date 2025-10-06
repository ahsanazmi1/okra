"""
Credit scoring ML model for Okra.

This module provides advanced credit scoring using XGBoost with calibration
for improved probability estimates.
"""

import os
import json
import joblib
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List
from datetime import datetime

import xgboost as xgb
from sklearn.calibration import CalibratedClassifierCV
from sklearn.metrics import classification_report, roc_auc_score, log_loss
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

from .feature_engineering import feature_store


class CreditScoringModel:
    """Advanced credit scoring ML model using XGBoost."""
    
    def __init__(self, model_dir: str = "models/credit_scoring"):
        """Initialize the credit scoring model."""
        self.model_dir = Path(model_dir)
        self.model_dir.mkdir(parents=True, exist_ok=True)
        
        self.model: Optional[xgb.XGBClassifier] = None
        self.calibrator: Optional[CalibratedClassifierCV] = None
        self.scaler: Optional[StandardScaler] = None
        self.feature_names: List[str] = []
        self.metadata: Dict[str, Any] = {}
        self.is_loaded = False
        
        # Try to load existing model
        self._load_model()
    
    def _load_model(self) -> bool:
        """Load existing model artifacts."""
        model_path = self.model_dir / "credit_scoring_model.pkl"
        scaler_path = self.model_dir / "credit_scoring_scaler.pkl"
        metadata_path = self.model_dir / "credit_scoring_metadata.json"
        
        try:
            if all(p.exists() for p in [model_path, scaler_path, metadata_path]):
                self.model = joblib.load(model_path)
                self.scaler = joblib.load(scaler_path)
                
                with open(metadata_path, 'r') as f:
                    self.metadata = json.load(f)
                
                self.feature_names = self.metadata.get('feature_names', [])
                self.is_loaded = True
                print(f"✅ Loaded credit scoring model from {self.model_dir}")
                return True
        except Exception as e:
            print(f"⚠️ Failed to load credit scoring model: {e}")
        
        return False
    
    def train_model(self, n_samples: int = 10000) -> Dict[str, Any]:
        """
        Train the credit scoring model with synthetic data.
        
        Args:
            n_samples: Number of training samples to generate
            
        Returns:
            Training metrics
        """
        print("🚀 Training credit scoring ML model...")
        
        # Generate synthetic training data
        X, y = self._generate_training_data(n_samples)
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
        
        # Scale features
        self.scaler = StandardScaler()
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        # Train XGBoost model
        self.model = xgb.XGBClassifier(
            n_estimators=200,
            max_depth=6,
            learning_rate=0.1,
            subsample=0.8,
            colsample_bytree=0.8,
            random_state=42,
            eval_metric='logloss',
            objective='binary:logistic'
        )
        
        self.model.fit(
            X_train_scaled, y_train,
            eval_set=[(X_test_scaled, y_test)],
            verbose=False
        )
        
        # Calibrate the model
        print("📊 Calibrating credit scoring model...")
        self.calibrator = CalibratedClassifierCV(
            self.model, method='isotonic', cv=3
        )
        self.calibrator.fit(X_train_scaled, y_train)
        
        # Evaluate model
        y_pred_proba = self.calibrator.predict_proba(X_test_scaled)[:, 1]
        y_pred = (y_pred_proba > 0.5).astype(int)
        
        # Calculate metrics
        auc_score = roc_auc_score(y_test, y_pred_proba)
        log_loss_score = log_loss(y_test, y_pred_proba)
        
        # Feature importance (convert numpy types to Python types for JSON serialization)
        feature_importance = dict(zip(
            self.feature_names, 
            [float(x) for x in self.model.feature_importances_]
        ))
        
        # Create metadata
        self.metadata = {
            'version': '1.0.0',
            'trained_on': datetime.now().isoformat(),
            'feature_names': self.feature_names,
            'feature_importance': feature_importance,
            'training_metrics': {
                'auc_score': float(auc_score),
                'log_loss': float(log_loss_score),
                'n_features': len(self.feature_names),
                'n_samples_train': len(X_train),
                'n_samples_test': len(X_test)
            },
            'model_parameters': {
                'n_estimators': 200,
                'max_depth': 6,
                'learning_rate': 0.1,
                'subsample': 0.8,
                'colsample_bytree': 0.8
            }
        }
        
        # Save model artifacts
        self._save_model()
        
        print(f"✅ Credit scoring model trained successfully!")
        print(f"📊 AUC Score: {auc_score:.4f}")
        print(f"📊 Log Loss: {log_loss_score:.4f}")
        
        return {
            'auc_score': auc_score,
            'log_loss': log_loss_score,
            'feature_importance': feature_importance,
            'training_samples': n_samples
        }
    
    def predict_credit_score(self, features: Dict[str, float]) -> Dict[str, Any]:
        """
        Predict credit score using the trained model.
        
        Args:
            features: Feature dictionary
            
        Returns:
            Prediction results with score and metadata
        """
        if not self.is_loaded:
            # Fallback to rule-based scoring
            return self._fallback_prediction(features)
        
        try:
            # Convert features to array
            feature_array = np.array([features.get(name, 0.0) for name in self.feature_names])
            feature_array = feature_array.reshape(1, -1)
            
            # Scale features
            feature_array_scaled = self.scaler.transform(feature_array)
            
            # Predict probability
            if self.calibrator:
                approval_probability = self.calibrator.predict_proba(feature_array_scaled)[0, 1]
            else:
                approval_probability = self.model.predict_proba(feature_array_scaled)[0, 1]
            
            # Convert probability to credit score (300-850 scale)
            credit_score = 300 + (approval_probability * 550)
            
            # Determine approval decision
            approval_decision = approval_probability > 0.6  # 60% threshold
            
            # Calculate risk level
            if approval_probability >= 0.8:
                risk_level = "low"
            elif approval_probability >= 0.6:
                risk_level = "medium"
            else:
                risk_level = "high"
            
            # Feature importance for this prediction
            feature_contributions = dict(zip(
                self.feature_names,
                self.model.feature_importances_
            ))
            
            return {
                'approval_probability': float(approval_probability),
                'credit_score': float(credit_score),
                'approval_decision': approval_decision,
                'risk_level': risk_level,
                'feature_contributions': feature_contributions,
                'model_version': self.metadata.get('version', '1.0.0'),
                'prediction_confidence': float(approval_probability),
                'model_type': 'xgboost_credit_scoring'
            }
            
        except Exception as e:
            print(f"⚠️ ML prediction failed: {e}")
            return self._fallback_prediction(features)
    
    def _generate_training_data(self, n_samples: int) -> Tuple[pd.DataFrame, pd.Series]:
        """Generate synthetic training data for credit scoring."""
        np.random.seed(42)
        
        data = []
        for _ in range(n_samples):
            # Generate realistic credit features
            credit_score = np.random.normal(650, 100)
            annual_income = np.random.lognormal(10.5, 0.5)  # Log-normal distribution
            dti_ratio = np.random.beta(2, 5)  # Beta distribution for DTI
            credit_history = np.random.exponential(60)  # Exponential for credit history
            
            # Generate employment status
            employment_status = np.random.choice([1.0, 0.8, 0.2, 0.6, 0.3], 
                                               p=[0.6, 0.2, 0.05, 0.1, 0.05])
            
            # Generate request features
            requested_amount = np.random.lognormal(9, 0.8)
            term_months = np.random.choice([12, 24, 36, 48, 60], p=[0.1, 0.2, 0.4, 0.2, 0.1])
            
            # Generate additional features
            velocity_12m = np.random.poisson(12)
            late_payments = np.random.poisson(1)
            credit_utilization = np.random.beta(2, 3)
            inquiries = np.random.poisson(2)
            bankruptcy = np.random.choice([0, 1], p=[0.95, 0.05])
            income_stability = np.random.beta(5, 2)
            geographic_risk = np.random.beta(2, 3)
            purpose_risk = np.random.beta(2, 3)
            
            # Create feature vector
            features = {
                'credit_score_normalized': min(max((credit_score - 300) / 550.0, 0.0), 1.0),
                'annual_income_log': np.log1p(annual_income),
                'debt_to_income_ratio': min(dti_ratio, 1.0),
                'credit_history_months_normalized': min(credit_history / 120.0, 1.0),
                'employment_status_encoded': employment_status,
                'requested_amount_log': np.log1p(requested_amount),
                'term_months_normalized': min(term_months / 60.0, 1.0),
                'velocity_12m': velocity_12m,
                'late_payments_12m': late_payments,
                'credit_utilization': credit_utilization,
                'inquiries_6m': inquiries,
                'bankruptcy_flag': bankruptcy,
                'income_stability': income_stability,
                'geographic_risk': geographic_risk,
                'purpose_risk': purpose_risk
            }
            
            data.append(features)
        
        # Convert to DataFrame
        df = pd.DataFrame(data)
        self.feature_names = df.columns.tolist()
        
        # Generate target variable (approval decision)
        # Higher credit score, lower DTI, stable employment = higher approval probability
        approval_probability = (
            df['credit_score_normalized'] * 0.3 +
            (1 - df['debt_to_income_ratio']) * 0.25 +
            df['employment_status_encoded'] * 0.2 +
            df['credit_history_months_normalized'] * 0.15 +
            (1 - df['bankruptcy_flag']) * 0.1
        )
        
        # Add some noise
        approval_probability += np.random.normal(0, 0.1, len(approval_probability))
        approval_probability = np.clip(approval_probability, 0, 1)
        
        # Convert to binary target
        y = (approval_probability > 0.5).astype(int)
        
        return df, y
    
    def _fallback_prediction(self, features: Dict[str, float]) -> Dict[str, Any]:
        """Fallback prediction using rule-based scoring."""
        credit_score_norm = features.get('credit_score_normalized', 0.6)
        dti_ratio = features.get('debt_to_income_ratio', 0.3)
        employment_status = features.get('employment_status_encoded', 0.8)
        
        # Simple rule-based scoring
        approval_probability = (
            credit_score_norm * 0.4 +
            (1 - dti_ratio) * 0.3 +
            employment_status * 0.3
        )
        
        credit_score = 300 + (approval_probability * 550)
        approval_decision = approval_probability > 0.6
        
        risk_level = "low" if approval_probability >= 0.8 else "medium" if approval_probability >= 0.6 else "high"
        
        return {
            'approval_probability': float(approval_probability),
            'credit_score': float(credit_score),
            'approval_decision': approval_decision,
            'risk_level': risk_level,
            'feature_contributions': {},
            'model_version': 'fallback-1.0.0',
            'prediction_confidence': 0.5,
            'model_type': 'rule_based_fallback'
        }
    
    def _save_model(self):
        """Save model artifacts."""
        if self.model and self.scaler:
            # Save model
            model_path = self.model_dir / "credit_scoring_model.pkl"
            joblib.dump(self.model, model_path)
            
            # Save scaler
            scaler_path = self.model_dir / "credit_scoring_scaler.pkl"
            joblib.dump(self.scaler, scaler_path)
            
            # Save metadata
            metadata_path = self.model_dir / "credit_scoring_metadata.json"
            with open(metadata_path, 'w') as f:
                json.dump(self.metadata, f, indent=2)
            
            print(f"💾 Credit scoring model saved to {self.model_dir}")


# Global model instance
credit_scoring_model = CreditScoringModel()
