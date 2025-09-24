"""
FastAPI service for Okra credit quotes.
"""

from decimal import Decimal
from typing import Any, Dict, Optional

from fastapi import FastAPI, HTTPException, Query, status
from pydantic import BaseModel, Field

from .policies import CreditPolicies, CreditRequest, CreditProfile
from .events import emit_credit_quote_event
from .bnpl import score_bnpl, generate_bnpl_quote, validate_features
from .ce import emit_bnpl_quote_ce, create_bnpl_quote_payload, get_trace_id
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from mcp.server import router as mcp_router


app = FastAPI(
    title="Okra Credit Agent",
    description="Open Credit Agent providing credit quotes and policy evaluation",
    version="0.1.0",
)

# Include MCP router
app.include_router(mcp_router)


# Pydantic models for API
class AP2Mandate(BaseModel):
    """AP2-aligned mandate for credit requests."""

    actor: Dict[str, Any] = Field(..., description="Actor information")
    cart: Dict[str, Any] = Field(..., description="Cart/transaction information")
    payment: Dict[str, Any] = Field(..., description="Payment context")


class CreditQuoteRequest(BaseModel):
    """Credit quote request."""

    mandate: AP2Mandate = Field(..., description="AP2-aligned mandate")
    credit_profile: Optional[Dict[str, Any]] = Field(None, description="Credit profile information")
    requested_amount: float = Field(..., ge=1000, le=50000, description="Requested credit amount")
    term_months: int = Field(..., ge=1, le=60, description="Loan term in months")
    purpose: str = Field("general", description="Loan purpose")


class CreditQuoteResponse(BaseModel):
    """Credit quote response."""

    quote_id: str = Field(..., description="Unique quote identifier")
    approved: bool = Field(..., description="Whether credit is approved")
    credit_limit: float = Field(..., ge=0, description="Approved credit limit")
    apr: float = Field(..., ge=0, le=100, description="Annual Percentage Rate")
    term_months: int = Field(..., ge=1, le=60, description="Loan term in months")
    monthly_payment: float = Field(..., ge=0, description="Estimated monthly payment")
    reasons: list[str] = Field(..., description="Reasons for decision")
    review_required: bool = Field(False, description="Whether manual review is required")
    policy_version: str = Field("v1.0.0", description="Policy version used")


class BNPLQuoteRequest(BaseModel):
    """BNPL quote request."""

    amount: float = Field(..., ge=100, le=5000, description="Requested BNPL amount")
    tenor: int = Field(..., ge=1, le=12, description="Payment term in months")
    on_time_rate: float = Field(0.0, ge=0.0, le=1.0, description="Historical on-time payment rate")
    utilization: float = Field(0.0, ge=0.0, le=1.0, description="Current credit utilization")


class BNPLQuoteResponse(BaseModel):
    """BNPL quote response."""

    limit: float = Field(..., ge=0, description="Approved BNPL limit")
    apr: float = Field(..., ge=0, description="Annual Percentage Rate")
    term_months: int = Field(..., ge=1, le=12, description="Payment term in months")
    monthly_payment: float = Field(..., ge=0, description="Monthly payment amount")
    score: float = Field(..., ge=0, le=1, description="BNPL risk score")
    approved: bool = Field(..., description="Whether BNPL is approved")
    key_signals: Dict[str, Any] = Field(..., description="Key risk signals")
    components: Dict[str, float] = Field(..., description="Score components")


@app.get("/", response_model=Dict[str, Any])
async def root():
    """Root endpoint with API information."""
    return {
        "service": "Okra Credit Agent",
        "version": "0.1.0",
        "status": "operational",
        "endpoints": {
            "credit_quote": "/credit/quote",
            "bnpl_quote": "/bnpl/quote",
            "policies": "/policies",
            "health": "/health",
        },
    }


@app.get("/health", response_model=Dict[str, str])
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "okra-credit-agent"}


@app.get("/policies", response_model=Dict[str, Any])
async def get_policies():
    """Get current credit policies and parameters."""
    return CreditPolicies.list_policies()


@app.post("/credit/quote", response_model=CreditQuoteResponse, status_code=status.HTTP_200_OK)
async def get_credit_quote(request: CreditQuoteRequest):
    """
    Get a credit quote based on AP2 mandate and credit profile.

    This endpoint:
    1. Extracts relevant information from the AP2 mandate
    2. Evaluates the request using deterministic policy rules
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
            amount=Decimal(str(request.requested_amount)),
            term_months=request.term_months,
            purpose=request.purpose,
            actor_id=actor_id,
            profile=credit_profile,
        )

        # Evaluate using policies
        quote = CreditPolicies.evaluate_credit_request(credit_request)

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

        # Emit CloudEvent for the quote (optional)
        try:
            await emit_credit_quote_event(
                quote_id=quote_id, actor_id=actor_id, mandate=request.mandate, quote=quote
            )
        except Exception as e:
            # Don't fail the request if event emission fails
            print(f"Warning: Failed to emit credit quote event: {e}")

        return response

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing credit quote request: {str(e)}",
        )


@app.post("/bnpl/quote")
async def get_bnpl_quote(
    request: BNPLQuoteRequest,
    emit_ce: bool = Query(False, description="Emit CloudEvent for BNPL quote"),
) -> Dict[str, Any]:
    """
    Get a BNPL (Buy Now, Pay Later) quote with deterministic scoring.

    Args:
        request: BNPL quote request with amount, tenor, payment history
        emit_ce: Whether to emit CloudEvent for the quote

    Returns:
        BNPL quote with limit, APR, term, and risk score
    """
    try:
        # Validate and normalize features
        features = validate_features(request.model_dump())

        # Score BNPL application
        scoring_result = score_bnpl(features, random_state=42)

        # Generate BNPL quote
        quote = generate_bnpl_quote(
            score=scoring_result["score"], amount=features["amount"], tenor=features["tenor"]
        )

        # Create response dictionary
        response_dict = {
            "limit": quote["limit"],
            "apr": quote["apr"],
            "term_months": quote["term_months"],
            "monthly_payment": quote["monthly_payment"],
            "score": quote["score"],
            "approved": quote["approved"],
            "key_signals": scoring_result["key_signals"],
            "components": scoring_result["components"],
        }

        # Emit CloudEvent if requested
        if emit_ce:
            trace_id = get_trace_id()
            payload = create_bnpl_quote_payload(quote, features, scoring_result["key_signals"])
            ce_event = emit_bnpl_quote_ce(trace_id, payload)

            # Add CloudEvent to response (for testing purposes)
            # In production, this would be emitted to an event bus
            response_dict["cloud_event"] = ce_event
            response_dict["trace_id"] = trace_id

        return response_dict

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing BNPL quote request: {str(e)}",
        )


@app.get("/credit/quote/{quote_id}", response_model=CreditQuoteResponse)
async def get_quote_by_id(quote_id: str):
    """
    Retrieve a credit quote by ID (stub implementation).

    In a production system, this would retrieve quotes from a database.
    """
    # Stub implementation - in production this would query a database
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Quote retrieval by ID not yet implemented",
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("okra.api:app", host="0.0.0.0", port=8000, reload=True)  # nosec B104
