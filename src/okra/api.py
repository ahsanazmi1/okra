"""
FastAPI service for Okra credit quotes.
"""

from typing import Any, Dict, Optional

from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field

from .policies import CreditPolicies, CreditRequest
from .events import emit_credit_quote_event


app = FastAPI(
    title="Okra Credit Agent",
    description="Open Credit Agent providing credit quotes and policy evaluation",
    version="0.1.0",
)


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


@app.get("/", response_model=Dict[str, Any])
async def root():
    """Root endpoint with API information."""
    return {
        "service": "Okra Credit Agent",
        "version": "0.1.0",
        "status": "operational",
        "endpoints": {
            "credit_quote": "/credit/quote",
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
            credit_profile = request.credit_profile

        # Create credit request
        credit_request = CreditRequest(
            amount=request.requested_amount,
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

    uvicorn.run("okra.api:app", host="0.0.0.0", port=8000, reload=True)
