"""
Deterministic policy rules for Okra credit decisions.
"""

from decimal import Decimal
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class CreditProfile(BaseModel):
    """Credit profile information for policy evaluation."""

    credit_score: Optional[int] = Field(None, ge=300, le=850, description="Credit score (300-850)")
    annual_income: Optional[Decimal] = Field(None, ge=0, description="Annual income in USD")
    debt_to_income_ratio: Optional[Decimal] = Field(None, ge=0, le=1, description="DTI ratio (0-1)")
    employment_status: Optional[str] = Field(None, description="Employment status")
    credit_history_months: Optional[int] = Field(
        None, ge=0, description="Credit history length in months"
    )


class CreditRequest(BaseModel):
    """Credit request information."""

    amount: Decimal = Field(..., gt=0, description="Requested credit amount")
    term_months: int = Field(..., ge=1, le=60, description="Loan term in months")
    purpose: str = Field(..., description="Loan purpose")
    actor_id: str = Field(..., description="Actor/borrower identifier")
    profile: Optional[CreditProfile] = Field(None, description="Credit profile information")


class CreditQuote(BaseModel):
    """Credit quote response."""

    approved: bool = Field(..., description="Whether credit is approved")
    credit_limit: Decimal = Field(..., ge=0, description="Approved credit limit")
    apr: Decimal = Field(..., ge=0, le=100, description="Annual Percentage Rate")
    term_months: int = Field(..., ge=1, le=60, description="Loan term in months")
    monthly_payment: Decimal = Field(..., ge=0, description="Estimated monthly payment")
    reasons: List[str] = Field(..., description="Reasons for decision")
    review_required: bool = Field(False, description="Whether manual review is required")
    policy_version: str = Field("v1.0.0", description="Policy version used")


class CreditPolicies:
    """Deterministic credit policies for Okra."""

    # Policy thresholds
    MIN_CREDIT_SCORE_AUTO_APPROVE = 720
    MIN_CREDIT_SCORE_REVIEW = 650
    MAX_DTI_RATIO = Decimal("0.45")
    MIN_ANNUAL_INCOME = Decimal("25000")
    MAX_LOAN_AMOUNT = Decimal("50000")
    MIN_LOAN_AMOUNT = Decimal("1000")

    # Rate tiers
    RATE_TIERS = [
        (720, Decimal("8.99")),  # Excellent credit
        (680, Decimal("12.99")),  # Good credit
        (650, Decimal("18.99")),  # Fair credit
        (600, Decimal("24.99")),  # Poor credit
        (0, Decimal("29.99")),  # Subprime
    ]

    @classmethod
    def evaluate_credit_request(cls, request: CreditRequest) -> CreditQuote:
        """
        Evaluate a credit request using deterministic policy rules.

        Args:
            request: Credit request information

        Returns:
            Credit quote with approval decision and terms
        """
        reasons = []
        approved = False
        review_required = False

        # Basic amount validation
        if request.amount < cls.MIN_LOAN_AMOUNT:
            reasons.append(
                f"Requested amount ${request.amount} below minimum ${cls.MIN_LOAN_AMOUNT}"
            )
            return cls._create_declined_quote(request, reasons)

        if request.amount > cls.MAX_LOAN_AMOUNT:
            reasons.append(
                f"Requested amount ${request.amount} exceeds maximum ${cls.MAX_LOAN_AMOUNT}"
            )
            return cls._create_declined_quote(request, reasons)

        # If no profile provided, require review
        if not request.profile:
            review_required = True
            reasons.append("No credit profile provided - manual review required")
            return cls._create_review_quote(request, reasons)

        profile = request.profile

        # Check minimum income
        if profile.annual_income and profile.annual_income < cls.MIN_ANNUAL_INCOME:
            reasons.append(
                f"Income ${profile.annual_income} below minimum ${cls.MIN_ANNUAL_INCOME}"
            )
            return cls._create_declined_quote(request, reasons)

        # Check debt-to-income ratio
        if profile.debt_to_income_ratio and profile.debt_to_income_ratio > cls.MAX_DTI_RATIO:
            reasons.append(
                f"DTI ratio {profile.debt_to_income_ratio:.2%} exceeds maximum {cls.MAX_DTI_RATIO:.2%}"
            )
            return cls._create_declined_quote(request, reasons)

        # Check credit score
        if not profile.credit_score:
            review_required = True
            reasons.append("No credit score provided - manual review required")
            return cls._create_review_quote(request, reasons)

        credit_score = profile.credit_score

        # Auto-approve for excellent credit
        if credit_score >= cls.MIN_CREDIT_SCORE_AUTO_APPROVE:
            approved = True
            reasons.append(f"Excellent credit score {credit_score} - auto-approved")
        elif credit_score >= cls.MIN_CREDIT_SCORE_REVIEW:
            review_required = True
            reasons.append(f"Good credit score {credit_score} - review required")
        else:
            reasons.append(f"Credit score {credit_score} below minimum threshold")
            return cls._create_declined_quote(request, reasons)

        # Calculate terms
        apr = cls._get_apr_for_score(credit_score)
        credit_limit = cls._calculate_credit_limit(request.amount, profile)

        # Calculate monthly payment
        monthly_rate = apr / 100 / 12
        monthly_payment = cls._calculate_monthly_payment(
            credit_limit, monthly_rate, request.term_months
        )

        if approved:
            reasons.append(f"Approved for ${credit_limit} at {apr}% APR")

        return CreditQuote(
            approved=approved,
            credit_limit=credit_limit,
            apr=apr,
            term_months=request.term_months,
            monthly_payment=monthly_payment,
            reasons=reasons,
            review_required=review_required,
            policy_version="v1.0.0",
        )

    @classmethod
    def _get_apr_for_score(cls, credit_score: int) -> Decimal:
        """Get APR based on credit score."""
        for min_score, apr in cls.RATE_TIERS:
            if credit_score >= min_score:
                return apr
        return cls.RATE_TIERS[-1][1]  # Default to highest rate

    @classmethod
    def _calculate_credit_limit(cls, requested_amount: Decimal, profile: CreditProfile) -> Decimal:
        """Calculate approved credit limit."""
        # Start with requested amount
        limit = requested_amount

        # Adjust based on income (max 30% of annual income)
        if profile.annual_income:
            max_by_income = profile.annual_income * Decimal("0.30")
            limit = min(limit, max_by_income)

        # Adjust based on credit score
        if profile.credit_score:
            if profile.credit_score >= 750:
                # Excellent credit - can go up to requested amount
                pass
            elif profile.credit_score >= 700:
                # Good credit - reduce by 10%
                limit = limit * Decimal("0.90")
            elif profile.credit_score >= 650:
                # Fair credit - reduce by 20%
                limit = limit * Decimal("0.80")
            else:
                # Poor credit - reduce by 30%
                limit = limit * Decimal("0.70")

        # Ensure minimum of $1000
        limit = max(limit, cls.MIN_LOAN_AMOUNT)

        return limit.quantize(Decimal("0.01"))

    @classmethod
    def _calculate_monthly_payment(
        cls, principal: Decimal, monthly_rate: Decimal, months: int
    ) -> Decimal:
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

    @classmethod
    def _create_declined_quote(cls, request: CreditRequest, reasons: List[str]) -> CreditQuote:
        """Create a declined credit quote."""
        return CreditQuote(
            approved=False,
            credit_limit=Decimal("0"),
            apr=Decimal("0"),
            term_months=request.term_months,
            monthly_payment=Decimal("0"),
            reasons=reasons,
            review_required=False,
            policy_version="v1.0.0",
        )

    @classmethod
    def _create_review_quote(cls, request: CreditRequest, reasons: List[str]) -> CreditQuote:
        """Create a quote requiring manual review."""
        # Provide estimated terms for review
        apr = cls.RATE_TIERS[1][1]  # Use "good" rate as estimate
        credit_limit = min(request.amount, cls.MAX_LOAN_AMOUNT * Decimal("0.80"))
        monthly_rate = apr / 100 / 12
        monthly_payment = cls._calculate_monthly_payment(
            credit_limit, monthly_rate, request.term_months
        )

        return CreditQuote(
            approved=False,
            credit_limit=credit_limit,
            apr=apr,
            term_months=request.term_months,
            monthly_payment=monthly_payment,
            reasons=reasons,
            review_required=True,
            policy_version="v1.0.0",
        )

    @classmethod
    def list_policies(cls) -> Dict[str, Any]:
        """List current policy parameters."""
        return {
            "policy_version": "v1.0.0",
            "thresholds": {
                "min_credit_score_auto_approve": cls.MIN_CREDIT_SCORE_AUTO_APPROVE,
                "min_credit_score_review": cls.MIN_CREDIT_SCORE_REVIEW,
                "max_dti_ratio": float(cls.MAX_DTI_RATIO),
                "min_annual_income": float(cls.MIN_ANNUAL_INCOME),
                "max_loan_amount": float(cls.MAX_LOAN_AMOUNT),
                "min_loan_amount": float(cls.MIN_LOAN_AMOUNT),
            },
            "rate_tiers": [
                {"min_score": score, "apr": float(apr)} for score, apr in cls.RATE_TIERS
            ],
        }
