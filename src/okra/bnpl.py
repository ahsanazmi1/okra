"""
Okra BNPL (Buy Now, Pay Later) scoring module.

Provides deterministic scoring for BNPL credit decisions.
"""

import random
from typing import Any, Dict

# BNPL configuration constants
MIN_AMOUNT = 100.0
MAX_AMOUNT = 5000.0
MIN_TENOR = 1  # months
MAX_TENOR = 12  # months
MIN_SCORE = 0.0
MAX_SCORE = 1.0

# Scoring weights
AMOUNT_WEIGHT = 0.2
TENOR_WEIGHT = 0.3
ON_TIME_RATE_WEIGHT = 0.35
UTILIZATION_WEIGHT = 0.15


def score_bnpl(features: Dict[str, Any], *, random_state: int = 42) -> Dict[str, Any]:
    """
    Score BNPL application using deterministic algorithm.

    Args:
        features: BNPL features containing amount, tenor, on_time_rate, utilization
        random_state: Random seed for deterministic scoring (default: 42)

    Returns:
        Dictionary with score and key_signals
    """
    # Set random seed for deterministic results
    random.seed(random_state)

    # Extract and validate features
    amount = float(features.get("amount", 0.0))
    tenor = int(features.get("tenor", 1))
    on_time_rate = float(features.get("on_time_rate", 0.0))
    utilization = float(features.get("utilization", 0.0))

    # Validate feature ranges
    amount = max(MIN_AMOUNT, min(MAX_AMOUNT, amount))
    tenor = max(MIN_TENOR, min(MAX_TENOR, tenor))
    on_time_rate = max(0.0, min(1.0, on_time_rate))
    utilization = max(0.0, min(1.0, utilization))

    # Calculate individual component scores
    amount_score = _calculate_amount_score(amount)
    tenor_score = _calculate_tenor_score(tenor)
    on_time_score = on_time_rate  # Direct mapping
    utilization_score = 1.0 - utilization  # Lower utilization is better

    # Weighted total score
    total_score = (
        amount_score * AMOUNT_WEIGHT
        + tenor_score * TENOR_WEIGHT
        + on_time_score * ON_TIME_RATE_WEIGHT
        + utilization_score * UTILIZATION_WEIGHT
    )

    # Ensure score is bounded
    total_score = max(MIN_SCORE, min(MAX_SCORE, total_score))

    # Generate key signals
    key_signals = _generate_key_signals(amount, tenor, on_time_rate, utilization, total_score)

    return {
        "score": round(total_score, 3),
        "key_signals": key_signals,
        "components": {
            "amount_score": round(amount_score, 3),
            "tenor_score": round(tenor_score, 3),
            "on_time_score": round(on_time_score, 3),
            "utilization_score": round(utilization_score, 3),
        },
        "weights": {
            "amount": AMOUNT_WEIGHT,
            "tenor": TENOR_WEIGHT,
            "on_time_rate": ON_TIME_RATE_WEIGHT,
            "utilization": UTILIZATION_WEIGHT,
        },
    }


def _calculate_amount_score(amount: float) -> float:
    """Calculate amount component score (moderate amounts score higher)."""
    # Normalize amount to [0, 1] range
    normalized_amount = (amount - MIN_AMOUNT) / (MAX_AMOUNT - MIN_AMOUNT)

    # Optimal amount range is around 40-60% of max (moderate purchases)
    optimal_range_start = 0.4
    optimal_range_end = 0.6

    if optimal_range_start <= normalized_amount <= optimal_range_end:
        # In optimal range - higher score
        return 0.9 + 0.1 * (1.0 - abs(normalized_amount - 0.5) / 0.1)
    else:
        # Outside optimal range - lower score
        distance_from_optimal = min(
            abs(normalized_amount - optimal_range_start), abs(normalized_amount - optimal_range_end)
        )
        return max(0.3, 0.9 - distance_from_optimal * 2.0)


def _calculate_tenor_score(tenor: int) -> float:
    """Calculate tenor component score (shorter terms score higher)."""
    # Shorter terms are generally better for BNPL
    # Score decreases as tenor increases
    normalized_tenor = (tenor - MIN_TENOR) / (MAX_TENOR - MIN_TENOR)

    # Exponential decay for longer terms
    return 1.0 - (normalized_tenor**1.5)


def _generate_key_signals(
    amount: float, tenor: int, on_time_rate: float, utilization: float, total_score: float
) -> Dict[str, Any]:
    """Generate key signals for the BNPL decision."""
    signals = {}

    # Amount-based signals
    if amount < 500:
        signals["amount_signal"] = "low_amount"
    elif amount > 3000:
        signals["amount_signal"] = "high_amount"
    else:
        signals["amount_signal"] = "moderate_amount"

    # Tenor-based signals
    if tenor <= 3:
        signals["tenor_signal"] = "short_term"
    elif tenor >= 9:
        signals["tenor_signal"] = "long_term"
    else:
        signals["tenor_signal"] = "medium_term"

    # Payment history signals
    if on_time_rate >= 0.95:
        signals["payment_signal"] = "excellent_history"
    elif on_time_rate >= 0.85:
        signals["payment_signal"] = "good_history"
    elif on_time_rate >= 0.70:
        signals["payment_signal"] = "fair_history"
    else:
        signals["payment_signal"] = "poor_history"

    # Utilization signals
    if utilization <= 0.3:
        signals["utilization_signal"] = "low_utilization"
    elif utilization >= 0.8:
        signals["utilization_signal"] = "high_utilization"
    else:
        signals["utilization_signal"] = "moderate_utilization"

    # Overall risk signals
    if total_score >= 0.8:
        signals["risk_signal"] = "low_risk"
    elif total_score >= 0.6:
        signals["risk_signal"] = "medium_risk"
    else:
        signals["risk_signal"] = "high_risk"

    return signals


def generate_bnpl_quote(score: float, amount: float, tenor: int) -> Dict[str, Any]:
    """
    Generate BNPL quote based on score and parameters.

    Args:
        score: BNPL score (0-1)
        amount: Requested amount
        tenor: Requested tenor in months

    Returns:
        BNPL quote with limit, APR, and term
    """
    # Calculate approved limit (percentage of requested amount based on score)
    limit_multiplier = 0.5 + (score * 0.5)  # 50-100% of requested amount
    approved_limit = min(amount * limit_multiplier, MAX_AMOUNT)

    # Calculate APR based on score (lower score = higher APR)
    base_apr = 15.0  # Base APR for BNPL
    risk_adjustment = (1.0 - score) * 10.0  # 0-10% additional APR
    apr = base_apr + risk_adjustment

    # Determine term (may be adjusted based on score and tenor)
    if score >= 0.8:
        approved_term = tenor  # Approve requested term
    elif score >= 0.6:
        approved_term = min(tenor + 1, MAX_TENOR)  # Slightly longer term
    else:
        approved_term = min(tenor + 2, MAX_TENOR)  # Longer term for higher risk

    return {
        "limit": round(approved_limit, 2),
        "apr": round(apr, 2),
        "term_months": approved_term,
        "monthly_payment": round(approved_limit / approved_term, 2),
        "score": score,
        "approved": score >= 0.5,  # Minimum threshold for approval
    }


def validate_features(features: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate and normalize BNPL features.

    Args:
        features: Raw features dictionary

    Returns:
        Validated and normalized features
    """
    validated = {
        "amount": max(MIN_AMOUNT, min(MAX_AMOUNT, float(features.get("amount", MIN_AMOUNT)))),
        "tenor": max(MIN_TENOR, min(MAX_TENOR, int(features.get("tenor", MIN_TENOR)))),
        "on_time_rate": max(0.0, min(1.0, float(features.get("on_time_rate", 0.0)))),
        "utilization": max(0.0, min(1.0, float(features.get("utilization", 0.0)))),
    }

    return validated
