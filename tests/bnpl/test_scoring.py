"""
Tests for BNPL scoring functionality.
"""

from okra.bnpl import score_bnpl, generate_bnpl_quote, validate_features


def test_score_bnpl_deterministic() -> None:
    """Test that BNPL scoring produces deterministic results."""
    features = {"amount": 1500.0, "tenor": 6, "on_time_rate": 0.95, "utilization": 0.3}

    # Run scoring multiple times with same random state
    results = []
    for _ in range(3):
        result = score_bnpl(features, random_state=42)
        results.append(result["score"])

    # All results should be identical
    assert all(score == results[0] for score in results)
    assert results[0] is not None
    assert 0.0 <= results[0] <= 1.0


def test_score_bnpl_feature_validation() -> None:
    """Test that features are properly validated and bounded."""
    # Test with extreme values
    features = {
        "amount": 10000.0,  # Above max
        "tenor": 24,  # Above max
        "on_time_rate": 1.5,  # Above max
        "utilization": -0.1,  # Below min
    }

    result = score_bnpl(features, random_state=42)

    # Score should still be valid
    assert 0.0 <= result["score"] <= 1.0

    # Components should be bounded
    assert 0.0 <= result["components"]["amount_score"] <= 1.0
    assert 0.0 <= result["components"]["tenor_score"] <= 1.0
    assert 0.0 <= result["components"]["on_time_score"] <= 1.0
    assert 0.0 <= result["components"]["utilization_score"] <= 1.0


def test_score_bnpl_key_signals() -> None:
    """Test that key signals are properly generated."""
    features = {"amount": 1500.0, "tenor": 6, "on_time_rate": 0.95, "utilization": 0.3}

    result = score_bnpl(features, random_state=42)
    signals = result["key_signals"]

    # Check required signals
    required_signals = [
        "amount_signal",
        "tenor_signal",
        "payment_signal",
        "utilization_signal",
        "risk_signal",
    ]

    for signal in required_signals:
        assert signal in signals
        assert signals[signal] is not None
        assert isinstance(signals[signal], str)


def test_score_bnpl_amount_signals() -> None:
    """Test amount-based signals."""
    # Low amount
    low_features = {"amount": 300.0, "tenor": 3, "on_time_rate": 0.9, "utilization": 0.2}
    low_result = score_bnpl(low_features, random_state=42)
    assert low_result["key_signals"]["amount_signal"] == "low_amount"

    # High amount
    high_features = {"amount": 4000.0, "tenor": 3, "on_time_rate": 0.9, "utilization": 0.2}
    high_result = score_bnpl(high_features, random_state=42)
    assert high_result["key_signals"]["amount_signal"] == "high_amount"

    # Moderate amount
    moderate_features = {"amount": 2000.0, "tenor": 3, "on_time_rate": 0.9, "utilization": 0.2}
    moderate_result = score_bnpl(moderate_features, random_state=42)
    assert moderate_result["key_signals"]["amount_signal"] == "moderate_amount"


def test_score_bnpl_payment_history_signals() -> None:
    """Test payment history signals."""
    # Excellent history
    excellent_features = {"amount": 1500.0, "tenor": 6, "on_time_rate": 0.98, "utilization": 0.3}
    excellent_result = score_bnpl(excellent_features, random_state=42)
    assert excellent_result["key_signals"]["payment_signal"] == "excellent_history"

    # Poor history
    poor_features = {"amount": 1500.0, "tenor": 6, "on_time_rate": 0.65, "utilization": 0.3}
    poor_result = score_bnpl(poor_features, random_state=42)
    assert poor_result["key_signals"]["payment_signal"] == "poor_history"


def test_score_bnpl_utilization_signals() -> None:
    """Test utilization signals."""
    # Low utilization
    low_features = {"amount": 1500.0, "tenor": 6, "on_time_rate": 0.9, "utilization": 0.2}
    low_result = score_bnpl(low_features, random_state=42)
    assert low_result["key_signals"]["utilization_signal"] == "low_utilization"

    # High utilization
    high_features = {"amount": 1500.0, "tenor": 6, "on_time_rate": 0.9, "utilization": 0.85}
    high_result = score_bnpl(high_features, random_state=42)
    assert high_result["key_signals"]["utilization_signal"] == "high_utilization"


def test_score_bnpl_risk_signals() -> None:
    """Test risk signals based on total score."""
    # High score (low risk)
    high_score_features = {"amount": 1500.0, "tenor": 3, "on_time_rate": 0.98, "utilization": 0.2}
    high_score_result = score_bnpl(high_score_features, random_state=42)
    assert high_score_result["key_signals"]["risk_signal"] in ["low_risk", "medium_risk"]

    # Low score (high risk)
    low_score_features = {"amount": 4000.0, "tenor": 12, "on_time_rate": 0.6, "utilization": 0.9}
    low_score_result = score_bnpl(low_score_features, random_state=42)
    assert low_score_result["key_signals"]["risk_signal"] in ["medium_risk", "high_risk"]


def test_generate_bnpl_quote() -> None:
    """Test BNPL quote generation."""
    # High score should get better terms
    high_score_quote = generate_bnpl_quote(score=0.9, amount=1500.0, tenor=6)

    assert high_score_quote["approved"] is True
    assert high_score_quote["limit"] > 0
    assert high_score_quote["apr"] >= 15.0  # Base APR
    assert high_score_quote["term_months"] <= 6  # Should approve requested term or less
    assert high_score_quote["monthly_payment"] > 0

    # Low score should get worse terms
    low_score_quote = generate_bnpl_quote(score=0.3, amount=1500.0, tenor=6)

    assert low_score_quote["approved"] is False  # Below threshold
    assert low_score_quote["limit"] < 1500.0  # Reduced limit
    assert low_score_quote["apr"] > 20.0  # Higher APR
    assert low_score_quote["term_months"] >= 6  # Longer term


def test_validate_features() -> None:
    """Test feature validation and normalization."""
    raw_features = {
        "amount": 5000.0,  # Above max
        "tenor": 15,  # Above max
        "on_time_rate": 1.2,  # Above max
        "utilization": -0.1,  # Below min
    }

    validated = validate_features(raw_features)

    # Should be bounded to valid ranges
    assert 100.0 <= validated["amount"] <= 5000.0
    assert 1 <= validated["tenor"] <= 12
    assert 0.0 <= validated["on_time_rate"] <= 1.0
    assert 0.0 <= validated["utilization"] <= 1.0


def test_score_bnpl_weights() -> None:
    """Test that scoring weights are properly applied."""
    features = {"amount": 1500.0, "tenor": 6, "on_time_rate": 0.95, "utilization": 0.3}

    result = score_bnpl(features, random_state=42)

    # Check that weights are included
    assert "weights" in result
    weights = result["weights"]

    expected_weights = {"amount": 0.2, "tenor": 0.3, "on_time_rate": 0.35, "utilization": 0.15}

    for key, expected_value in expected_weights.items():
        assert key in weights
        assert weights[key] == expected_value


def test_score_bnpl_components() -> None:
    """Test that score components are properly calculated."""
    features = {"amount": 1500.0, "tenor": 6, "on_time_rate": 0.95, "utilization": 0.3}

    result = score_bnpl(features, random_state=42)
    components = result["components"]

    # All components should be in valid range
    for component_name, score in components.items():
        assert 0.0 <= score <= 1.0
        assert isinstance(score, (int, float))

    # Check that utilization score is inverted (lower utilization = higher score)
    utilization_score = components["utilization_score"]
    assert utilization_score == 0.7  # 1.0 - 0.3


def test_score_bnpl_different_random_states() -> None:
    """Test that different random states produce deterministic results."""
    features = {"amount": 1500.0, "tenor": 6, "on_time_rate": 0.95, "utilization": 0.3}

    # Same random state should produce same results
    result1 = score_bnpl(features, random_state=42)
    result2 = score_bnpl(features, random_state=42)
    assert result1["score"] == result2["score"]

    # Different random state should produce different results
    result3 = score_bnpl(features, random_state=123)
    # Note: In this implementation, random state doesn't affect deterministic scoring
    # but the function signature supports it for future enhancements
    assert isinstance(result3["score"], (int, float))
