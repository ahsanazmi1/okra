# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Phase 2 — Explainability scaffolding
- PR template for Phase 2 development

## [0.2.0] - 2025-01-25

### 🚀 Phase 2 Complete: BNPL Scoring & Explainability

This release completes Phase 2 development, delivering deterministic BNPL (Buy Now, Pay Later) scoring, AI-powered credit decision explanations, and production-ready infrastructure for transparent credit assessment.

#### Highlights
- **Deterministic BNPL Scoring**: Fixed vectors → fixed scores with comprehensive key signals analysis
- **AI-Powered Credit Decisions**: Azure OpenAI integration for human-readable credit reasoning
- **CloudEvents Integration**: Complete CloudEvent emission for BNPL quotes with schema validation
- **Production Infrastructure**: Robust CI/CD workflows with security scanning
- **MCP Integration**: Enhanced Model Context Protocol verbs for explainability features

#### Core Features
- **BNPL Scoring Engine**: Deterministic scoring based on amount, tenor, on-time rate, and utilization
- **Credit Quote Generation**: Complete BNPL quotes with limit, APR, term, and confidence scoring
- **Decision Audit Trails**: Complete decision audit trails with explainable reasoning
- **API Endpoints**: RESTful endpoints for BNPL quote generation and credit decisions
- **Policy Engine**: Advanced policy management for credit decisions and risk assessment

#### Quality & Infrastructure
- **Test Coverage**: Comprehensive test suite with BNPL scoring and API validation
- **Security Hardening**: Enhanced security validation and risk assessment
- **CI/CD Pipeline**: Complete GitHub Actions workflow with security scanning
- **Documentation**: Comprehensive API and contract documentation

### Added
- Deterministic BNPL scoring with fixed random state for reproducible results
- AI-powered credit decision explanations with Azure OpenAI integration
- LLM integration for human-readable reasoning
- Explainability API endpoints for BNPL quotes
- Decision audit trail with explanations
- CloudEvents integration with ocn.okra.bnpl_quote.v1 schema
- Enhanced MCP verbs for explainability features
- Comprehensive BNPL quote generation with key signals
- Advanced policy engine for credit decisions
- Production-ready CI/CD infrastructure

### Changed
- Enhanced BNPL scoring with deterministic outputs
- Improved credit decision engine with explainable reasoning
- Streamlined MCP integration for better explainability
- Optimized API performance and accuracy

### Deprecated
- None

### Removed
- None

### Fixed
- Resolved MCP manifest validation indentation errors
- Fixed mypy type checking issues
- Resolved security workflow issues
- Enhanced error handling and validation

### Security
- Enhanced security validation for BNPL scoring
- Comprehensive risk assessment and mitigation
- Secure API endpoints with proper authentication
- Robust credit decision security measures

## [Unreleased] — Phase 2

### Added
- AI-powered credit decision explanations
- LLM integration for human-readable reasoning
- Explainability API endpoints
- Decision audit trail with explanations
- Integration with Azure OpenAI for explanations

### Changed

### Deprecated

### Removed

### Fixed

### Security

## [0.1.0] - 2025-01-XX

### Added
- Initial Okra agent implementation
- MCP (Model Context Protocol) integration
- Credit quote API endpoints
- Policy engine for credit decisions
- FastAPI service with health checks
- Basic test suite

## [0.1.0] - 2025-01-XX

### Added
- Initial release
- Basic credit quote functionality
- MCP stubs for getStatus and getCreditQuote
- FastAPI application structure
- Basic test suite
