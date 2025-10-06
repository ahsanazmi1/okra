"""
BNPL optimization ML model for Okra.

This module provides advanced BNPL optimization using Random Forest
for dynamic pricing and risk assessment.
"""

import os
import json
import joblib
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List
from datetime import datetime

from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

from .feature_engineering import feature_store


class BNPLOptimizationModel:
    """BNPL optimization ML model using Random Forest."""
    
    def __init__(self, model_dir: str = "models/bnpl_optimization"):
        """Initialize the BNPL optimization model."""
        self.model_dir = Path(model_dir)
        self.model_dir.mkdir(parents=True, exist_ok=True)
        
        self.model: Optional[RandomForestRegressor] = None
        self.scaler: Optional[StandardScaler] = None
        self.feature_names: List[str] = []
        self.metadata: Dict[str, Any] = {}
        self.is_loaded = False
        
        # Try to load existing model
        self._load_model()
    
    def _load_model(self) -> bool:
        """Load existing model artifacts."""
        model_path = self.model_dir / "bnpl_optimization_model.pkl"
        scaler_path = self.model_dir / "bnpl_optimization_scaler.pkl"
        metadata_path = self.model_dir / "bnpl_optimization_metadata.json"
        
        try:
            if all(p.exists() for p in [model_path, scaler_path, metadata_path]):
                self.model = joblib.load(model_path)
                self.scaler = joblib.load(scaler_path)
                
                with open(metadata_path, 'r') as f:
                    self.metadata = json.load(f)
                
                self.feature_names = self.metadata.get('feature_names', [])
                self.is_loaded = True
                print(f"✅ Loaded BNPL optimization model from {self.model_dir}")
                return True
        except Exception as e:
            print(f"⚠️ Failed to load BNPL optimization model: {e}")
        
        return False
    
    def train_model(self, n_samples: int = 8000) -> Dict[str, Any]:
        """
        Train the BNPL optimization model with synthetic data.
        
        Args:
            n_samples: Number of training samples to generate
            
        Returns:
            Training metrics
        """
        print("🚀 Training BNPL optimization ML model...")
        
        # Generate synthetic training data
        X, y = self._generate_training_data(n_samples)
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
        
        # Scale features
        self.scaler = StandardScaler()
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        # Train Random Forest model
        self.model = RandomForestRegressor(
            n_estimators=200,
            max_depth=10,
            min_samples_split=5,
            min_samples_leaf=2,
            random_state=42,
            n_jobs=-1
        )
        
        self.model.fit(X_train_scaled, y_train)
        
        # Evaluate model
        y_pred = self.model.predict(X_test_scaled)
        
        # Calculate metrics
        mse = mean_squared_error(y_test, y_pred)
        rmse = np.sqrt(mse)
        r2 = r2_score(y_test, y_pred)
        
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
                'mse': float(mse),
                'rmse': float(rmse),
                'r2_score': float(r2),
                'n_features': len(self.feature_names),
                'n_samples_train': len(X_train),
                'n_samples_test': len(X_test)
            },
            'model_parameters': {
                'n_estimators': 200,
                'max_depth': 10,
                'min_samples_split': 5,
                'min_samples_leaf': 2
            }
        }
        
        # Save model artifacts
        self._save_model()
        
        print(f"✅ BNPL optimization model trained successfully!")
        print(f"📊 RMSE: {rmse:.4f}")
        print(f"📊 R² Score: {r2:.4f}")
        
        return {
            'mse': mse,
            'rmse': rmse,
            'r2_score': r2,
            'feature_importance': feature_importance,
            'training_samples': n_samples
        }
    
    def optimize_bnpl_terms(self, features: Dict[str, float]) -> Dict[str, Any]:
        """
        Optimize BNPL terms using the trained model.
        
        Args:
            features: Feature dictionary
            
        Returns:
            Optimization results with recommended terms
        """
        if not self.is_loaded:
            # Fallback to rule-based optimization
            return self._fallback_optimization(features)
        
        try:
            # Convert features to array
            feature_array = np.array([features.get(name, 0.0) for name in self.feature_names])
            feature_array = feature_array.reshape(1, -1)
            
            # Scale features
            feature_array_scaled = self.scaler.transform(feature_array)
            
            # Predict optimal terms
            optimal_score = self.model.predict(feature_array_scaled)[0]
            
            # Convert score to BNPL terms
            bnpl_terms = self._score_to_bnpl_terms(optimal_score, features)
            
            # Calculate risk assessment
            risk_assessment = self._calculate_risk_assessment(features)
            
            # Feature importance for this prediction
            feature_contributions = dict(zip(
                self.feature_names,
                self.model.feature_importances_
            ))
            
            return {
                'optimal_score': float(optimal_score),
                'recommended_terms': bnpl_terms,
                'risk_assessment': risk_assessment,
                'feature_contributions': feature_contributions,
                'model_version': self.metadata.get('version', '1.0.0'),
                'optimization_confidence': 0.8,
                'model_type': 'random_forest_bnpl_optimization'
            }
            
        except Exception as e:
            print(f"⚠️ ML optimization failed: {e}")
            return self._fallback_optimization(features)
    
    def _generate_training_data(self, n_samples: int) -> Tuple[pd.DataFrame, pd.Series]:
        """Generate synthetic training data for BNPL optimization."""
        np.random.seed(42)
        
        data = []
        for _ in range(n_samples):
            # Generate BNPL features
            amount = np.random.uniform(50, 5000)
            tenor = np.random.choice([1, 2, 3, 4, 6, 12], p=[0.1, 0.2, 0.3, 0.2, 0.15, 0.05])
            on_time_rate = np.random.beta(8, 2)  # Skewed towards high on-time rates
            utilization = np.random.beta(2, 5)  # Skewed towards low utilization
            customer_age_days = np.random.exponential(365 * 2)  # Customer age
            
            # Generate additional features
            payment_frequency = np.random.poisson(12)  # Monthly payments
            merchant_category = np.random.choice([0.2, 0.3, 0.4, 0.5, 0.6, 0.7], 
                                               p=[0.3, 0.2, 0.2, 0.15, 0.1, 0.05])
            seasonal_factor = np.random.uniform(0.5, 1.0)
            
            # Create feature vector
            features = {
                'amount_normalized': min(amount / 5000.0, 1.0),
                'tenor_normalized': min(tenor / 12.0, 1.0),
                'on_time_rate': on_time_rate,
                'utilization': utilization,
                'customer_age_days_normalized': min(customer_age_days / 3650.0, 1.0),
                'payment_frequency': payment_frequency,
                'merchant_category_encoded': merchant_category,
                'seasonal_factor': seasonal_factor
            }
            
            data.append(features)
        
        # Convert to DataFrame
        df = pd.DataFrame(data)
        self.feature_names = df.columns.tolist()
        
        # Generate target variable (optimization score)
        # Higher score = better BNPL terms (lower interest, longer terms)
        optimization_score = (
            df['on_time_rate'] * 0.3 +  # Good payment history
            (1 - df['utilization']) * 0.25 +  # Low utilization
            df['customer_age_days_normalized'] * 0.2 +  # Established customer
            (1 - df['amount_normalized']) * 0.15 +  # Smaller amounts are safer
            df['seasonal_factor'] * 0.1  # Seasonal considerations
        )
        
        # Add some noise
        optimization_score += np.random.normal(0, 0.05, len(optimization_score))
        optimization_score = np.clip(optimization_score, 0, 1)
        
        return df, optimization_score
    
    def _score_to_bnpl_terms(self, score: float, features: Dict[str, float]) -> Dict[str, Any]:
        """Convert optimization score to BNPL terms."""
        amount = features.get('amount_normalized', 0.5) * 5000  # Convert back to actual amount
        tenor = features.get('tenor_normalized', 0.25) * 12  # Convert back to actual tenor
        
        # Calculate interest rate based on score (lower score = higher risk = higher rate)
        base_rate = 0.15  # 15% base rate
        risk_adjustment = (1 - score) * 0.1  # Up to 10% additional for high risk
        interest_rate = base_rate + risk_adjustment
        
        # Calculate monthly payment
        monthly_rate = interest_rate / 12
        if monthly_rate > 0:
            monthly_payment = amount * (monthly_rate * (1 + monthly_rate) ** tenor) / \
                            ((1 + monthly_rate) ** tenor - 1)
        else:
            monthly_payment = amount / tenor
        
        # Calculate total cost
        total_cost = monthly_payment * tenor
        
        return {
            'amount': float(amount),
            'interest_rate': float(interest_rate),
            'term_months': int(tenor),
            'monthly_payment': float(monthly_payment),
            'total_cost': float(total_cost),
            'apr': float(interest_rate * 100),
            'approval_probability': float(score)
        }
    
    def _calculate_risk_assessment(self, features: Dict[str, float]) -> Dict[str, Any]:
        """Calculate risk assessment for BNPL terms."""
        on_time_rate = features.get('on_time_rate', 0.9)
        utilization = features.get('utilization', 0.2)
        customer_age = features.get('customer_age_days_normalized', 0.5)
        
        # Calculate risk score
        risk_score = (
            (1 - on_time_rate) * 0.4 +  # Payment history risk
            utilization * 0.3 +  # Utilization risk
            (1 - customer_age) * 0.3  # Customer maturity risk
        )
        
        # Determine risk level
        if risk_score <= 0.2:
            risk_level = "low"
        elif risk_score <= 0.5:
            risk_level = "medium"
        else:
            risk_level = "high"
        
        return {
            'risk_score': float(risk_score),
            'risk_level': risk_level,
            'risk_factors': {
                'payment_history_risk': float(1 - on_time_rate),
                'utilization_risk': float(utilization),
                'customer_maturity_risk': float(1 - customer_age)
            }
        }
    
    def _fallback_optimization(self, features: Dict[str, float]) -> Dict[str, Any]:
        """Fallback optimization using rule-based scoring."""
        amount = features.get('amount_normalized', 0.5) * 5000
        tenor = features.get('tenor_normalized', 0.25) * 12
        on_time_rate = features.get('on_time_rate', 0.9)
        
        # Simple rule-based optimization
        if on_time_rate >= 0.95:
            interest_rate = 0.12  # 12% for excellent payment history
        elif on_time_rate >= 0.90:
            interest_rate = 0.15  # 15% for good payment history
        else:
            interest_rate = 0.20  # 20% for poor payment history
        
        monthly_rate = interest_rate / 12
        if monthly_rate > 0:
            monthly_payment = amount * (monthly_rate * (1 + monthly_rate) ** tenor) / \
                            ((1 + monthly_rate) ** tenor - 1)
        else:
            monthly_payment = amount / tenor
        
        total_cost = monthly_payment * tenor
        
        return {
            'optimal_score': 0.7,  # Default score
            'recommended_terms': {
                'amount': float(amount),
                'interest_rate': float(interest_rate),
                'term_months': int(tenor),
                'monthly_payment': float(monthly_payment),
                'total_cost': float(total_cost),
                'apr': float(interest_rate * 100),
                'approval_probability': float(on_time_rate)
            },
            'risk_assessment': {
                'risk_score': float(1 - on_time_rate),
                'risk_level': 'low' if on_time_rate >= 0.9 else 'medium' if on_time_rate >= 0.8 else 'high',
                'risk_factors': {
                    'payment_history_risk': float(1 - on_time_rate),
                    'utilization_risk': features.get('utilization', 0.2),
                    'customer_maturity_risk': 0.3
                }
            },
            'feature_contributions': {},
            'model_version': 'fallback-1.0.0',
            'optimization_confidence': 0.5,
            'model_type': 'rule_based_fallback'
        }
    
    def _save_model(self):
        """Save model artifacts."""
        if self.model and self.scaler:
            # Save model
            model_path = self.model_dir / "bnpl_optimization_model.pkl"
            joblib.dump(self.model, model_path)
            
            # Save scaler
            scaler_path = self.model_dir / "bnpl_optimization_scaler.pkl"
            joblib.dump(self.scaler, scaler_path)
            
            # Save metadata
            metadata_path = self.model_dir / "bnpl_optimization_metadata.json"
            with open(metadata_path, 'w') as f:
                json.dump(self.metadata, f, indent=2)
            
            print(f"💾 BNPL optimization model saved to {self.model_dir}")


# Global model instance
bnpl_optimization_model = BNPLOptimizationModel()
