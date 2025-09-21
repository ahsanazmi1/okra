# Okra Credit Agent Contract

Okra is an Open Credit Agent that provides credit quotes and policy evaluation based on AP2-aligned mandates and credit profiles.

## Overview

Okra implements deterministic credit policies that evaluate credit requests and return structured quotes with approval decisions, terms, and reasoning. The agent is designed to be transparent, auditable, and consistent in its decision-making.

## API Contract

### Credit Quote Request

**Endpoint:** `POST /credit/quote`

**Request Format:**
```json
{
  "mandate": {
    "actor": {
      "id": "user_12345",
      "type": "user",
      "profile": {
        "name": "John Doe",
        "email": "john@example.com"
      }
    },
    "cart": {
      "amount": "15000.00",
      "currency": "USD",
      "items": [
        {
          "id": "item_001",
          "name": "Home Improvement Loan",
          "amount": "15000.00",
          "quantity": 1,
          "category": "Financial Services"
        }
      ],
      "geo": {
        "country": "US",
        "region": "CA",
        "city": "San Francisco"
      },
      "metadata": {}
    },
    "payment": {
      "method": "bank_transfer",
      "modality": {
        "type": "installment",
        "description": "Monthly payments"
      },
      "auth_requirements": ["bank_verification"],
      "metadata": {
        "bank_name": "Chase Bank",
        "account_type": "checking"
      }
    }
  },
  "credit_profile": {
    "credit_score": 750,
    "annual_income": 85000,
    "debt_to_income_ratio": 0.28,
    "employment_status": "employed",
    "credit_history_months": 84
  },
  "requested_amount": 15000,
  "term_months": 36,
  "purpose": "home_improvement"
}
```

**Response Format:**
```json
{
  "quote_id": "quote_user_12345_1234567890",
  "approved": true,
  "credit_limit": 15000.0,
  "apr": 8.99,
  "term_months": 36,
  "monthly_payment": 477.42,
  "reasons": [
    "Excellent credit score 750 - auto-approved",
    "Approved for $15000.00 at 8.99% APR"
  ],
  "review_required": false,
  "policy_version": "v1.0.0"
}
```

## Credit Policies

### Policy Version 1.0.0

#### Auto-Approval Criteria
- Credit score ≥ 720
- Annual income ≥ $25,000
- Debt-to-income ratio ≤ 45%
- Requested amount between $1,000 - $50,000

#### Review Required Criteria
- Credit score 650-719
- Annual income ≥ $25,000
- Debt-to-income ratio ≤ 45%

#### Decline Criteria
- Credit score < 650
- Annual income < $25,000
- Debt-to-income ratio > 45%
- Requested amount < $1,000 or > $50,000

#### APR Rate Tiers
- 720+: 8.99% (Excellent)
- 680-719: 12.99% (Good)
- 650-679: 18.99% (Fair)
- 600-649: 24.99% (Poor)
- < 600: 29.99% (Subprime)

### Credit Limit Calculation

1. **Base Limit:** Requested amount
2. **Income Adjustment:** Maximum 30% of annual income
3. **Credit Score Adjustment:**
   - 750+: No reduction
   - 700-749: 10% reduction
   - 650-699: 20% reduction
   - < 650: 30% reduction
4. **Minimum:** $1,000

### Monthly Payment Calculation

Uses standard loan payment formula:
```
Payment = Principal × (Monthly Rate × (1 + Monthly Rate)^Months) / ((1 + Monthly Rate)^Months - 1)
```

## Decision Outcomes

### Approved
- `approved: true`
- `review_required: false`
- Credit limit > 0
- APR and monthly payment calculated

### Review Required
- `approved: false`
- `review_required: true`
- Estimated terms provided
- Requires manual review for final decision

### Declined
- `approved: false`
- `review_required: false`
- Credit limit = 0
- APR and monthly payment = 0
- Reasons provided for decline

## Error Handling

### Validation Errors (422)
- Invalid amount (< $0)
- Invalid term (< 1 or > 60 months)
- Missing required fields
- Invalid credit score (< 300 or > 850)
- Invalid DTI ratio (> 1.0)

### Server Errors (500)
- Policy evaluation failures
- Internal processing errors

## CloudEvents Integration

Okra optionally emits CloudEvents for credit quotes:

**Event Type:** `ocn.okra.credit_quote.v1`

**Event Structure:**
```json
{
  "specversion": "1.0",
  "id": "evt_quote_12345",
  "source": "https://okra.ocn.ai/v1",
  "type": "ocn.okra.credit_quote.v1",
  "subject": "user_12345",
  "time": "2024-01-21T12:34:56Z",
  "datacontenttype": "application/json",
  "data": {
    "quote_id": "quote_user_12345_1234567890",
    "actor_id": "user_12345",
    "mandate": { /* AP2 mandate */ },
    "quote_result": { /* Credit quote */ },
    "policy_version": "v1.0.0",
    "timestamp": "2024-01-21T12:34:56Z"
  }
}
```

## Compliance & Audit

### Deterministic Results
- Same inputs always produce same outputs
- Quote IDs are deterministic based on input hash
- All decisions are reproducible and auditable

### Transparency
- All policy parameters are publicly available
- Decision reasons are provided for every quote
- Policy version is tracked and reported

### Data Privacy
- No PII is stored in quotes
- Only necessary identifiers are retained
- Credit profiles are not persisted

## Rate Limiting

- Default: No rate limiting
- Configurable per endpoint
- IP-based or API key-based limiting available

## Security

### Authentication
- Optional API key authentication
- Configurable via environment variables

### Input Validation
- Strict validation of all inputs
- Sanitization of user-provided data
- Protection against injection attacks

### Output Sanitization
- No sensitive data in error messages
- Consistent error response format
- Audit logging of all requests

## Monitoring & Observability

### Metrics
- Quote request rate
- Approval/decline ratios
- Policy evaluation performance
- API response times

### Logging
- Request/response logging
- Policy decision logging
- Error condition logging
- Performance metrics

### Alerting
- High error rates
- Unusual approval patterns
- Performance degradation
- Security anomalies
