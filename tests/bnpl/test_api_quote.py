"""
Tests for BNPL API quote endpoints.
"""

from typing import Any, Dict

import pytest
from fastapi.testclient import TestClient

from okra.api import app


@pytest.fixture
def client() -> TestClient:
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def valid_bnpl_request() -> Dict[str, Any]:
    """Valid BNPL quote request."""
    return {"amount": 1500.0, "tenor": 6, "on_time_rate": 0.95, "utilization": 0.3}


def test_bnpl_quote_endpoint_success(
    client: TestClient, valid_bnpl_request: Dict[str, Any]
) -> None:
    """Test successful BNPL quote request."""
    response = client.post("/bnpl/quote", json=valid_bnpl_request)

    assert response.status_code == 200

    data = response.json()

    # Check required fields
    required_fields = [
        "limit",
        "apr",
        "term_months",
        "monthly_payment",
        "score",
        "approved",
        "key_signals",
        "components",
    ]

    for field in required_fields:
        assert field in data

    # Validate data types and ranges
    assert isinstance(data["limit"], (int, float))
    assert data["limit"] > 0

    assert isinstance(data["apr"], (int, float))
    assert data["apr"] >= 15.0  # Minimum base APR

    assert isinstance(data["term_months"], int)
    assert 1 <= data["term_months"] <= 12

    assert isinstance(data["monthly_payment"], (int, float))
    assert data["monthly_payment"] > 0

    assert isinstance(data["score"], (int, float))
    assert 0.0 <= data["score"] <= 1.0

    assert isinstance(data["approved"], bool)

    assert isinstance(data["key_signals"], dict)
    assert isinstance(data["components"], dict)


def test_bnpl_quote_endpoint_deterministic(
    client: TestClient, valid_bnpl_request: Dict[str, Any]
) -> None:
    """Test that BNPL quotes are deterministic."""
    # Make multiple requests with same parameters
    responses = []
    for _ in range(3):
        response = client.post("/bnpl/quote", json=valid_bnpl_request)
        assert response.status_code == 200
        responses.append(response.json())

    # All responses should be identical
    first_response = responses[0]
    for response in responses[1:]:
        assert response["score"] == first_response["score"]
        assert response["limit"] == first_response["limit"]
        assert response["apr"] == first_response["apr"]
        assert response["term_months"] == first_response["term_months"]
        assert response["monthly_payment"] == first_response["monthly_payment"]
        assert response["approved"] == first_response["approved"]


def test_bnpl_quote_endpoint_with_ce(
    client: TestClient, valid_bnpl_request: Dict[str, Any]
) -> None:
    """Test BNPL quote with CloudEvent emission."""
    response = client.post("/bnpl/quote?emit_ce=true", json=valid_bnpl_request)

    assert response.status_code == 200

    data = response.json()

    # Should include CloudEvent data
    assert "cloud_event" in data
    assert "trace_id" in data

    cloud_event = data["cloud_event"]
    trace_id = data["trace_id"]

    # Validate CloudEvent structure
    assert cloud_event["type"] == "ocn.okra.bnpl_quote.v1"
    assert cloud_event["source"] == "okra"
    assert cloud_event["subject"] == trace_id
    assert cloud_event["specversion"] == "1.0"
    assert cloud_event["datacontenttype"] == "application/json"

    # Validate CloudEvent data
    ce_data = cloud_event["data"]
    assert "quote" in ce_data
    assert "features" in ce_data
    assert "key_signals" in ce_data
    assert "timestamp" in ce_data
    assert "metadata" in ce_data


def test_bnpl_quote_endpoint_validation_amount_too_low(client: TestClient) -> None:
    """Test validation for amount below minimum."""
    request = {
        "amount": 50.0,  # Below minimum
        "tenor": 6,
        "on_time_rate": 0.95,
        "utilization": 0.3,
    }

    response = client.post("/bnpl/quote", json=request)
    assert response.status_code == 422  # Validation error


def test_bnpl_quote_endpoint_validation_amount_too_high(client: TestClient) -> None:
    """Test validation for amount above maximum."""
    request = {
        "amount": 10000.0,  # Above maximum
        "tenor": 6,
        "on_time_rate": 0.95,
        "utilization": 0.3,
    }

    response = client.post("/bnpl/quote", json=request)
    assert response.status_code == 422  # Validation error


def test_bnpl_quote_endpoint_validation_tenor_too_low(client: TestClient) -> None:
    """Test validation for tenor below minimum."""
    request = {
        "amount": 1500.0,
        "tenor": 0,  # Below minimum
        "on_time_rate": 0.95,
        "utilization": 0.3,
    }

    response = client.post("/bnpl/quote", json=request)
    assert response.status_code == 422  # Validation error


def test_bnpl_quote_endpoint_validation_tenor_too_high(client: TestClient) -> None:
    """Test validation for tenor above maximum."""
    request = {
        "amount": 1500.0,
        "tenor": 15,  # Above maximum
        "on_time_rate": 0.95,
        "utilization": 0.3,
    }

    response = client.post("/bnpl/quote", json=request)
    assert response.status_code == 422  # Validation error


def test_bnpl_quote_endpoint_validation_on_time_rate_out_of_range(client: TestClient) -> None:
    """Test validation for on_time_rate out of range."""
    request = {
        "amount": 1500.0,
        "tenor": 6,
        "on_time_rate": 1.5,  # Above maximum
        "utilization": 0.3,
    }

    response = client.post("/bnpl/quote", json=request)
    assert response.status_code == 422  # Validation error


def test_bnpl_quote_endpoint_validation_utilization_out_of_range(client: TestClient) -> None:
    """Test validation for utilization out of range."""
    request = {
        "amount": 1500.0,
        "tenor": 6,
        "on_time_rate": 0.95,
        "utilization": -0.1,  # Below minimum
    }

    response = client.post("/bnpl/quote", json=request)
    assert response.status_code == 422  # Validation error


def test_bnpl_quote_endpoint_missing_required_fields(client: TestClient) -> None:
    """Test validation for missing required fields."""
    # Missing amount
    request = {"tenor": 6, "on_time_rate": 0.95, "utilization": 0.3}

    response = client.post("/bnpl/quote", json=request)
    assert response.status_code == 422  # Validation error

    # Missing tenor
    request = {"amount": 1500.0, "on_time_rate": 0.95, "utilization": 0.3}

    response = client.post("/bnpl/quote", json=request)
    assert response.status_code == 422  # Validation error


def test_bnpl_quote_endpoint_optional_fields_defaults(client: TestClient) -> None:
    """Test that optional fields use default values."""
    request = {
        "amount": 1500.0,
        "tenor": 6,
        # on_time_rate and utilization should default to 0.0
    }

    response = client.post("/bnpl/quote", json=request)
    assert response.status_code == 200

    data = response.json()

    # Should still produce valid results with defaults
    assert 0.0 <= data["score"] <= 1.0
    assert data["limit"] > 0
    assert data["apr"] >= 15.0


def test_bnpl_quote_endpoint_key_signals_structure(
    client: TestClient, valid_bnpl_request: Dict[str, Any]
) -> None:
    """Test that key_signals have expected structure."""
    response = client.post("/bnpl/quote", json=valid_bnpl_request)
    assert response.status_code == 200

    data = response.json()
    key_signals = data["key_signals"]

    # Check required signals
    required_signals = [
        "amount_signal",
        "tenor_signal",
        "payment_signal",
        "utilization_signal",
        "risk_signal",
    ]

    for signal in required_signals:
        assert signal in key_signals
        assert isinstance(key_signals[signal], str)
        assert key_signals[signal]  # Not empty


def test_bnpl_quote_endpoint_components_structure(
    client: TestClient, valid_bnpl_request: Dict[str, Any]
) -> None:
    """Test that components have expected structure."""
    response = client.post("/bnpl/quote", json=valid_bnpl_request)
    assert response.status_code == 200

    data = response.json()
    components = data["components"]

    # Check required components
    required_components = ["amount_score", "tenor_score", "on_time_score", "utilization_score"]

    for component in required_components:
        assert component in components
        assert isinstance(components[component], (int, float))
        assert 0.0 <= components[component] <= 1.0


def test_bnpl_quote_endpoint_response_shape_consistency(client: TestClient) -> None:
    """Test that response shape is consistent across different inputs."""
    test_cases = [
        {"amount": 500.0, "tenor": 3, "on_time_rate": 0.8, "utilization": 0.5},
        {"amount": 2000.0, "tenor": 9, "on_time_rate": 0.99, "utilization": 0.1},
        {"amount": 3500.0, "tenor": 12, "on_time_rate": 0.7, "utilization": 0.8},
    ]

    for test_case in test_cases:
        response = client.post("/bnpl/quote", json=test_case)
        assert response.status_code == 200

        data = response.json()

        # All responses should have same structure
        assert all(
            field in data
            for field in [
                "limit",
                "apr",
                "term_months",
                "monthly_payment",
                "score",
                "approved",
                "key_signals",
                "components",
            ]
        )

        # All responses should have valid data types
        assert isinstance(data["limit"], (int, float))
        assert isinstance(data["apr"], (int, float))
        assert isinstance(data["term_months"], int)
        assert isinstance(data["monthly_payment"], (int, float))
        assert isinstance(data["score"], (int, float))
        assert isinstance(data["approved"], bool)
        assert isinstance(data["key_signals"], dict)
        assert isinstance(data["components"], dict)
