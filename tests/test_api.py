"""
Tests for FastAPI service.
"""

import pytest
from fastapi.testclient import TestClient

from okra.api import app


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def sample_mandate():
    """Sample AP2 mandate for testing."""
    return {
        "actor": {
            "id": "user_12345",
            "type": "user",
            "profile": {
                "name": "John Doe",
                "email": "john@example.com"
            }
        },
        "cart": {
            "amount": "15000.00",
            "currency": "USD",
            "items": [
                {
                    "id": "item_001",
                    "name": "Home Improvement Loan",
                    "amount": "15000.00",
                    "quantity": 1,
                    "category": "Financial Services"
                }
            ],
            "geo": {
                "country": "US",
                "region": "CA",
                "city": "San Francisco"
            },
            "metadata": {}
        },
        "payment": {
            "method": "bank_transfer",
            "modality": {
                "type": "installment",
                "description": "Monthly payments"
            },
            "auth_requirements": ["bank_verification"],
            "metadata": {
                "bank_name": "Chase Bank",
                "account_type": "checking"
            }
        }
    }


@pytest.fixture
def sample_credit_profile():
    """Sample credit profile for testing."""
    return {
        "credit_score": 750,
        "annual_income": 85000,
        "debt_to_income_ratio": 0.28,
        "employment_status": "employed",
        "credit_history_months": 84
    }


class TestRootEndpoints:
    """Test root endpoints."""

    def test_root_endpoint(self, client):
        """Test root endpoint."""
        response = client.get("/")
        assert response.status_code == 200
        
        data = response.json()
        assert data["service"] == "Okra Credit Agent"
        assert data["version"] == "0.1.0"
        assert data["status"] == "operational"
        assert "credit_quote" in data["endpoints"]
        
    def test_health_check(self, client):
        """Test health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "okra-credit-agent"
        
    def test_get_policies(self, client):
        """Test get policies endpoint."""
        response = client.get("/policies")
        assert response.status_code == 200
        
        data = response.json()
        assert "policy_version" in data
        assert "thresholds" in data
        assert "rate_tiers" in data


class TestCreditQuote:
    """Test credit quote endpoint."""

    def test_credit_quote_approved(self, client, sample_mandate, sample_credit_profile):
        """Test credit quote for approved case."""
        request_data = {
            "mandate": sample_mandate,
            "credit_profile": sample_credit_profile,
            "requested_amount": 15000,
            "term_months": 36,
            "purpose": "home_improvement"
        }
        
        response = client.post("/credit/quote", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        assert "quote_id" in data
        assert data["approved"] is True
        assert data["credit_limit"] > 0
        assert data["apr"] > 0
        assert data["monthly_payment"] > 0
        assert data["term_months"] == 36
        assert len(data["reasons"]) > 0
        assert data["review_required"] is False
        assert data["policy_version"] == "v1.0.0"
        
    def test_credit_quote_review_required(self, client, sample_mandate):
        """Test credit quote for review required case."""
        credit_profile = {
            "credit_score": 680,  # Good but requires review
            "annual_income": 65000,
            "debt_to_income_ratio": 0.35
        }
        
        request_data = {
            "mandate": sample_mandate,
            "credit_profile": credit_profile,
            "requested_amount": 10000,
            "term_months": 24,
            "purpose": "debt_consolidation"
        }
        
        response = client.post("/credit/quote", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        assert "quote_id" in data
        assert data["approved"] is False
        assert data["review_required"] is True
        assert data["credit_limit"] > 0
        assert data["apr"] > 0
        assert "review required" in " ".join(data["reasons"])
        
    def test_credit_quote_declined(self, client, sample_mandate):
        """Test credit quote for declined case."""
        credit_profile = {
            "credit_score": 580,  # Poor credit
            "annual_income": 30000,
            "debt_to_income_ratio": 0.55
        }
        
        request_data = {
            "mandate": sample_mandate,
            "credit_profile": credit_profile,
            "requested_amount": 8000,
            "term_months": 12,
            "purpose": "emergency"
        }
        
        response = client.post("/credit/quote", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        assert "quote_id" in data
        assert data["approved"] is False
        assert data["review_required"] is False
        assert data["credit_limit"] == 0
        assert data["apr"] == 0
        assert data["monthly_payment"] == 0
        
    def test_credit_quote_no_profile(self, client, sample_mandate):
        """Test credit quote without credit profile."""
        request_data = {
            "mandate": sample_mandate,
            "requested_amount": 10000,
            "term_months": 24,
            "purpose": "general"
        }
        
        response = client.post("/credit/quote", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        assert "quote_id" in data
        assert data["approved"] is False
        assert data["review_required"] is True
        assert "manual review required" in " ".join(data["reasons"])
        
    def test_credit_quote_invalid_amount(self, client, sample_mandate, sample_credit_profile):
        """Test credit quote with invalid amount."""
        request_data = {
            "mandate": sample_mandate,
            "credit_profile": sample_credit_profile,
            "requested_amount": 100,  # Too small
            "term_months": 12,
            "purpose": "test"
        }
        
        response = client.post("/credit/quote", json=request_data)
        assert response.status_code == 422  # Validation error
        
    def test_credit_quote_invalid_term(self, client, sample_mandate, sample_credit_profile):
        """Test credit quote with invalid term."""
        request_data = {
            "mandate": sample_mandate,
            "credit_profile": sample_credit_profile,
            "requested_amount": 10000,
            "term_months": 0,  # Invalid
            "purpose": "test"
        }
        
        response = client.post("/credit/quote", json=request_data)
        assert response.status_code == 422  # Validation error
        
    def test_credit_quote_missing_mandate(self, client, sample_credit_profile):
        """Test credit quote with missing mandate."""
        request_data = {
            "credit_profile": sample_credit_profile,
            "requested_amount": 10000,
            "term_months": 24,
            "purpose": "test"
        }
        
        response = client.post("/credit/quote", json=request_data)
        assert response.status_code == 422  # Validation error


class TestQuoteRetrieval:
    """Test quote retrieval endpoint."""

    def test_get_quote_by_id_not_implemented(self, client):
        """Test getting quote by ID (not implemented yet)."""
        response = client.get("/credit/quote/nonexistent_id")
        assert response.status_code == 501
        assert "not yet implemented" in response.json()["detail"]


class TestDeterministicResults:
    """Test that results are deterministic."""

    def test_deterministic_quote_id(self, client, sample_mandate, sample_credit_profile):
        """Test that same inputs produce same quote ID."""
        request_data = {
            "mandate": sample_mandate,
            "credit_profile": sample_credit_profile,
            "requested_amount": 15000,
            "term_months": 36,
            "purpose": "home_improvement"
        }
        
        # Make two identical requests
        response1 = client.post("/credit/quote", json=request_data)
        response2 = client.post("/credit/quote", json=request_data)
        
        assert response1.status_code == 200
        assert response2.status_code == 200
        
        data1 = response1.json()
        data2 = response2.json()
        
        # Quote IDs should be the same
        assert data1["quote_id"] == data2["quote_id"]
        
        # Results should be identical
        assert data1["approved"] == data2["approved"]
        assert data1["credit_limit"] == data2["credit_limit"]
        assert data1["apr"] == data2["apr"]
        assert data1["monthly_payment"] == data2["monthly_payment"]
        
    def test_different_inputs_different_results(self, client, sample_mandate, sample_credit_profile):
        """Test that different inputs produce different results."""
        # First request
        request1 = {
            "mandate": sample_mandate,
            "credit_profile": sample_credit_profile,
            "requested_amount": 10000,
            "term_months": 24,
            "purpose": "test1"
        }
        
        # Second request with different amount
        request2 = {
            "mandate": sample_mandate,
            "credit_profile": sample_credit_profile,
            "requested_amount": 20000,  # Different amount
            "term_months": 24,
            "purpose": "test1"
        }
        
        response1 = client.post("/credit/quote", json=request1)
        response2 = client.post("/credit/quote", json=request2)
        
        assert response1.status_code == 200
        assert response2.status_code == 200
        
        data1 = response1.json()
        data2 = response2.json()
        
        # Quote IDs should be different
        assert data1["quote_id"] != data2["quote_id"]
        
        # Credit limits should be different
        assert data1["credit_limit"] != data2["credit_limit"]
