"""
Okra CloudEvents module.

Handles emission and validation of CloudEvents for BNPL quotes.
"""

import json
import uuid
from datetime import datetime, timezone
from typing import Any, Dict

from pydantic import BaseModel, Field


class BNPLQuoteEvent(BaseModel):
    """CloudEvent model for Okra BNPL quotes."""

    specversion: str = "1.0"
    type: str = "ocn.okra.bnpl_quote.v1"
    source: str = "okra"
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    time: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    subject: str  # trace_id
    datacontenttype: str = "application/json"
    data: Dict[str, Any]


def emit_bnpl_quote_ce(trace_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Emit a CloudEvent for BNPL quote.

    Args:
        trace_id: Trace ID for the request
        payload: BNPL quote payload

    Returns:
        CloudEvent envelope
    """
    event = BNPLQuoteEvent(subject=trace_id, data=payload)

    return event.model_dump()


def validate_ce_schema(event: Dict[str, Any]) -> bool:
    """
    Validate CloudEvent against ocn.okra.bnpl_quote.v1 schema.

    Args:
        event: CloudEvent to validate

    Returns:
        True if valid, False otherwise
    """
    try:
        # Check required fields
        required_fields = [
            "specversion",
            "type",
            "source",
            "id",
            "time",
            "subject",
            "datacontenttype",
            "data",
        ]

        for field in required_fields:
            if field not in event:
                return False

        # Validate specversion
        if event["specversion"] != "1.0":
            return False

        # Validate type
        if event["type"] != "ocn.okra.bnpl_quote.v1":
            return False

        # Validate source
        if event["source"] != "okra":
            return False

        # Validate datacontenttype
        if event["datacontenttype"] != "application/json":
            return False

        # Validate data structure
        data = event["data"]
        if not isinstance(data, dict):
            return False

        # Check required data fields - handle nested structure
        if "quote" in data:
            # Nested structure from create_bnpl_quote_payload
            quote = data["quote"]
            required_fields = [
                "limit",
                "apr",
                "term_months",
                "monthly_payment",
                "score",
                "approved",
            ]
            for field in required_fields:
                if field not in quote:
                    return False

            # Validate score is a number between 0 and 1
            score = quote["score"]
            if not isinstance(score, (int, float)) or not (0 <= score <= 1):
                return False

            # Validate approved is boolean
            if not isinstance(quote["approved"], bool):
                return False
        else:
            # Direct structure (legacy)
            required_data_fields = [
                "limit",
                "apr",
                "term_months",
                "monthly_payment",
                "score",
                "approved",
            ]
            for field in required_data_fields:
                if field not in data:
                    return False

            # Validate score is a number between 0 and 1
            score = data["score"]
            if not isinstance(score, (int, float)) or not (0 <= score <= 1):
                return False

            # Validate approved is boolean
            if not isinstance(data["approved"], bool):
                return False

        return True

    except Exception:
        return False


def create_bnpl_quote_payload(
    quote: Dict[str, Any], features: Dict[str, Any], key_signals: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Create BNPL quote payload for CloudEvent.

    Args:
        quote: BNPL quote information
        features: Input features
        key_signals: Key signals from scoring

    Returns:
        Payload dictionary
    """
    return {
        "quote": quote,
        "features": features,
        "key_signals": key_signals,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "metadata": {"service": "okra", "version": "1.0.0", "feature": "bnpl_scoring"},
    }


def get_trace_id() -> str:
    """
    Generate or retrieve trace ID.

    Returns:
        Trace ID string
    """
    return str(uuid.uuid4())


def format_ce_for_logging(event: Dict[str, Any]) -> str:
    """
    Format CloudEvent for logging purposes.

    Args:
        event: CloudEvent dictionary

    Returns:
        Formatted string for logging
    """
    return json.dumps(event, indent=2)
