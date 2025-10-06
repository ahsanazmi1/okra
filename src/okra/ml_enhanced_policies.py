"""
ML-enhanced credit policies for Okra.

This module provides advanced credit decision making using both traditional
policy rules and machine learning models for improved accuracy and optimization.
"""

import os
import numpy as np
from decimal import Decimal
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

# Import ML models
from .ml.credit_scoring_model import credit_scoring_model
from .ml.bnpl_optimization_model import bnpl_optimization_model
from .ml.feature_engineering import feature_store

# Import base policies
from .policies import CreditProfile, CreditRequest, CreditQuote, CreditPolicies


class MLEnhancedCreditQuote(CreditQuote):
    """Enhanced credit quote with ML predictions."""
    
    # ML-specific fields
    ml_prediction: Optional[Dict[str, Any]] = Field(None, description="ML model predictions")
    ml_confidence: Optional[float] = Field(None, ge=0, le=1, description="ML model confidence")
    feature_contributions: Optional[Dict[str, float]] = Field(None, description="Feature contributions to decision")


class MLEnhancedCreditPolicies:
    """ML-enhanced credit policies combining rules and machine learning."""
    
    def __init__(self):
        """Initialize ML-enhanced policies."""
        self.use_ml = os.getenv("OKRA_USE_ML", "true").lower() == "true"
        self.ml_weight = float(os.getenv("OKRA_ML_WEIGHT", "0.7"))  # 70% ML, 30% rules
        
        # Train models if not already trained
        self._ensure_models_trained()
    
    def _ensure_models_trained(self):
        """Ensure ML models are trained."""
        if not self.use_ml:
            return
            
        try:
            # Train credit scoring model if not loaded
            if not credit_scoring_model.is_loaded:
                print("🚀 Training credit scoring ML model...")
                credit_scoring_model.train_model()
            
            # Train BNPL optimization model if not loaded
            if not bnpl_optimization_model.is_loaded:
                print("🚀 Training BNPL optimization ML model...")
                bnpl_optimization_model.train_model()
                
        except Exception as e:
            print(f"⚠️ Failed to train ML models: {e}")
            self.use_ml = False
    
    def evaluate_credit_request(self, request: CreditRequest) -> MLEnhancedCreditQuote:
        """
        Evaluate a credit request using ML-enhanced policies.
        
        Args:
            request: Credit request information
            
        Returns:
            ML-enhanced credit quote with approval decision and terms
        """
        # First, apply traditional policy rules
        traditional_quote = CreditPolicies.evaluate_credit_request(request)
        
        if not self.use_ml:
            # Return traditional quote with ML fields set to None
            return MLEnhancedCreditQuote(
                **traditional_quote.dict(),
                ml_prediction=None,
                ml_confidence=None,
                feature_contributions=None
            )
        
        try:
            # Extract features for ML model
            credit_profile_dict = request.profile.dict() if request.profile else {}
            credit_request_dict = {
                'requested_amount': float(request.amount),
                'term_months': request.term_months,
                'purpose': request.purpose
            }
            
            # Generate additional context for feature engineering
            additional_context = self._generate_additional_context(request)
            
            # Get ML features
            ml_features = feature_store.get_credit_features(
                actor_id=request.actor_id,
                credit_request=credit_request_dict,
                credit_profile=credit_profile_dict,
                additional_context=additional_context
            )
            
            # Get ML prediction
            ml_prediction = credit_scoring_model.predict_credit_score(ml_features)
            
            # Combine traditional and ML decisions
            enhanced_quote = self._combine_decisions(traditional_quote, ml_prediction, request)
            
            return enhanced_quote
            
        except Exception as e:
            print(f"⚠️ ML evaluation failed: {e}")
            # Return traditional quote with error information
            return MLEnhancedCreditQuote(
                **traditional_quote.dict(),
                ml_prediction={"error": str(e)},
                ml_confidence=0.0,
                feature_contributions={}
            )
    
    def _generate_additional_context(self, request: CreditRequest) -> Dict[str, Any]:
        """Generate additional context for ML feature engineering."""
        # This would typically come from external data sources
        # For now, we'll generate synthetic context based on actor_id
        
        # Use actor_id as seed for deterministic synthetic data
        import hashlib
        seed = int(hashlib.md5(request.actor_id.encode()).hexdigest()[:8], 16)
        
        # Generate synthetic context
        np.random.seed(seed)
        
        return {
            'velocity_12m': np.random.poisson(12),  # Average 12 transactions per year
            'late_payments_12m': np.random.poisson(1),  # Average 1 late payment
            'credit_utilization': np.random.beta(2, 3),  # Skewed towards low utilization
            'inquiries_6m': np.random.poisson(2),  # Average 2 credit inquiries
            'bankruptcy_flag': np.random.choice([True, False], p=[0.05, 0.95]),
            'income_stability': np.random.beta(5, 2),  # Skewed towards high stability
            'geographic_risk': np.random.beta(2, 3),  # Skewed towards low risk
            'purpose_risk': np.random.beta(2, 3)  # Skewed towards low risk
        }
    
    def _combine_decisions(self, traditional_quote: CreditQuote, 
                          ml_prediction: Dict[str, Any], 
                          request: CreditRequest) -> MLEnhancedCreditQuote:
        """Combine traditional policy and ML predictions."""
        
        ml_approval_probability = ml_prediction.get('approval_probability', 0.5)
        ml_confidence = ml_prediction.get('prediction_confidence', 0.5)
        
        # Determine final decision based on ML and traditional rules
        if self.ml_weight > 0.5:
            # ML-weighted decision
            final_approved = ml_approval_probability > 0.6
            final_review_required = not final_approved and ml_approval_probability > 0.4
        else:
            # Traditional rules weighted decision
            final_approved = traditional_quote.approved
            final_review_required = traditional_quote.review_required
        
        # Use ML for APR and credit limit optimization
        if ml_prediction.get('model_type') != 'rule_based_fallback':
            # Use ML-optimized terms
            ml_credit_score = ml_prediction.get('credit_score', 650)
            optimized_apr = self._get_ml_optimized_apr(ml_credit_score, ml_approval_probability)
            optimized_limit = self._get_ml_optimized_limit(request.amount, ml_credit_score, ml_approval_probability)
        else:
            # Use traditional terms
            optimized_apr = traditional_quote.apr
            optimized_limit = traditional_quote.credit_limit
        
        # Calculate monthly payment
        monthly_rate = optimized_apr / 100 / 12
        monthly_payment = self._calculate_monthly_payment(
            optimized_limit, monthly_rate, request.term_months
        )
        
        # Combine reasons
        combined_reasons = traditional_quote.reasons.copy()
        if ml_prediction.get('model_type') != 'rule_based_fallback':
            combined_reasons.append(f"ML model prediction: {ml_approval_probability:.1%} approval probability")
            combined_reasons.append(f"ML risk level: {ml_prediction.get('risk_level', 'medium')}")
        
        return MLEnhancedCreditQuote(
            approved=final_approved,
            credit_limit=optimized_limit,
            apr=optimized_apr,
            term_months=request.term_months,
            monthly_payment=monthly_payment,
            reasons=combined_reasons,
            review_required=final_review_required,
            policy_version="ml-enhanced-v1.0.0",
            ml_prediction=ml_prediction,
            ml_confidence=ml_confidence,
            feature_contributions=ml_prediction.get('feature_contributions', {})
        )
    
    def _get_ml_optimized_apr(self, ml_credit_score: float, approval_probability: float) -> Decimal:
        """Get ML-optimized APR based on credit score and approval probability."""
        # Base APR from credit score
        if ml_credit_score >= 750:
            base_apr = 8.99
        elif ml_credit_score >= 700:
            base_apr = 12.99
        elif ml_credit_score >= 650:
            base_apr = 18.99
        elif ml_credit_score >= 600:
            base_apr = 24.99
        else:
            base_apr = 29.99
        
        # Adjust based on approval probability
        if approval_probability >= 0.9:
            # Excellent risk - reduce APR
            adjustment = -1.0
        elif approval_probability >= 0.8:
            # Good risk - slight reduction
            adjustment = -0.5
        elif approval_probability >= 0.6:
            # Medium risk - no adjustment
            adjustment = 0.0
        else:
            # High risk - increase APR
            adjustment = 2.0
        
        optimized_apr = base_apr + adjustment
        return Decimal(str(max(optimized_apr, 5.99)))  # Minimum 5.99% APR
    
    def _get_ml_optimized_limit(self, requested_amount: Decimal, 
                               ml_credit_score: float, 
                               approval_probability: float) -> Decimal:
        """Get ML-optimized credit limit."""
        # Start with requested amount
        limit = requested_amount
        
        # Adjust based on ML credit score
        if ml_credit_score >= 750:
            # Excellent credit - can exceed requested amount by 20%
            limit = limit * Decimal("1.20")
        elif ml_credit_score >= 700:
            # Good credit - can exceed by 10%
            limit = limit * Decimal("1.10")
        elif ml_credit_score >= 650:
            # Fair credit - keep at requested amount
            pass
        else:
            # Poor credit - reduce by 20%
            limit = limit * Decimal("0.80")
        
        # Adjust based on approval probability
        if approval_probability >= 0.9:
            # Excellent risk - increase limit
            limit = limit * Decimal("1.10")
        elif approval_probability < 0.6:
            # High risk - reduce limit
            limit = limit * Decimal("0.85")
        
        # Ensure within bounds
        limit = max(limit, Decimal("1000"))  # Minimum $1000
        limit = min(limit, Decimal("50000"))  # Maximum $50000
        
        return limit.quantize(Decimal("0.01"))
    
    def _calculate_monthly_payment(self, principal: Decimal, monthly_rate: Decimal, months: int) -> Decimal:
        """Calculate monthly payment using standard loan formula."""
        if monthly_rate == 0:
            return principal / months
        
        # Standard loan payment formula
        payment = (
            principal
            * (monthly_rate * (1 + monthly_rate) ** months)
            / ((1 + monthly_rate) ** months - 1)
        )
        return payment.quantize(Decimal("0.01"))
    
    def optimize_bnpl_terms(self, bnpl_request: Dict[str, Any], 
                           customer_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Optimize BNPL terms using ML model.
        
        Args:
            bnpl_request: BNPL request information
            customer_context: Customer context data
            
        Returns:
            Optimized BNPL terms
        """
        if not self.use_ml or not bnpl_optimization_model.is_loaded:
            # Fallback to rule-based optimization
            return self._rule_based_bnpl_optimization(bnpl_request)
        
        try:
            # Get BNPL features
            bnpl_features = feature_store.get_bnpl_features(
                actor_id=customer_context.get('actor_id', 'unknown') if customer_context else 'unknown',
                bnpl_request=bnpl_request,
                customer_context=customer_context
            )
            
            # Get ML optimization
            ml_optimization = bnpl_optimization_model.optimize_bnpl_terms(bnpl_features)
            
            return {
                'optimized_terms': ml_optimization.get('recommended_terms', {}),
                'risk_assessment': ml_optimization.get('risk_assessment', {}),
                'ml_prediction': ml_optimization,
                'optimization_method': 'ml_enhanced'
            }
            
        except Exception as e:
            print(f"⚠️ BNPL ML optimization failed: {e}")
            return self._rule_based_bnpl_optimization(bnpl_request)
    
    def _rule_based_bnpl_optimization(self, bnpl_request: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback rule-based BNPL optimization."""
        amount = float(bnpl_request.get('amount', 500))
        tenor = bnpl_request.get('tenor', 3)
        on_time_rate = bnpl_request.get('on_time_rate', 0.95)
        
        # Simple rule-based optimization
        if on_time_rate >= 0.95:
            interest_rate = 0.12
        elif on_time_rate >= 0.90:
            interest_rate = 0.15
        else:
            interest_rate = 0.20
        
        monthly_rate = interest_rate / 12
        if monthly_rate > 0:
            monthly_payment = amount * (monthly_rate * (1 + monthly_rate) ** tenor) / \
                            ((1 + monthly_rate) ** tenor - 1)
        else:
            monthly_payment = amount / tenor
        
        return {
            'optimized_terms': {
                'amount': amount,
                'interest_rate': interest_rate,
                'term_months': tenor,
                'monthly_payment': monthly_payment,
                'total_cost': monthly_payment * tenor,
                'apr': interest_rate * 100,
                'approval_probability': on_time_rate
            },
            'risk_assessment': {
                'risk_score': 1 - on_time_rate,
                'risk_level': 'low' if on_time_rate >= 0.9 else 'medium' if on_time_rate >= 0.8 else 'high',
                'risk_factors': {
                    'payment_history_risk': 1 - on_time_rate,
                    'utilization_risk': bnpl_request.get('utilization', 0.2),
                    'customer_maturity_risk': 0.3
                }
            },
            'ml_prediction': None,
            'optimization_method': 'rule_based'
        }
    
    def list_policies(self) -> Dict[str, Any]:
        """List current policy parameters including ML configuration."""
        base_policies = CreditPolicies.list_policies()
        
        return {
            **base_policies,
            "ml_enhanced": True,
            "ml_configuration": {
                "use_ml": self.use_ml,
                "ml_weight": self.ml_weight,
                "credit_scoring_model_loaded": credit_scoring_model.is_loaded,
                "bnpl_optimization_model_loaded": bnpl_optimization_model.is_loaded
            },
            "policy_version": "ml-enhanced-v1.0.0"
        }


# Global ML-enhanced policies instance
ml_enhanced_policies = MLEnhancedCreditPolicies()
