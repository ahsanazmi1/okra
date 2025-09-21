"""
MCP server for Okra credit agent.
"""

import asyncio
import json
import sys
from typing import Any, Dict, List, Optional

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.server import NotificationOptions, Server
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
from mcp.types import (
    CallToolRequest,
    CallToolResult,
    ListResourcesRequest,
    ListResourcesResult,
    ListToolsRequest,
    ListToolsResult,
    ReadResourceRequest,
    ReadResourceResult,
    Resource,
    TextContent,
    Tool,
)

from ..policies import CreditPolicies, CreditRequest, CreditProfile
from ..events import emit_credit_quote_event


# MCP Server instance
server = Server("okra-credit-agent")


@server.list_tools()
async def handle_list_tools() -> ListToolsResult:
    """List available tools."""
    tools = [
        Tool(
            name="getCreditQuote",
            description="Get a credit quote based on AP2 mandate and credit profile",
            inputSchema={
                "type": "object",
                "properties": {
                    "mandate": {
                        "type": "object",
                        "description": "AP2-aligned mandate with actor, cart, and payment context",
                        "properties": {
                            "actor": {"type": "object", "description": "Actor information"},
                            "cart": {"type": "object", "description": "Cart/transaction information"},
                            "payment": {"type": "object", "description": "Payment context"}
                        },
                        "required": ["actor", "cart", "payment"]
                    },
                    "credit_profile": {
                        "type": "object",
                        "description": "Credit profile information",
                        "properties": {
                            "credit_score": {"type": "integer", "minimum": 300, "maximum": 850},
                            "annual_income": {"type": "number", "minimum": 0},
                            "debt_to_income_ratio": {"type": "number", "minimum": 0, "maximum": 1},
                            "employment_status": {"type": "string"},
                            "credit_history_months": {"type": "integer", "minimum": 0}
                        }
                    },
                    "requested_amount": {"type": "number", "minimum": 0, "description": "Requested credit amount"},
                    "term_months": {"type": "integer", "minimum": 1, "maximum": 60, "description": "Loan term in months"},
                    "purpose": {"type": "string", "description": "Loan purpose", "default": "general"}
                },
                "required": ["mandate", "requested_amount", "term_months"]
            }
        ),
        Tool(
            name="listPolicies",
            description="List current credit policies and parameters",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        )
    ]
    return ListToolsResult(tools=tools)


@server.call_tool()
async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> CallToolResult:
    """Handle tool calls."""
    try:
        if name == "getCreditQuote":
            return await handle_get_credit_quote(arguments)
        elif name == "listPolicies":
            return await handle_list_policies()
        else:
            return CallToolResult(
                content=[TextContent(type="text", text=f"Unknown tool: {name}")],
                isError=True
            )
    except Exception as e:
        return CallToolResult(
            content=[TextContent(type="text", text=f"Error: {str(e)}")],
            isError=True
        )


async def handle_get_credit_quote(arguments: Dict[str, Any]) -> CallToolResult:
    """Handle getCreditQuote tool call."""
    try:
        # Extract arguments
        mandate = arguments["mandate"]
        requested_amount = arguments["requested_amount"]
        term_months = arguments["term_months"]
        purpose = arguments.get("purpose", "general")
        credit_profile_data = arguments.get("credit_profile")
        
        # Extract actor ID
        actor_id = mandate["actor"].get("id", "unknown")
        
        # Build credit profile if provided
        credit_profile = None
        if credit_profile_data:
            credit_profile = CreditProfile(**credit_profile_data)
        
        # Create credit request
        credit_request = CreditRequest(
            amount=requested_amount,
            term_months=term_months,
            purpose=purpose,
            actor_id=actor_id,
            profile=credit_profile
        )
        
        # Evaluate using policies
        quote = CreditPolicies.evaluate_credit_request(credit_request)
        
        # Generate quote ID
        quote_id = f"quote_{actor_id}_{hash(str(credit_request))}"
        
        # Emit CloudEvent (optional)
        try:
            await emit_credit_quote_event(
                quote_id=quote_id,
                actor_id=actor_id,
                mandate=mandate,
                quote=quote
            )
        except Exception as e:
            print(f"Warning: Failed to emit credit quote event: {e}")
        
        # Format response
        result = {
            "quote_id": quote_id,
            "approved": quote.approved,
            "credit_limit": float(quote.credit_limit),
            "apr": float(quote.apr),
            "term_months": quote.term_months,
            "monthly_payment": float(quote.monthly_payment),
            "reasons": quote.reasons,
            "review_required": quote.review_required,
            "policy_version": quote.policy_version
        }
        
        return CallToolResult(
            content=[TextContent(
                type="text",
                text=f"Credit Quote Result:\n{json.dumps(result, indent=2)}"
            )]
        )
        
    except KeyError as e:
        return CallToolResult(
            content=[TextContent(type="text", text=f"Missing required argument: {e}")],
            isError=True
        )
    except Exception as e:
        return CallToolResult(
            content=[TextContent(type="text", text=f"Error processing credit quote: {str(e)}")],
            isError=True
        )


async def handle_list_policies() -> CallToolResult:
    """Handle listPolicies tool call."""
    try:
        policies = CreditPolicies.list_policies()
        
        return CallToolResult(
            content=[TextContent(
                type="text",
                text=f"Current Credit Policies:\n{json.dumps(policies, indent=2)}"
            )]
        )
        
    except Exception as e:
        return CallToolResult(
            content=[TextContent(type="text", text=f"Error listing policies: {str(e)}")],
            isError=True
        )


@server.list_resources()
async def handle_list_resources() -> ListResourcesResult:
    """List available resources."""
    resources = [
        Resource(
            uri="okra://policies",
            name="Credit Policies",
            description="Current credit policies and parameters",
            mimeType="application/json"
        )
    ]
    return ListResourcesResult(resources=resources)


@server.read_resource()
async def handle_read_resource(uri: str) -> ReadResourceResult:
    """Read a resource."""
    if uri == "okra://policies":
        try:
            policies = CreditPolicies.list_policies()
            content = json.dumps(policies, indent=2)
            
            return ReadResourceResult(
                contents=[TextContent(type="text", text=content)]
            )
        except Exception as e:
            return ReadResourceResult(
                contents=[TextContent(type="text", text=f"Error reading policies: {str(e)}")]
            )
    else:
        return ReadResourceResult(
            contents=[TextContent(type="text", text=f"Unknown resource: {uri}")]
        )


async def main():
    """Main MCP server loop."""
    # Run server using stdio
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="okra-credit-agent",
                server_version="0.1.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={}
                )
            )
        )


if __name__ == "__main__":
    asyncio.run(main())
