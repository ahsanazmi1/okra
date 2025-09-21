"""
Tests for credit policies.
"""

import pytest
from decimal import Decimal

from okra.policies import CreditPolicies, CreditProfile, CreditRequest, CreditQuote


class TestCreditProfile:
    """Test CreditProfile model."""

    def test_valid_profile(self):
        """Test valid credit profile."""
        profile = CreditProfile(
            credit_score=750,
            annual_income=Decimal("75000"),
            debt_to_income_ratio=Decimal("0.30"),
            employment_status="employed",
            credit_history_months=60
        )
        
        assert profile.credit_score == 750
        assert profile.annual_income == Decimal("75000")
        assert profile.debt_to_income_ratio == Decimal("0.30")
        
    def test_profile_validation(self):
        """Test profile validation."""
        # Invalid credit score
        with pytest.raises(ValueError):
            CreditProfile(credit_score=299)  # Too low
            
        with pytest.raises(ValueError):
            CreditProfile(credit_score=851)  # Too high
            
        # Invalid DTI ratio
        with pytest.raises(ValueError):
            CreditProfile(debt_to_income_ratio=Decimal("1.1"))  # Too high


class TestCreditRequest:
    """Test CreditRequest model."""

    def test_valid_request(self):
        """Test valid credit request."""
        profile = CreditProfile(credit_score=750)
        request = CreditRequest(
            amount=Decimal("10000"),
            term_months=36,
            purpose="home_improvement",
            actor_id="user_123",
            profile=profile
        )
        
        assert request.amount == Decimal("10000")
        assert request.term_months == 36
        assert request.purpose == "home_improvement"
        assert request.actor_id == "user_123"
        
    def test_request_validation(self):
        """Test request validation."""
        # Invalid amount
        with pytest.raises(ValueError):
            CreditRequest(
                amount=Decimal("-1000"),  # Negative
                term_months=12,
                purpose="test",
                actor_id="user_123"
            )
            
        # Invalid term
        with pytest.raises(ValueError):
            CreditRequest(
                amount=Decimal("10000"),
                term_months=0,  # Too low
                purpose="test",
                actor_id="user_123"
            )
            
        with pytest.raises(ValueError):
            CreditRequest(
                amount=Decimal("10000"),
                term_months=61,  # Too high
                purpose="test",
                actor_id="user_123"
            )


class TestCreditPolicies:
    """Test credit policy evaluation."""

    def test_excellent_credit_auto_approve(self):
        """Test auto-approval for excellent credit."""
        profile = CreditProfile(
            credit_score=750,
            annual_income=Decimal("100000"),
            debt_to_income_ratio=Decimal("0.25")
        )
        
        request = CreditRequest(
            amount=Decimal("15000"),
            term_months=36,
            purpose="home_improvement",
            actor_id="user_123",
            profile=profile
        )
        
        quote = CreditPolicies.evaluate_credit_request(request)
        
        assert quote.approved is True
        assert quote.credit_limit > 0
        assert quote.apr > 0
        assert quote.monthly_payment > 0
        assert quote.review_required is False
        assert "auto-approved" in " ".join(quote.reasons)
        
    def test_good_credit_review_required(self):
        """Test review required for good credit."""
        profile = CreditProfile(
            credit_score=680,
            annual_income=Decimal("75000"),
            debt_to_income_ratio=Decimal("0.35")
        )
        
        request = CreditRequest(
            amount=Decimal("10000"),
            term_months=24,
            purpose="debt_consolidation",
            actor_id="user_123",
            profile=profile
        )
        
        quote = CreditPolicies.evaluate_credit_request(request)
        
        assert quote.approved is False
        assert quote.review_required is True
        assert "review required" in " ".join(quote.reasons)
        
    def test_poor_credit_declined(self):
        """Test decline for poor credit."""
        profile = CreditProfile(
            credit_score=600,
            annual_income=Decimal("40000"),
            debt_to_income_ratio=Decimal("0.50")
        )
        
        request = CreditRequest(
            amount=Decimal("5000"),
            term_months=12,
            purpose="emergency",
            actor_id="user_123",
            profile=profile
        )
        
        quote = CreditPolicies.evaluate_credit_request(request)
        
        assert quote.approved is False
        assert quote.review_required is False
        assert quote.credit_limit == Decimal("0")
        assert quote.apr == Decimal("0")
        assert quote.monthly_payment == Decimal("0")
        
    def test_low_income_declined(self):
        """Test decline for low income."""
        profile = CreditProfile(
            credit_score=750,
            annual_income=Decimal("20000"),  # Below minimum
            debt_to_income_ratio=Decimal("0.20")
        )
        
        request = CreditRequest(
            amount=Decimal("10000"),
            term_months=24,
            purpose="test",
            actor_id="user_123",
            profile=profile
        )
        
        quote = CreditPolicies.evaluate_credit_request(request)
        
        assert quote.approved is False
        assert quote.review_required is False
        assert "below minimum" in " ".join(quote.reasons)
        
    def test_high_dti_declined(self):
        """Test decline for high debt-to-income ratio."""
        profile = CreditProfile(
            credit_score=750,
            annual_income=Decimal("100000"),
            debt_to_income_ratio=Decimal("0.50")  # Above maximum
        )
        
        request = CreditRequest(
            amount=Decimal("10000"),
            term_months=24,
            purpose="test",
            actor_id="user_123",
            profile=profile
        )
        
        quote = CreditPolicies.evaluate_credit_request(request)
        
        assert quote.approved is False
        assert quote.review_required is False
        assert "exceeds maximum" in " ".join(quote.reasons)
        
    def test_amount_validation(self):
        """Test amount validation."""
        profile = CreditProfile(credit_score=750)
        
        # Too small
        request = CreditRequest(
            amount=Decimal("500"),  # Below minimum
            term_months=12,
            purpose="test",
            actor_id="user_123",
            profile=profile
        )
        
        quote = CreditPolicies.evaluate_credit_request(request)
        assert quote.approved is False
        assert "below minimum" in " ".join(quote.reasons)
        
        # Too large
        request = CreditRequest(
            amount=Decimal("60000"),  # Above maximum
            term_months=12,
            purpose="test",
            actor_id="user_123",
            profile=profile
        )
        
        quote = CreditPolicies.evaluate_credit_request(request)
        assert quote.approved is False
        assert "exceeds maximum" in " ".join(quote.reasons)
        
    def test_no_profile_review_required(self):
        """Test review required when no profile provided."""
        request = CreditRequest(
            amount=Decimal("10000"),
            term_months=24,
            purpose="test",
            actor_id="user_123",
            profile=None
        )
        
        quote = CreditPolicies.evaluate_credit_request(request)
        
        assert quote.approved is False
        assert quote.review_required is True
        assert "manual review required" in " ".join(quote.reasons)
        
    def test_no_credit_score_review_required(self):
        """Test review required when no credit score provided."""
        profile = CreditProfile(
            annual_income=Decimal("75000"),
            debt_to_income_ratio=Decimal("0.30")
            # No credit_score
        )
        
        request = CreditRequest(
            amount=Decimal("10000"),
            term_months=24,
            purpose="test",
            actor_id="user_123",
            profile=profile
        )
        
        quote = CreditPolicies.evaluate_credit_request(request)
        
        assert quote.approved is False
        assert quote.review_required is True
        assert "manual review required" in " ".join(quote.reasons)
        
    def test_rate_tiers(self):
        """Test APR assignment based on credit score."""
        # Test different credit scores
        test_cases = [
            (800, Decimal("8.99")),  # Excellent
            (720, Decimal("8.99")),  # Excellent
            (700, Decimal("12.99")), # Good
            (680, Decimal("12.99")), # Good
            (650, Decimal("18.99")), # Fair
            (620, Decimal("24.99")), # Poor
            (580, Decimal("29.99"))  # Subprime
        ]
        
        for credit_score, expected_apr in test_cases:
            profile = CreditProfile(
                credit_score=credit_score,
                annual_income=Decimal("100000"),
                debt_to_income_ratio=Decimal("0.25")
            )
            
            request = CreditRequest(
                amount=Decimal("10000"),
                term_months=24,
                purpose="test",
                actor_id="user_123",
                profile=profile
            )
            
            quote = CreditPolicies.evaluate_credit_request(request)
            
            # For approved quotes, check APR
            if quote.approved or quote.review_required:
                assert quote.apr == expected_apr, f"Credit score {credit_score} should get APR {expected_apr}, got {quote.apr}"
                
    def test_list_policies(self):
        """Test listing policies."""
        policies = CreditPolicies.list_policies()
        
        assert "policy_version" in policies
        assert "thresholds" in policies
        assert "rate_tiers" in policies
        
        thresholds = policies["thresholds"]
        assert "min_credit_score_auto_approve" in thresholds
        assert "min_credit_score_review" in thresholds
        assert "max_dti_ratio" in thresholds
        assert "min_annual_income" in thresholds
        assert "max_loan_amount" in thresholds
        assert "min_loan_amount" in thresholds
        
        rate_tiers = policies["rate_tiers"]
        assert isinstance(rate_tiers, list)
        assert len(rate_tiers) > 0
        
        for tier in rate_tiers:
            assert "min_score" in tier
            assert "apr" in tier
