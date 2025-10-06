"""
ML-enhanced API endpoints for Okra.

This module provides enhanced API endpoints that use machine learning
models for improved credit scoring and BNPL optimization.
"""

from fastapi import FastAPI, HTTPException, Query, status
from typing import Dict, Any, List, Optional

# Import ML-enhanced policies
from .ml_enhanced_policies import ml_enhanced_policies, MLEnhancedCreditQuote

# Import existing models and types
from .api import (
    app, AP2Mandate, CreditQuoteRequest, CreditQuoteResponse, 
    BNPLQuoteRequest, BNPLQuoteResponse
)
from .policies import CreditProfile, CreditRequest


@app.get("/policies", response_model=Dict[str, Any])
async def get_policies():
    """Get current credit policies and ML configuration."""
    return ml_enhanced_policies.list_policies()


@app.post("/credit/quote", response_model=CreditQuoteResponse, status_code=status.HTTP_200_OK)
async def get_credit_quote(request: CreditQuoteRequest):
    """
    Get a credit quote using ML-enhanced policies.

    This endpoint:
    1. Extracts relevant information from the AP2 mandate
    2. Evaluates the request using ML-enhanced policies (rules + ML)
    3. Returns a credit quote with approval decision and terms
    4. Optionally emits a CloudEvent for the quote
    """
    try:
        # Extract actor ID from mandate
        actor_id = request.mandate.actor.get("id", "unknown")

        # Build credit profile from request
        credit_profile = None
        if request.credit_profile:
            try:
                credit_profile = CreditProfile(**request.credit_profile)
            except Exception:
                # If profile data is invalid, continue without it
                credit_profile = None

        # Create credit request
        credit_request = CreditRequest(
            amount=request.requested_amount,
            term_months=request.term_months,
            purpose=request.purpose,
            actor_id=actor_id,
            profile=credit_profile,
        )

        # Evaluate using ML-enhanced policies
        quote = ml_enhanced_policies.evaluate_credit_request(credit_request)

        # Generate quote ID (in production, this would be a proper UUID)
        quote_id = f"quote_{actor_id}_{hash(str(credit_request))}"

        # Create response
        response = CreditQuoteResponse(
            quote_id=quote_id,
            approved=quote.approved,
            credit_limit=float(quote.credit_limit),
            apr=float(quote.apr),
            term_months=quote.term_months,
            monthly_payment=float(quote.monthly_payment),
            reasons=quote.reasons,
            review_required=quote.review_required,
            policy_version=quote.policy_version,
        )

        # Add ML-specific fields if available
        if quote.ml_prediction:
            response.ml_prediction = {
                "approval_probability": quote.ml_prediction.get("approval_probability"),
                "risk_level": quote.ml_prediction.get("risk_level"),
                "model_version": quote.ml_prediction.get("model_version"),
                "model_type": quote.ml_prediction.get("model_type")
            }
        
        if quote.feature_contributions:
            response.feature_contributions = quote.feature_contributions

        return response

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Credit quote evaluation failed: {str(e)}",
        )


@app.post("/bnpl/quote")
async def get_bnpl_quote(
    request: BNPLQuoteRequest,
    emit_ce: bool = Query(False, description="Emit CloudEvent for BNPL quote"),
) -> Dict[str, Any]:
    """
    Get a BNPL quote using ML-enhanced optimization.

    This endpoint:
    1. Uses ML models to optimize BNPL terms
    2. Provides risk assessment and pricing
    3. Optionally emits a CloudEvent for the quote
    """
    try:
        # Convert request to dictionary
        bnpl_request = {
            "amount": request.amount,
            "tenor": request.tenor,
            "on_time_rate": request.on_time_rate,
            "utilization": request.utilization
        }

        # Generate customer context (in production, this would come from customer data)
        customer_context = {
            "actor_id": "bnpl_customer",
            "customer_age_days": 365 * 2,  # 2 years
            "payment_frequency": 12.0,  # Monthly
            "merchant_category": "general"
        }

        # Get ML-optimized BNPL terms
        optimization_result = ml_enhanced_policies.optimize_bnpl_terms(
            bnpl_request, customer_context
        )

        # Extract optimized terms
        optimized_terms = optimization_result.get("optimized_terms", {})
        risk_assessment = optimization_result.get("risk_assessment", {})
        ml_prediction = optimization_result.get("ml_prediction", {})

        # Create response
        response = {
            "quote_id": f"bnpl_quote_{hash(str(bnpl_request))}",
            "approved": optimized_terms.get("approval_probability", 0.5) > 0.6,
            "amount": optimized_terms.get("amount", request.amount),
            "interest_rate": optimized_terms.get("interest_rate", 0.15),
            "term_months": optimized_terms.get("term_months", request.tenor),
            "monthly_payment": optimized_terms.get("monthly_payment", 0),
            "total_cost": optimized_terms.get("total_cost", 0),
            "apr": optimized_terms.get("apr", 15.0),
            "approval_probability": optimized_terms.get("approval_probability", 0.5),
            "risk_assessment": risk_assessment,
            "optimization_method": optimization_result.get("optimization_method", "unknown"),
            "ml_prediction": ml_prediction,
            "policy_version": "ml-enhanced-v1.0.0"
        }

        return response

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"BNPL quote evaluation failed: {str(e)}",
        )


@app.get("/credit/quote/{quote_id}", response_model=CreditQuoteResponse)
async def get_quote_by_id(quote_id: str):
    """
    Get a credit quote by ID (placeholder implementation).
    
    In production, this would retrieve the quote from a database.
    """
    # This is a placeholder - in production, you'd retrieve from database
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Quote retrieval by ID not implemented yet",
    )


@app.get("/ml/status", response_model=Dict[str, Any])
async def get_ml_status():
    """Get ML model status and configuration."""
    try:
        from .ml.credit_scoring_model import credit_scoring_model
        from .ml.bnpl_optimization_model import bnpl_optimization_model
        
        return {
            "ml_enabled": ml_enhanced_policies.use_ml,
            "ml_weight": ml_enhanced_policies.ml_weight,
            "models": {
                "credit_scoring": {
                    "loaded": credit_scoring_model.is_loaded,
                    "version": credit_scoring_model.metadata.get("version", "unknown"),
                    "training_date": credit_scoring_model.metadata.get("trained_on", "unknown"),
                    "features": len(credit_scoring_model.feature_names) if credit_scoring_model.feature_names else 0
                },
                "bnpl_optimization": {
                    "loaded": bnpl_optimization_model.is_loaded,
                    "version": bnpl_optimization_model.metadata.get("version", "unknown"),
                    "training_date": bnpl_optimization_model.metadata.get("trained_on", "unknown"),
                    "features": len(bnpl_optimization_model.feature_names) if bnpl_optimization_model.feature_names else 0
                }
            },
            "feature_store": {
                "cache_size": len(ml_enhanced_policies.feature_store.cache) if hasattr(ml_enhanced_policies, 'feature_store') else 0
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get ML status: {str(e)}",
        )


@app.post("/ml/retrain", response_model=Dict[str, Any])
async def retrain_ml_models():
    """Retrain ML models (admin endpoint)."""
    try:
        from .ml.credit_scoring_model import credit_scoring_model
        from .ml.bnpl_optimization_model import bnpl_optimization_model
        
        results = {}
        
        # Retrain credit scoring model
        print("🔄 Retraining credit scoring model...")
        credit_results = credit_scoring_model.train_model()
        results["credit_scoring"] = {
            "status": "success",
            "auc_score": credit_results.get("auc_score", 0),
            "log_loss": credit_results.get("log_loss", 0),
            "training_samples": credit_results.get("training_samples", 0)
        }
        
        # Retrain BNPL optimization model
        print("🔄 Retraining BNPL optimization model...")
        bnpl_results = bnpl_optimization_model.train_model()
        results["bnpl_optimization"] = {
            "status": "success",
            "r2_score": bnpl_results.get("r2_score", 0),
            "rmse": bnpl_results.get("rmse", 0),
            "training_samples": bnpl_results.get("training_samples", 0)
        }
        
        # Clear feature cache
        if hasattr(ml_enhanced_policies, 'feature_store'):
            ml_enhanced_policies.feature_store.clear_cache()
        
        return {
            "status": "success",
            "message": "ML models retrained successfully",
            "results": results
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrain ML models: {str(e)}",
        )
