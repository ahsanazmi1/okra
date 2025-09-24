"""
Tests for BNPL CloudEvents functionality.
"""

import json
import uuid


from okra.ce import (
    emit_bnpl_quote_ce,
    validate_ce_schema,
    create_bnpl_quote_payload,
    get_trace_id,
    format_ce_for_logging,
)


def test_get_trace_id_generates_uuid() -> None:
    """Test that get_trace_id generates a valid UUID."""
    trace_id = get_trace_id()
    assert isinstance(trace_id, str)
    assert len(trace_id) == 36  # UUID format
    assert uuid.UUID(trace_id, version=4)


def test_create_bnpl_quote_payload_structure() -> None:
    """Test that create_bnpl_quote_payload returns the correct structure."""
    quote = {
        "limit": 1200.0,
        "apr": 18.5,
        "term_months": 6,
        "monthly_payment": 200.0,
        "score": 0.75,
        "approved": True,
    }

    features = {"amount": 1500.0, "tenor": 6, "on_time_rate": 0.95, "utilization": 0.3}

    key_signals = {
        "amount_signal": "moderate_amount",
        "tenor_signal": "medium_term",
        "payment_signal": "excellent_history",
        "utilization_signal": "low_utilization",
        "risk_signal": "low_risk",
    }

    payload = create_bnpl_quote_payload(quote, features, key_signals)

    assert "quote" in payload
    assert "features" in payload
    assert "key_signals" in payload
    assert "timestamp" in payload
    assert "metadata" in payload

    assert payload["quote"] == quote
    assert payload["features"] == features
    assert payload["key_signals"] == key_signals

    assert "service" in payload["metadata"]
    assert payload["metadata"]["service"] == "okra"
    assert payload["metadata"]["feature"] == "bnpl_scoring"


def test_emit_bnpl_quote_ce_structure() -> None:
    """Test that emit_bnpl_quote_ce creates a valid CloudEvent structure."""
    trace_id = get_trace_id()
    payload = {
        "quote": {
            "limit": 1200.0,
            "apr": 18.5,
            "term_months": 6,
            "monthly_payment": 200.0,
            "score": 0.75,
            "approved": True,
        },
        "features": {"amount": 1500.0, "tenor": 6},
        "key_signals": {"risk_signal": "low_risk"},
    }

    event = emit_bnpl_quote_ce(trace_id, payload)

    assert "specversion" in event
    assert "type" in event
    assert "source" in event
    assert "id" in event
    assert "time" in event
    assert "subject" in event
    assert "datacontenttype" in event
    assert "data" in event

    assert event["specversion"] == "1.0"
    assert event["type"] == "ocn.okra.bnpl_quote.v1"
    assert event["source"] == "okra"
    assert event["subject"] == trace_id
    assert event["datacontenttype"] == "application/json"
    assert event["data"] == payload


def test_validate_ce_schema_valid_event() -> None:
    """Test validate_ce_schema with a valid CloudEvent."""
    trace_id = get_trace_id()
    payload = create_bnpl_quote_payload(
        quote={
            "limit": 1200.0,
            "apr": 18.5,
            "term_months": 6,
            "monthly_payment": 200.0,
            "score": 0.75,
            "approved": True,
        },
        features={"amount": 1500.0, "tenor": 6},
        key_signals={"risk_signal": "low_risk"},
    )

    event = emit_bnpl_quote_ce(trace_id, payload)
    assert validate_ce_schema(event) is True


def test_validate_ce_schema_invalid_event_missing_field() -> None:
    """Test validate_ce_schema with a CloudEvent missing a required field."""
    trace_id = get_trace_id()
    payload = create_bnpl_quote_payload(
        quote={
            "limit": 1200.0,
            "apr": 18.5,
            "term_months": 6,
            "monthly_payment": 200.0,
            "score": 0.75,
            "approved": True,
        },
        features={"amount": 1500.0, "tenor": 6},
        key_signals={"risk_signal": "low_risk"},
    )

    event = emit_bnpl_quote_ce(trace_id, payload)
    del event["type"]  # Remove a required field
    assert validate_ce_schema(event) is False


def test_validate_ce_schema_invalid_event_wrong_type() -> None:
    """Test validate_ce_schema with a CloudEvent having wrong type."""
    trace_id = get_trace_id()
    payload = create_bnpl_quote_payload(
        quote={
            "limit": 1200.0,
            "apr": 18.5,
            "term_months": 6,
            "monthly_payment": 200.0,
            "score": 0.75,
            "approved": True,
        },
        features={"amount": 1500.0, "tenor": 6},
        key_signals={"risk_signal": "low_risk"},
    )

    event = emit_bnpl_quote_ce(trace_id, payload)
    event["type"] = "ocn.orca.decision.v1"  # Wrong type
    assert validate_ce_schema(event) is False


def test_validate_ce_schema_invalid_event_wrong_source() -> None:
    """Test validate_ce_schema with a CloudEvent having wrong source."""
    trace_id = get_trace_id()
    payload = create_bnpl_quote_payload(
        quote={
            "limit": 1200.0,
            "apr": 18.5,
            "term_months": 6,
            "monthly_payment": 200.0,
            "score": 0.75,
            "approved": True,
        },
        features={"amount": 1500.0, "tenor": 6},
        key_signals={"risk_signal": "low_risk"},
    )

    event = emit_bnpl_quote_ce(trace_id, payload)
    event["source"] = "orion"  # Wrong source
    assert validate_ce_schema(event) is False


def test_validate_ce_schema_invalid_data_missing_quote_field() -> None:
    """Test validate_ce_schema with data missing a required quote field."""
    trace_id = get_trace_id()
    payload = create_bnpl_quote_payload(
        quote={
            "limit": 1200.0,
            "apr": 18.5,
            "term_months": 6,
            "monthly_payment": 200.0,
            "score": 0.75,
            # "approved": True  # Missing field
        },
        features={"amount": 1500.0, "tenor": 6},
        key_signals={"risk_signal": "low_risk"},
    )

    event = emit_bnpl_quote_ce(trace_id, payload)
    assert validate_ce_schema(event) is False


def test_validate_ce_schema_invalid_data_wrong_score_type() -> None:
    """Test validate_ce_schema with data having wrong score type."""
    trace_id = get_trace_id()
    payload = create_bnpl_quote_payload(
        quote={
            "limit": 1200.0,
            "apr": 18.5,
            "term_months": 6,
            "monthly_payment": 200.0,
            "score": "not_a_number",  # Wrong type
            "approved": True,
        },
        features={"amount": 1500.0, "tenor": 6},
        key_signals={"risk_signal": "low_risk"},
    )

    event = emit_bnpl_quote_ce(trace_id, payload)
    assert validate_ce_schema(event) is False


def test_validate_ce_schema_invalid_data_score_out_of_range() -> None:
    """Test validate_ce_schema with data having score out of range."""
    trace_id = get_trace_id()
    payload = create_bnpl_quote_payload(
        quote={
            "limit": 1200.0,
            "apr": 18.5,
            "term_months": 6,
            "monthly_payment": 200.0,
            "score": 1.5,  # Out of range
            "approved": True,
        },
        features={"amount": 1500.0, "tenor": 6},
        key_signals={"risk_signal": "low_risk"},
    )

    event = emit_bnpl_quote_ce(trace_id, payload)
    assert validate_ce_schema(event) is False


def test_validate_ce_schema_invalid_data_wrong_approved_type() -> None:
    """Test validate_ce_schema with data having wrong approved type."""
    trace_id = get_trace_id()
    payload = create_bnpl_quote_payload(
        quote={
            "limit": 1200.0,
            "apr": 18.5,
            "term_months": 6,
            "monthly_payment": 200.0,
            "score": 0.75,
            "approved": "yes",  # Wrong type
        },
        features={"amount": 1500.0, "tenor": 6},
        key_signals={"risk_signal": "low_risk"},
    )

    event = emit_bnpl_quote_ce(trace_id, payload)
    assert validate_ce_schema(event) is False


def test_format_ce_for_logging() -> None:
    """Test that CloudEvent is formatted correctly for logging."""
    trace_id = "test-trace-123"
    payload = create_bnpl_quote_payload(
        quote={
            "limit": 1200.0,
            "apr": 18.5,
            "term_months": 6,
            "monthly_payment": 200.0,
            "score": 0.75,
            "approved": True,
        },
        features={"amount": 1500.0, "tenor": 6},
        key_signals={"risk_signal": "low_risk"},
    )

    event = emit_bnpl_quote_ce(trace_id, payload)
    formatted = format_ce_for_logging(event)

    assert isinstance(formatted, str)

    # Should be valid JSON
    parsed = json.loads(formatted)
    assert parsed == event

    # Should contain key information
    assert "ocn.okra.bnpl_quote.v1" in formatted
    assert "test-trace-123" in formatted


def test_end_to_end_ce_validation() -> None:
    """Test end-to-end CloudEvent creation and validation."""
    # Create BNPL quote payload
    quote = {
        "limit": 1200.0,
        "apr": 18.5,
        "term_months": 6,
        "monthly_payment": 200.0,
        "score": 0.75,
        "approved": True,
    }

    features = {"amount": 1500.0, "tenor": 6, "on_time_rate": 0.95, "utilization": 0.3}

    key_signals = {
        "amount_signal": "moderate_amount",
        "tenor_signal": "medium_term",
        "payment_signal": "excellent_history",
        "utilization_signal": "low_utilization",
        "risk_signal": "low_risk",
    }

    payload = create_bnpl_quote_payload(quote, features, key_signals)

    # Emit CloudEvent
    trace_id = get_trace_id()
    event = emit_bnpl_quote_ce(trace_id, payload)

    # Validate the event
    assert validate_ce_schema(event) is True

    # Check that data matches payload
    assert event["data"] == payload

    # Check that event has correct type and source
    assert event["type"] == "ocn.okra.bnpl_quote.v1"
    assert event["source"] == "okra"
    assert event["subject"] == trace_id


def test_ce_event_id_uniqueness() -> None:
    """Test that CloudEvent IDs are unique."""
    trace_id = get_trace_id()
    payload = {
        "quote": {"score": 0.5, "approved": True},
        "features": {"amount": 1000.0},
        "key_signals": {"risk_signal": "medium_risk"},
    }

    # Generate multiple events
    events = []
    for _ in range(5):
        event = emit_bnpl_quote_ce(trace_id, payload)
        events.append(event)

    # All event IDs should be unique
    event_ids = [event["id"] for event in events]
    assert len(set(event_ids)) == len(event_ids)

    # All events should have valid UUIDs
    for event_id in event_ids:
        assert uuid.UUID(event_id, version=4)


def test_ce_event_timestamp_format() -> None:
    """Test that CloudEvent timestamps are in correct ISO format."""
    trace_id = get_trace_id()
    payload = {
        "quote": {"score": 0.5, "approved": True},
        "features": {"amount": 1000.0},
        "key_signals": {"risk_signal": "medium_risk"},
    }

    event = emit_bnpl_quote_ce(trace_id, payload)

    # Should be valid ISO timestamp
    import datetime

    timestamp = datetime.datetime.fromisoformat(event["time"].replace("Z", "+00:00"))
    assert isinstance(timestamp, datetime.datetime)

    # Should be recent (within last minute)
    now = datetime.datetime.now(datetime.timezone.utc)
    time_diff = abs((now - timestamp).total_seconds())
    assert time_diff < 60  # Within 1 minute
