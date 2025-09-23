# Okra — The Open Credit Agent

[![CI](https://github.com/ahsanazmi1/okra/actions/workflows/ci.yml/badge.svg)](https://github.com/ahsanazmi1/okra/actions/workflows/ci.yml)
[![Contracts Validation](https://github.com/ahsanazmi1/okra/actions/workflows/contracts.yml/badge.svg)](https://github.com/ahsanazmi1/okra/actions/workflows/contracts.yml)
[![Security Validation](https://github.com/ahsanazmi1/okra/actions/workflows/security.yml/badge.svg)](https://github.com/ahsanazmi1/okra/actions/workflows/security.yml)

**Okra** is the **open, transparent credit agent** for the [Open Checkout Network (OCN)](https://github.com/ocn-ai/ocn-common).

## Purpose

Okra provides intelligent credit decisions and quotes for the OCN ecosystem. Unlike traditional black-box credit systems, Okra offers:

- **Transparent Credit Policies** - Clear, auditable credit decision logic
- **Explainable AI** - Human-readable explanations for credit decisions
- **Open Architecture** - Integrates seamlessly with OCN protocols
- **MCP Integration** - Model Context Protocol support for agent interactions

## Quick Start

```bash
# Clone and setup
git clone https://github.com/ahsanazmi1/okra.git
cd okra

# Create virtual environment
python -m venv .venv && source .venv/bin/activate

# Install dependencies
pip install -U pip && pip install -e .[dev]

# Run tests
pytest -q

# Start the service
uvicorn okra.api:app --reload
```

## API Endpoints

### Health Check
```bash
curl http://localhost:8000/health
```

### Credit Quote
```bash
curl -X POST http://localhost:8000/quote \
  -H "Content-Type: application/json" \
  -d '{
    "amount": 10000,
    "currency": "USD",
    "term_months": 12,
    "applicant_info": {
      "credit_score": 750,
      "income": 50000
    }
  }'
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
