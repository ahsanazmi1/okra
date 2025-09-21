"""
CloudEvents emitter for Okra credit quotes.
"""

from datetime import datetime, timezone
from typing import Any, Dict, Optional
from uuid import uuid4

from pydantic import BaseModel


class CreditQuoteEvent(BaseModel):
    """CloudEvent for credit quotes."""

    specversion: str = "1.0"
    id: str
    source: str
    type: str = "ocn.okra.credit_quote.v1"
    subject: Optional[str] = None
    time: str
    datacontenttype: str = "application/json"
    dataschema: Optional[str] = None
    data: Dict[str, Any]


class CreditQuoteData(BaseModel):
    """Data payload for credit quote events."""

    quote_id: str
    actor_id: str
    mandate: Dict[str, Any]
    quote_result: Dict[str, Any]
    policy_version: str
    timestamp: str


async def emit_credit_quote_event(
    quote_id: str,
    actor_id: str,
    mandate: Any,  # Can be AP2Mandate or Dict
    quote: Any,  # CreditQuote from policies
    source: str = "https://okra.ocn.ai/v1",
) -> CreditQuoteEvent:
    """
    Emit a CloudEvent for a credit quote.

    Args:
        quote_id: Unique quote identifier
        actor_id: Actor/borrower identifier
        mandate: AP2 mandate information
        quote: Credit quote result
        source: Event source URI

    Returns:
        CloudEvent object (in production, this would be sent to an event bus)
    """
    # Convert quote to dict for serialization
    quote_data = {
        "approved": quote.approved,
        "credit_limit": float(quote.credit_limit),
        "apr": float(quote.apr),
        "term_months": quote.term_months,
        "monthly_payment": float(quote.monthly_payment),
        "reasons": quote.reasons,
        "review_required": quote.review_required,
        "policy_version": quote.policy_version,
    }

    # Convert mandate to dict if it's a Pydantic model
    mandate_dict = mandate
    if hasattr(mandate, "model_dump"):
        mandate_dict = mandate.model_dump()
    elif hasattr(mandate, "dict"):
        mandate_dict = mandate.dict()

    # Create event data
    event_data = CreditQuoteData(
        quote_id=quote_id,
        actor_id=actor_id,
        mandate=mandate_dict,
        quote_result=quote_data,
        policy_version=quote.policy_version,
        timestamp=datetime.now(timezone.utc).isoformat(),
    )

    # Create CloudEvent
    event = CreditQuoteEvent(
        id=str(uuid4()),
        source=source,
        subject=actor_id,  # Use actor_id as subject
        time=datetime.now(timezone.utc).isoformat(),
        data=event_data.model_dump(),
    )

    # In production, this would send the event to an event bus
    # For now, we'll just log it
    print(f"Credit Quote Event: {event.model_dump_json()}")

    return event


# Inline schema for credit quote events
CREDIT_QUOTE_EVENT_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "$id": "https://schemas.ocn.ai/events/v1/okra.credit_quote.v1.schema.json",
    "title": "Okra Credit Quote CloudEvent",
    "description": "Schema for Okra credit quote events, following CloudEvents v1.0 specification.",
    "type": "object",
    "required": ["specversion", "id", "source", "type", "subject", "time", "data"],
    "properties": {
        "specversion": {
            "type": "string",
            "enum": ["1.0"],
            "description": "The version of the CloudEvents specification which the event uses.",
        },
        "id": {"type": "string", "description": "A unique identifier for the event."},
        "source": {
            "type": "string",
            "format": "uri-reference",
            "description": "The context in which the event happened. Often a URI.",
        },
        "type": {
            "type": "string",
            "enum": ["ocn.okra.credit_quote.v1"],
            "description": "The type of event, e.g., 'ocn.okra.credit_quote.v1'.",
        },
        "subject": {
            "type": "string",
            "description": "The subject of the event in the context of the event producer (e.g., actor_id).",
        },
        "time": {
            "type": "string",
            "format": "date-time",
            "description": "The time when the event occurred as a UTC ISO 8601 timestamp.",
        },
        "datacontenttype": {"type": "string", "description": "Content type of the data attribute."},
        "dataschema": {
            "type": ["string", "null"],
            "description": "A link to the schema that the data attribute adheres to.",
        },
        "data": {
            "type": "object",
            "description": "The credit quote payload.",
            "required": [
                "quote_id",
                "actor_id",
                "mandate",
                "quote_result",
                "policy_version",
                "timestamp",
            ],
            "properties": {
                "quote_id": {"type": "string", "description": "Unique quote identifier"},
                "actor_id": {"type": "string", "description": "Actor/borrower identifier"},
                "mandate": {"type": "object", "description": "AP2 mandate information"},
                "quote_result": {
                    "type": "object",
                    "description": "Credit quote result",
                    "required": [
                        "approved",
                        "credit_limit",
                        "apr",
                        "term_months",
                        "monthly_payment",
                        "reasons",
                        "review_required",
                        "policy_version",
                    ],
                    "properties": {
                        "approved": {"type": "boolean"},
                        "credit_limit": {"type": "number"},
                        "apr": {"type": "number"},
                        "term_months": {"type": "integer"},
                        "monthly_payment": {"type": "number"},
                        "reasons": {"type": "array", "items": {"type": "string"}},
                        "review_required": {"type": "boolean"},
                        "policy_version": {"type": "string"},
                    },
                },
                "policy_version": {"type": "string", "description": "Policy version used"},
                "timestamp": {
                    "type": "string",
                    "format": "date-time",
                    "description": "Event timestamp",
                },
            },
        },
    },
}
