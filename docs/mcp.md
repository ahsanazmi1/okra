# Okra MCP Integration

Okra provides Model Context Protocol (MCP) integration for seamless interaction with AI agents and other MCP-compatible tools.

## MCP Server

The Okra MCP server exposes credit evaluation capabilities through standardized MCP tools and resources.

### Installation

```bash
# Install Okra with MCP support
pip install okra

# Run MCP server
python -m okra.mcp.server
```

### MCP Manifest

The server exposes the following capabilities:

**Tools:**
- `getCreditQuote`: Evaluate credit requests
- `listPolicies`: Get current policy parameters

**Resources:**
- `okra://policies`: Current credit policies (JSON)

## MCP Tools

### getCreditQuote

**Description:** Get a credit quote based on AP2 mandate and credit profile

**Input Schema:**
```json
{
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
    "requested_amount": {"type": "number", "minimum": 0},
    "term_months": {"type": "integer", "minimum": 1, "maximum": 60},
    "purpose": {"type": "string", "default": "general"}
  },
  "required": ["mandate", "requested_amount", "term_months"]
}
```

**Example Usage:**
```json
{
  "mandate": {
    "actor": {"id": "user_123", "type": "user"},
    "cart": {"amount": "10000", "currency": "USD"},
    "payment": {"method": "bank_transfer"}
  },
  "credit_profile": {
    "credit_score": 750,
    "annual_income": 75000,
    "debt_to_income_ratio": 0.30
  },
  "requested_amount": 10000,
  "term_months": 24,
  "purpose": "home_improvement"
}
```

**Response:**
```json
{
  "quote_id": "quote_user_123_1234567890",
  "approved": true,
  "credit_limit": 10000.0,
  "apr": 8.99,
  "term_months": 24,
  "monthly_payment": 459.71,
  "reasons": ["Excellent credit score 750 - auto-approved"],
  "review_required": false,
  "policy_version": "v1.0.0"
}
```

### listPolicies

**Description:** List current credit policies and parameters

**Input Schema:**
```json
{
  "type": "object",
  "properties": {},
  "required": []
}
```

**Response:**
```json
{
  "policy_version": "v1.0.0",
  "thresholds": {
    "min_credit_score_auto_approve": 720,
    "min_credit_score_review": 650,
    "max_dti_ratio": 0.45,
    "min_annual_income": 25000,
    "max_loan_amount": 50000,
    "min_loan_amount": 1000
  },
  "rate_tiers": [
    {"min_score": 720, "apr": 8.99},
    {"min_score": 680, "apr": 12.99},
    {"min_score": 650, "apr": 18.99},
    {"min_score": 600, "apr": 24.99},
    {"min_score": 0, "apr": 29.99}
  ]
}
```

## MCP Resources

### Credit Policies Resource

**URI:** `okra://policies`

**Description:** Current credit policies and parameters

**MIME Type:** `application/json`

**Content:**
```json
{
  "policy_version": "v1.0.0",
  "thresholds": {
    "min_credit_score_auto_approve": 720,
    "min_credit_score_review": 650,
    "max_dti_ratio": 0.45,
    "min_annual_income": 25000,
    "max_loan_amount": 50000,
    "min_loan_amount": 1000
  },
  "rate_tiers": [
    {"min_score": 720, "apr": 8.99},
    {"min_score": 680, "apr": 12.99},
    {"min_score": 650, "apr": 18.99},
    {"min_score": 600, "apr": 24.99},
    {"min_score": 0, "apr": 29.99}
  ]
}
```

## Integration Examples

### Claude Desktop Integration

Add to your Claude Desktop MCP configuration:

```json
{
  "mcpServers": {
    "okra": {
      "command": "python",
      "args": ["-m", "okra.mcp.server"],
      "env": {
        "OKRA_LOG_LEVEL": "INFO"
      }
    }
  }
}
```

### Programmatic Usage

```python
import asyncio
from mcp import ClientSession
from mcp.client.stdio import stdio_client

async def get_credit_quote():
    async with stdio_client(["python", "-m", "okra.mcp.server"]) as (read, write):
        async with ClientSession(read, write) as session:
            # Initialize session
            await session.initialize()

            # Get credit quote
            result = await session.call_tool(
                "getCreditQuote",
                {
                    "mandate": {
                        "actor": {"id": "user_123", "type": "user"},
                        "cart": {"amount": "10000", "currency": "USD"},
                        "payment": {"method": "bank_transfer"}
                    },
                    "credit_profile": {
                        "credit_score": 750,
                        "annual_income": 75000,
                        "debt_to_income_ratio": 0.30
                    },
                    "requested_amount": 10000,
                    "term_months": 24,
                    "purpose": "home_improvement"
                }
            )

            print(result.content[0].text)

# Run the example
asyncio.run(get_credit_quote())
```

### CLI Usage

```bash
# Start MCP server
python -m okra.mcp.server

# In another terminal, use MCP client
mcp-client okra://policies
mcp-tool okra getCreditQuote --mandate-file mandate.json
```

## Error Handling

### Tool Errors

The MCP server returns structured error responses:

```json
{
  "content": [
    {
      "type": "text",
      "text": "Error: Missing required argument: mandate"
    }
  ],
  "isError": true
}
```

### Common Error Types

- **Missing Arguments:** Required parameters not provided
- **Validation Errors:** Invalid input values
- **Policy Errors:** Credit policy evaluation failures
- **System Errors:** Internal processing failures

## Configuration

### Environment Variables

- `OKRA_LOG_LEVEL`: Logging level (default: INFO)
- `OKRA_POLICY_VERSION`: Policy version override
- `OKRA_RATE_LIMIT`: Rate limiting configuration

### MCP Server Parameters

The MCP server supports standard MCP configuration options:

- **Server Name:** `okra-credit-agent`
- **Server Version:** `0.1.0`
- **Capabilities:** Tools and Resources
- **Transport:** stdio (standard input/output)

## Security Considerations

### Input Validation
- All inputs are validated against schemas
- Credit scores and amounts have defined ranges
- Mandate structure is enforced

### Output Sanitization
- No sensitive data in error messages
- Consistent response format
- Audit logging of all requests

### Rate Limiting
- Configurable rate limits per client
- Protection against abuse
- Graceful degradation under load

## Monitoring & Debugging

### Logging
- Request/response logging
- Policy decision logging
- Error condition logging
- Performance metrics

### Debug Mode
Enable debug logging for detailed trace information:

```bash
OKRA_LOG_LEVEL=DEBUG python -m okra.mcp.server
```

### Health Checks
The MCP server includes built-in health monitoring:

- Tool availability checks
- Policy validation
- Resource accessibility
- Performance metrics

## Future Enhancements

### Planned Features
- **Resource Caching:** Cache policy resources for performance
- **Batch Processing:** Support for multiple quote requests
- **Custom Policies:** User-defined policy overrides
- **Advanced Analytics:** Quote pattern analysis
- **Integration Hooks:** Custom event handlers

### Extension Points
- **Custom Tools:** Additional MCP tools
- **Policy Plugins:** Pluggable policy engines
- **Event Handlers:** Custom event processing
- **Data Sources:** External data integration
