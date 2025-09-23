from typing import Any, Dict
from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()

class MCPRequest(BaseModel):
    """MCP request model."""
    verb: str
    args: Dict[str, Any] = {}

class MCPResponse(BaseModel):
    """MCP response model."""
    ok: bool
    data: Any = None
    error: Any = None

@router.post("/mcp/invoke", response_model=MCPResponse)
async def invoke_mcp_verb(request: MCPRequest) -> MCPResponse:
    """
    Handle MCP protocol requests.

    Supported verbs:
    - getStatus: Returns agent status
    - getCreditQuote: Returns deterministic stub credit quote
    """
    try:
        if request.verb == "getStatus":
            return MCPResponse(ok=True, data={"agent": "okra", "status": "active"})
        elif request.verb == "getCreditQuote":
            # Return deterministic stub credit quote
            return MCPResponse(
                ok=True,
                data={
                    "agent": "okra",
                    "quote_id": "quote_stub_12345",
                    "approved": True,
                    "credit_limit": 25000.0,
                    "apr": 8.5,
                    "term_months": 12,
                    "monthly_payment": 2196.75,
                    "reasons": ["Good credit profile", "Low debt-to-income ratio"],
                    "review_required": False,
                    "policy_version": "v1.0",
                    "description": "Deterministic stub credit quote for testing"
                }
            )
        else:
            return MCPResponse(ok=False, error=f"Unsupported verb: {request.verb}")
    except Exception as e:
        return MCPResponse(ok=False, error=str(e))
