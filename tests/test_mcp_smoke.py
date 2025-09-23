import pytest
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from fastapi.testclient import TestClient
from fastapi import FastAPI
from mcp.server import router as mcp_router

# Create a test FastAPI app and include the MCP router
@pytest.fixture(scope="module")
def client():
    app = FastAPI()
    app.include_router(mcp_router)
    with TestClient(app) as c:
        yield c

def test_mcp_get_status(client):
    """Test MCP getStatus verb returns agent status."""
    response = client.post(
        "/mcp/invoke",
        json={"verb": "getStatus", "args": {}}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is True
    assert data["data"]["agent"] == "okra"
    assert data["data"]["status"] == "active"

def test_mcp_get_credit_quote(client):
    """Test MCP getCreditQuote verb returns deterministic stub quote."""
    response = client.post(
        "/mcp/invoke",
        json={"verb": "getCreditQuote", "args": {}}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is True
    assert data["data"]["agent"] == "okra"
    assert data["data"]["quote_id"] == "quote_stub_12345"
    assert data["data"]["approved"] is True
    assert data["data"]["credit_limit"] == 25000.0
    assert data["data"]["apr"] == 8.5
    assert data["data"]["term_months"] == 12
    assert data["data"]["monthly_payment"] == 2196.75
    assert data["data"]["review_required"] is False
    assert "reasons" in data["data"]
    assert "description" in data["data"]

def test_mcp_unsupported_verb(client):
    """Test MCP with unsupported verb returns error."""
    response = client.post(
        "/mcp/invoke",
        json={"verb": "unsupportedVerb", "args": {}}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is False
    assert "Unsupported verb" in data["error"]

def test_mcp_missing_verb(client):
    """Test MCP with missing verb returns validation error."""
    response = client.post(
        "/mcp/invoke",
        json={"args": {}}
    )
    assert response.status_code == 422  # FastAPI validation error
    data = response.json()
    assert "detail" in data
    assert "Field required" in data["detail"][0]["msg"]

def test_mcp_invalid_json(client):
    """Test MCP with invalid JSON returns error."""
    response = client.post(
        "/mcp/invoke",
        data="invalid json"
    )
    assert response.status_code == 422  # FastAPI validation error
