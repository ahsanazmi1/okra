# Okra — The Open Credit Agent

[![CI](https://github.com/ahsanazmi1/okra/actions/workflows/ci.yml/badge.svg)](https://github.com/ahsanazmi1/okra/actions/workflows/ci.yml)
[![Contracts Validation](https://github.com/ahsanazmi1/okra/actions/workflows/contracts.yml/badge.svg)](https://github.com/ahsanazmi1/okra/actions/workflows/contracts.yml)
[![Security Validation](https://github.com/ahsanazmi1/okra/actions/workflows/security.yml/badge.svg)](https://github.com/ahsanazmi1/okra/actions/workflows/security.yml)

**Okra** is the **open, transparent credit agent** for the [Open Checkout Network (OCN)](https://github.com/ocn-ai/ocn-common).

## Phase 2 — Explainability

🚧 **Currently in development** - Phase 2 focuses on AI-powered explainability and human-readable credit decision reasoning.

- **Status**: Active development on `phase-2-explainability` branch
- **Features**: LLM integration, explainability API endpoints, decision audit trails
- **Issue Tracker**: [Phase 2 Issues](https://github.com/ahsanazmi1/okra/issues?q=is%3Aopen+is%3Aissue+label%3Aphase-2)
- **Timeline**: Weeks 4-8 of OCN development roadmap

## Purpose

Okra provides intelligent credit decisions and quotes for the OCN ecosystem. Unlike traditional black-box credit systems, Okra offers:

- **Transparent Credit Policies** - Clear, auditable credit decision logic
- **Explainable AI** - Human-readable explanations for credit decisions
- **Open Architecture** - Integrates seamlessly with OCN protocols
- **MCP Integration** - Model Context Protocol support for agent interactions

## Quickstart (≤ 60s)

Get up and running with Okra in under a minute:

```bash
# Clone the repository
git clone https://github.com/ahsanazmi1/okra.git
cd okra

# Setup everything (venv, deps, pre-commit hooks)
make setup

# Run tests to verify everything works
make test

# Start the service
make run
```

**That's it!** 🎉

The service will be running at `http://localhost:8000`. Test the endpoints:

```bash
# Health check
curl http://localhost:8000/health

# MCP getStatus
curl -X POST http://localhost:8000/mcp/invoke \
  -H "Content-Type: application/json" \
  -d '{"verb": "getStatus", "args": {}}'

# MCP getCreditQuote
curl -X POST http://localhost:8000/mcp/invoke \
  -H "Content-Type: application/json" \
  -d '{"verb": "getCreditQuote", "args": {}}'
```

### Additional Commands

```bash
# Run linting checks
make lint

# Format code
make fmt

# Clean up
make clean
```

## API Endpoints

### Health Check
```bash
curl http://localhost:8000/health
```

### Credit Quote
```bash
curl -X POST http://localhost:8000/credit/quote \
  -H "Content-Type: application/json" \
  -d '{
    "mandate": {
      "actor": {"id": "customer_123"},
      "cart": {"total": 5000.0},
      "payment": {"method": "credit"}
    },
    "requested_amount": 10000,
    "term_months": 12,
    "purpose": "general"
  }'
```

### BNPL Quote
```bash
# Basic BNPL quote
curl -X POST http://localhost:8000/bnpl/quote \
  -H "Content-Type: application/json" \
  -d '{
    "amount": 1500.0,
    "tenor": 6,
    "on_time_rate": 0.95,
    "utilization": 0.3
  }'

# BNPL quote with CloudEvent emission
curl -X POST "http://localhost:8000/bnpl/quote?emit_ce=true" \
  -H "Content-Type: application/json" \
  -d '{
    "amount": 1500.0,
    "tenor": 6,
    "on_time_rate": 0.95,
    "utilization": 0.3
  }'
```

#### BNPL Quote Response Example
```json
{
  "limit": 1200.0,
  "apr": 18.5,
  "term_months": 6,
  "monthly_payment": 200.0,
  "score": 0.75,
  "approved": true,
  "key_signals": {
    "amount_signal": "moderate_amount",
    "tenor_signal": "medium_term",
    "payment_signal": "excellent_history",
    "utilization_signal": "low_utilization",
    "risk_signal": "low_risk"
  },
  "components": {
    "amount_score": 0.85,
    "tenor_score": 0.70,
    "on_time_score": 0.95,
    "utilization_score": 0.70
  }
}
```

#### CloudEvent Sample (when emit_ce=true)
```json
{
  "specversion": "1.0",
  "type": "ocn.okra.bnpl_quote.v1",
  "source": "okra",
  "id": "12345678-1234-5678-9012-123456789abc",
  "time": "2024-01-15T10:30:00Z",
  "subject": "trace-12345",
  "datacontenttype": "application/json",
  "data": {
    "quote": {
      "limit": 1200.0,
      "apr": 18.5,
      "term_months": 6,
      "monthly_payment": 200.0,
      "score": 0.75,
      "approved": true
    },
    "features": {
      "amount": 1500.0,
      "tenor": 6,
      "on_time_rate": 0.95,
      "utilization": 0.3
    },
    "key_signals": {
      "amount_signal": "moderate_amount",
      "tenor_signal": "medium_term",
      "payment_signal": "excellent_history",
      "utilization_signal": "low_utilization",
      "risk_signal": "low_risk"
    },
    "timestamp": "2024-01-15T10:30:00Z",
    "metadata": {
      "service": "okra",
      "version": "1.0.0",
      "feature": "bnpl_scoring"
    }
  }
}
```

### MCP Protocol
```bash
# Get agent status
curl -X POST http://localhost:8000/mcp/invoke \
  -H "Content-Type: application/json" \
  -d '{"verb": "getStatus", "args": {}}'

# Get credit quote
curl -X POST http://localhost:8000/mcp/invoke \
  -H "Content-Type: application/json" \
  -d '{"verb": "getCreditQuote", "args": {"amount": 5000, "currency": "USD"}}'

# Get BNPL quote
curl -X POST http://localhost:8000/mcp/invoke \
  -H "Content-Type: application/json" \
  -d '{"verb": "getBnplQuote", "args": {"amount": 1500, "tenor": 6, "on_time_rate": 0.95, "utilization": 0.3}}'
```

## Open Checkout Network

Okra is part of the [Open Checkout Network (OCN)](https://github.com/ocn-ai/ocn-common), a decentralized ecosystem for transparent, merchant-controlled checkout experiences.

### Related Projects

- **[Orca](https://github.com/ocn-ai/orca)** - The Open Checkout Agent
- **[Onyx](https://github.com/ocn-ai/onyx)** - Trust Registry Agent
- **[Oasis](https://github.com/ocn-ai/oasis)** - Treasury Management Agent
- **[Orion](https://github.com/ocn-ai/orion)** - Payout Orchestration Agent
- **[Weave](https://github.com/ocn-ai/weave)** - Receipt Storage Agent

## Development

See [CONTRIBUTING.md](CONTRIBUTING.md) for development guidelines.

## License

MIT License - see [LICENSE](LICENSE) for details.

## Status

🚧 **Phase 1 Development** - Core credit functionality and MCP integration
