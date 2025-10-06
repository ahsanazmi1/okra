"""
LLM explanation generation for Okra credit decisions.

Provides Azure OpenAI integration for generating human-readable explanations 
of credit risk assessments and BNPL recommendations.
"""

import json
import logging
import os
from datetime import datetime
from typing import Any, Dict, List, Optional

try:
    from openai import AzureOpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class CreditExplanationRequest(BaseModel):
    """Request for credit explanation generation."""
    
    credit_decision: str = Field(..., description="Credit decision (APPROVED, DECLINED, REVIEW)")
    risk_score: float = Field(..., description="Credit risk score (0.0-1.0)")
    requested_amount: float = Field(..., description="Requested credit amount")
    available_credit: float = Field(..., description="Available credit limit")
    bnpl_offered: bool = Field(..., description="Whether BNPL was offered")
    bnpl_terms: Optional[Dict[str, Any]] = Field(None, description="BNPL terms if offered")
    customer_context: Dict[str, Any] = Field(..., description="Customer context and features")
    model_features: Dict[str, float] = Field(..., description="ML model features and scores")
    reason_codes: List[str] = Field(default_factory=list, description="Reason codes for decision")


class CreditExplanationResponse(BaseModel):
    """Response from credit explanation generation."""
    
    explanation: str = Field(..., description="Human-readable explanation")
    confidence: float = Field(..., description="Explanation confidence", ge=0.0, le=1.0)
    key_factors: List[str] = Field(..., description="Key factors in decision")
    risk_analysis: Dict[str, Any] = Field(..., description="Risk analysis breakdown")
    bnpl_explanation: Optional[str] = Field(None, description="BNPL explanation if applicable")
    model_provenance: Dict[str, str] = Field(..., description="Model provenance information")
    processing_time_ms: float = Field(..., description="Processing time in milliseconds")
    tokens_used: int = Field(..., description="Tokens used in generation")


class OkraLLMExplainer:
    """Azure OpenAI-based credit explanation generator."""
    
    def __init__(self):
        self.client = None
        self.is_available = False
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize Azure OpenAI client."""
        if not OPENAI_AVAILABLE:
            logger.warning("OpenAI library not available")
            return
        
        # Get configuration from environment
        endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        api_key = os.getenv("AZURE_OPENAI_API_KEY")
        api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview")
        deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT", "okra-llm")
        
        if endpoint and api_key:
            try:
                self.client = AzureOpenAI(
                    api_key=api_key,
                    api_version=api_version,
                    azure_endpoint=endpoint
                )
                self.is_available = True
                logger.info(f"✅ Azure OpenAI client initialized with deployment: {deployment}")
            except Exception as e:
                logger.error(f"Failed to initialize Azure OpenAI client: {e}")
                self.client = None
                self.is_available = False
        else:
            logger.warning("Azure OpenAI not configured - missing endpoint or API key")
    
    def is_configured(self) -> bool:
        """Check if Azure OpenAI is configured."""
        return self.is_available and self.client is not None
    
    def get_configuration_status(self) -> Dict[str, Any]:
        """Get configuration status."""
        return {
            "status": "configured" if self.is_configured() else "not_configured",
            "endpoint": os.getenv("AZURE_OPENAI_ENDPOINT"),
            "deployment": os.getenv("AZURE_OPENAI_DEPLOYMENT", "okra-llm"),
            "api_key": "***" if os.getenv("AZURE_OPENAI_API_KEY") else None,
        }
    
    def explain_credit_decision(self, request: CreditExplanationRequest) -> Optional[CreditExplanationResponse]:
        """Generate explanation for credit decision."""
        if not self.is_configured():
            logger.warning("Azure OpenAI not configured, using fallback explanation")
            return self._generate_fallback_explanation(request)
        
        start_time = datetime.now()
        
        try:
            # Build the prompt
            system_prompt = self._get_system_prompt()
            user_prompt = self._build_explanation_prompt(request)
            
            # Call Azure OpenAI
            response = self.client.chat.completions.create(
                model=os.getenv("AZURE_OPENAI_DEPLOYMENT", "okra-llm"),
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7,
                max_tokens=1000
            )
            
            raw_response = response.choices[0].message.content
            
            # Parse the response
            explanation_data = self._parse_explanation_response(raw_response)
            
            processing_time = (datetime.now() - start_time).total_seconds() * 1000
            
            return CreditExplanationResponse(
                explanation=explanation_data.get("explanation", raw_response),
                confidence=explanation_data.get("confidence", 0.8),
                key_factors=explanation_data.get("key_factors", []),
                risk_analysis=explanation_data.get("risk_analysis", {}),
                bnpl_explanation=explanation_data.get("bnpl_explanation"),
                model_provenance={
                    "model_name": os.getenv("AZURE_OPENAI_DEPLOYMENT", "okra-llm"),
                    "provider": "azure_openai",
                    "status": "active",
                    "endpoint": os.getenv("AZURE_OPENAI_ENDPOINT"),
                },
                processing_time_ms=processing_time,
                tokens_used=response.usage.total_tokens if response.usage else 0
            )
            
        except Exception as e:
            logger.error(f"Error generating credit explanation: {e}")
            return self._generate_fallback_explanation(request)
    
    def _get_system_prompt(self) -> str:
        """Get the system prompt for credit explanation generation."""
        return """You are an expert credit analyst for Okra, the Open Credit Agent.
Your task is to generate clear, helpful explanations for credit decisions and BNPL recommendations.

CRITICAL REQUIREMENTS:
1. Explain WHY the credit decision was made (APPROVED/DECLINED/REVIEW)
2. Highlight key risk factors and positive indicators
3. Explain BNPL terms if offered, including benefits and risks
4. Use consumer-friendly language (avoid jargon)
5. Be specific about amounts, percentages, and terms
6. Provide actionable insights for the customer

JSON SCHEMA FOR RESPONSE:
{
  "explanation": "string - Clear explanation of the credit decision (max 200 words)",
  "confidence": "number - Confidence score between 0.0 and 1.0",
  "key_factors": ["string"] - List of 3-5 most important factors,
  "risk_analysis": {
    "primary_risks": ["string"],
    "positive_indicators": ["string"],
    "recommendations": ["string"]
  },
  "bnpl_explanation": "string - BNPL explanation if applicable (optional)"
}

Always respond with valid JSON matching this schema."""
    
    def _build_explanation_prompt(self, request: CreditExplanationRequest) -> str:
        """Build the user prompt for explanation generation."""
        return f"""Generate a clear explanation for this credit decision:

CREDIT DECISION: {request.credit_decision}
RISK SCORE: {request.risk_score:.3f}
REQUESTED AMOUNT: ${request.requested_amount:,.2f}
AVAILABLE CREDIT: ${request.available_credit:,.2f}
BNPL OFFERED: {request.bnpl_offered}

CUSTOMER CONTEXT:
- Payment History: {request.customer_context.get('payment_history_score', 0):.3f}
- Credit Utilization: {request.customer_context.get('credit_utilization', 0):.1%}
- Debt-to-Income: {request.customer_context.get('debt_to_income_ratio', 0):.1%}
- Employment Status: {request.customer_context.get('employment_status', 'Unknown')}
- Income Level: {request.customer_context.get('income_level', 'Unknown')}

ML MODEL FEATURES:
{json.dumps(request.model_features, indent=2)}

REASON CODES: {', '.join(request.reason_codes) if request.reason_codes else 'None'}

BNPL TERMS (if offered):
{json.dumps(request.bnpl_terms, indent=2) if request.bnpl_terms else 'Not applicable'}

Please explain the credit decision and provide insights for the customer."""
    
    def _parse_explanation_response(self, raw_response: str) -> Dict[str, Any]:
        """Parse the LLM response."""
        try:
            # Try to extract JSON from the response
            if "```json" in raw_response:
                json_start = raw_response.find("```json") + 7
                json_end = raw_response.find("```", json_start)
                json_str = raw_response[json_start:json_end].strip()
            elif "{" in raw_response and "}" in raw_response:
                json_start = raw_response.find("{")
                json_end = raw_response.rfind("}") + 1
                json_str = raw_response[json_start:json_end]
            else:
                # Fallback to plain text
                return {
                    "explanation": raw_response,
                    "confidence": 0.7,
                    "key_factors": ["LLM-generated explanation"],
                    "risk_analysis": {
                        "primary_risks": ["Unable to parse"],
                        "positive_indicators": ["Unable to parse"],
                        "recommendations": ["Unable to parse"]
                    }
                }
            
            return json.loads(json_str)
            
        except json.JSONDecodeError:
            # Fallback to plain text
            return {
                "explanation": raw_response,
                "confidence": 0.7,
                "key_factors": ["LLM-generated explanation"],
                "risk_analysis": {
                    "primary_risks": ["Unable to parse"],
                    "positive_indicators": ["Unable to parse"],
                    "recommendations": ["Unable to parse"]
                }
            }
    
    def _generate_fallback_explanation(self, request: CreditExplanationRequest) -> CreditExplanationResponse:
        """Generate fallback explanation when LLM is not available."""
        decision = request.credit_decision
        risk_score = request.risk_score
        amount = request.requested_amount
        
        # Generate contextual explanation
        if decision == "APPROVED":
            explanation = f"Credit approved for ${amount:,.2f} with a risk score of {risk_score:.3f}"
            if request.bnpl_offered:
                explanation += ". BNPL option available for flexible payment terms."
            key_factors = ["credit_worthiness", "payment_history", "debt_ratio"]
        elif decision == "DECLINED":
            explanation = f"Credit declined for ${amount:,.2f} due to risk score of {risk_score:.3f}"
            key_factors = ["high_risk_score", "credit_utilization", "payment_history"]
        else:  # REVIEW
            explanation = f"Credit application under review for ${amount:,.2f} with risk score of {risk_score:.3f}"
            key_factors = ["moderate_risk", "additional_verification", "manual_review"]
        
        # Add risk analysis
        risk_analysis = {
            "primary_risks": ["credit_utilization", "payment_history"] if risk_score > 0.5 else [],
            "positive_indicators": ["stable_income", "low_utilization"] if risk_score < 0.3 else [],
            "recommendations": ["maintain_payment_history", "reduce_utilization"] if risk_score > 0.4 else ["continue_good_habits"]
        }
        
        # BNPL explanation if offered
        bnpl_explanation = None
        if request.bnpl_offered and request.bnpl_terms:
            bnpl_explanation = f"BNPL available with {request.bnpl_terms.get('installments', 4)} payments of ${request.bnpl_terms.get('installment_amount', amount/4):.2f}"
        
        return CreditExplanationResponse(
            explanation=explanation,
            confidence=0.6,
            key_factors=key_factors,
            risk_analysis=risk_analysis,
            bnpl_explanation=bnpl_explanation,
            model_provenance={
                "model_name": "fallback",
                "provider": "okra_deterministic",
                "status": "fallback_mode",
                "message": "Azure OpenAI not available, using deterministic explanation"
            },
            processing_time_ms=0,
            tokens_used=0
        )


# Global explainer instance
_explainer: Optional[OkraLLMExplainer] = None


def get_credit_explainer() -> OkraLLMExplainer:
    """Get the global credit explainer instance."""
    global _explainer
    if _explainer is None:
        _explainer = OkraLLMExplainer()
    return _explainer


def explain_credit_decision_llm(
    credit_decision: str,
    risk_score: float,
    requested_amount: float,
    available_credit: float,
    bnpl_offered: bool,
    customer_context: Dict[str, Any],
    model_features: Dict[str, float],
    bnpl_terms: Optional[Dict[str, Any]] = None,
    reason_codes: Optional[List[str]] = None
) -> Optional[CreditExplanationResponse]:
    """
    Generate LLM explanation for credit decision.
    
    Args:
        credit_decision: Credit decision (APPROVED, DECLINED, REVIEW)
        risk_score: Credit risk score (0.0-1.0)
        requested_amount: Requested credit amount
        available_credit: Available credit limit
        bnpl_offered: Whether BNPL was offered
        customer_context: Customer context and features
        model_features: ML model features and scores
        bnpl_terms: BNPL terms if offered
        reason_codes: Reason codes for decision
        
    Returns:
        CreditExplanationResponse with explanation
    """
    request = CreditExplanationRequest(
        credit_decision=credit_decision,
        risk_score=risk_score,
        requested_amount=requested_amount,
        available_credit=available_credit,
        bnpl_offered=bnpl_offered,
        bnpl_terms=bnpl_terms,
        customer_context=customer_context,
        model_features=model_features,
        reason_codes=reason_codes or []
    )
    
    explainer = get_credit_explainer()
    return explainer.explain_credit_decision(request)


def is_credit_llm_configured() -> bool:
    """Check if credit LLM explanation service is configured."""
    explainer = get_credit_explainer()
    return explainer.is_configured()

