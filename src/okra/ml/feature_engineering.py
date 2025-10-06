"""
Feature engineering for Okra ML models.

This module provides feature extraction and engineering capabilities
for credit scoring and BNPL optimization ML models.
"""

import numpy as np
import pandas as pd
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import hashlib


class CreditFeatureExtractor:
    """Feature extractor for credit scoring ML models."""
    
    def __init__(self):
        """Initialize the feature extractor."""
        self.feature_names = [
            'credit_score_normalized',
            'annual_income_log',
            'debt_to_income_ratio',
            'credit_history_months_normalized',
            'employment_status_encoded',
            'requested_amount_log',
            'term_months_normalized',
            'velocity_12m',
            'late_payments_12m',
            'credit_utilization',
            'inquiries_6m',
            'bankruptcy_flag',
            'income_stability',
            'geographic_risk',
            'purpose_risk'
        ]
    
    def extract_features(self, credit_request: Dict[str, Any], 
                        credit_profile: Optional[Dict[str, Any]] = None,
                        additional_context: Optional[Dict[str, Any]] = None) -> Dict[str, float]:
        """
        Extract features for credit scoring ML model.
        
        Args:
            credit_request: Credit request information
            credit_profile: Credit profile information
            additional_context: Additional context data
            
        Returns:
            Dictionary of engineered features
        """
        features = {}
        
        # Credit score features
        credit_score = credit_profile.get('credit_score', 650) if credit_profile else 650
        features['credit_score_normalized'] = self._normalize_credit_score(credit_score)
        
        # Income features
        annual_income = credit_profile.get('annual_income', 50000) if credit_profile else 50000
        features['annual_income_log'] = np.log1p(float(annual_income))
        
        # Debt-to-income ratio
        dti_ratio = credit_profile.get('debt_to_income_ratio', 0.3) if credit_profile else 0.3
        features['debt_to_income_ratio'] = min(float(dti_ratio), 1.0)
        
        # Credit history
        credit_history = credit_profile.get('credit_history_months', 60) if credit_profile else 60
        features['credit_history_months_normalized'] = min(credit_history / 120.0, 1.0)  # Normalize to 10 years
        
        # Employment status encoding
        employment_status = credit_profile.get('employment_status', 'employed') if credit_profile else 'employed'
        features['employment_status_encoded'] = self._encode_employment_status(employment_status)
        
        # Request amount
        requested_amount = float(credit_request.get('requested_amount', 10000))
        features['requested_amount_log'] = np.log1p(requested_amount)
        
        # Term months
        term_months = credit_request.get('term_months', 36)
        features['term_months_normalized'] = min(term_months / 60.0, 1.0)  # Normalize to 5 years
        
        # Additional features from context
        context = additional_context or {}
        
        # Velocity features
        features['velocity_12m'] = context.get('velocity_12m', 12.0)
        features['late_payments_12m'] = context.get('late_payments_12m', 0)
        features['credit_utilization'] = context.get('credit_utilization', 0.3)
        features['inquiries_6m'] = context.get('inquiries_6m', 2)
        
        # Risk flags
        features['bankruptcy_flag'] = 1.0 if context.get('bankruptcy_flag', False) else 0.0
        features['income_stability'] = context.get('income_stability', 0.8)
        features['geographic_risk'] = context.get('geographic_risk', 0.5)
        features['purpose_risk'] = context.get('purpose_risk', 0.5)
        
        return features
    
    def _normalize_credit_score(self, credit_score: int) -> float:
        """Normalize credit score to 0-1 range."""
        return min(max((credit_score - 300) / 550.0, 0.0), 1.0)
    
    def _encode_employment_status(self, status: str) -> float:
        """Encode employment status to numerical value."""
        employment_encoding = {
            'employed': 1.0,
            'self_employed': 0.8,
            'unemployed': 0.2,
            'retired': 0.6,
            'student': 0.3
        }
        return employment_encoding.get(status.lower(), 0.5)


class BNPLFeatureExtractor:
    """Feature extractor for BNPL optimization ML models."""
    
    def __init__(self):
        """Initialize the BNPL feature extractor."""
        self.feature_names = [
            'amount_normalized',
            'tenor_normalized',
            'on_time_rate',
            'utilization',
            'customer_age_days_normalized',
            'payment_frequency',
            'merchant_category_encoded',
            'seasonal_factor'
        ]
    
    def extract_features(self, bnpl_request: Dict[str, Any],
                        customer_context: Optional[Dict[str, Any]] = None) -> Dict[str, float]:
        """
        Extract features for BNPL optimization ML model.
        
        Args:
            bnpl_request: BNPL request information
            customer_context: Customer context data
            
        Returns:
            Dictionary of engineered features
        """
        features = {}
        
        # Amount normalization
        amount = float(bnpl_request.get('amount', 500))
        features['amount_normalized'] = min(amount / 5000.0, 1.0)  # Normalize to max $5000
        
        # Tenor normalization
        tenor = bnpl_request.get('tenor', 3)
        features['tenor_normalized'] = min(tenor / 12.0, 1.0)  # Normalize to max 12 months
        
        # Historical performance
        features['on_time_rate'] = bnpl_request.get('on_time_rate', 0.95)
        features['utilization'] = bnpl_request.get('utilization', 0.2)
        
        # Customer context
        context = customer_context or {}
        customer_age_days = context.get('customer_age_days', 365)
        features['customer_age_days_normalized'] = min(customer_age_days / 3650.0, 1.0)  # Normalize to 10 years
        
        # Payment patterns
        features['payment_frequency'] = context.get('payment_frequency', 12.0)  # Monthly
        
        # Merchant category encoding
        merchant_category = context.get('merchant_category', 'general')
        features['merchant_category_encoded'] = self._encode_merchant_category(merchant_category)
        
        # Seasonal factors
        current_month = datetime.now().month
        features['seasonal_factor'] = self._calculate_seasonal_factor(current_month)
        
        return features
    
    def _encode_merchant_category(self, category: str) -> float:
        """Encode merchant category to risk score."""
        category_risk = {
            'grocery': 0.2,
            'retail': 0.3,
            'electronics': 0.4,
            'fashion': 0.5,
            'travel': 0.6,
            'luxury': 0.7,
            'general': 0.5
        }
        return category_risk.get(category.lower(), 0.5)
    
    def _calculate_seasonal_factor(self, month: int) -> float:
        """Calculate seasonal factor based on month."""
        # Higher spending typically in Q4 (holiday season)
        seasonal_factors = {
            1: 0.6,   # January (post-holiday)
            2: 0.5,   # February
            3: 0.6,   # March
            4: 0.7,   # April
            5: 0.7,   # May
            6: 0.6,   # June
            7: 0.6,   # July
            8: 0.7,   # August (back to school)
            9: 0.7,   # September
            10: 0.8,  # October
            11: 0.9,  # November (holiday shopping)
            12: 1.0   # December (holiday season)
        }
        return seasonal_factors.get(month, 0.7)


class FeatureStore:
    """Feature store for caching and managing features."""
    
    def __init__(self):
        """Initialize the feature store."""
        self.cache = {}
        self.credit_extractor = CreditFeatureExtractor()
        self.bnpl_extractor = BNPLFeatureExtractor()
    
    def get_credit_features(self, actor_id: str, credit_request: Dict[str, Any],
                           credit_profile: Optional[Dict[str, Any]] = None,
                           additional_context: Optional[Dict[str, Any]] = None) -> Dict[str, float]:
        """Get credit features with caching."""
        # Create cache key
        cache_key = self._create_cache_key('credit', actor_id, credit_request, credit_profile)
        
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        # Extract features
        features = self.credit_extractor.extract_features(credit_request, credit_profile, additional_context)
        
        # Cache features
        self.cache[cache_key] = features
        
        return features
    
    def get_bnpl_features(self, actor_id: str, bnpl_request: Dict[str, Any],
                         customer_context: Optional[Dict[str, Any]] = None) -> Dict[str, float]:
        """Get BNPL features with caching."""
        # Create cache key
        cache_key = self._create_cache_key('bnpl', actor_id, bnpl_request, customer_context)
        
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        # Extract features
        features = self.bnpl_extractor.extract_features(bnpl_request, customer_context)
        
        # Cache features
        self.cache[cache_key] = features
        
        return features
    
    def _create_cache_key(self, model_type: str, actor_id: str, 
                         request: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> str:
        """Create a cache key for features."""
        # Create a hash of the request and context
        data_str = f"{model_type}:{actor_id}:{str(sorted(request.items()))}"
        if context:
            data_str += f":{str(sorted(context.items()))}"
        
        return hashlib.md5(data_str.encode()).hexdigest()
    
    def clear_cache(self):
        """Clear the feature cache."""
        self.cache.clear()


# Global feature store instance
feature_store = FeatureStore()
