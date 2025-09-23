# Contributing to Okra

Thank you for your interest in contributing to Okra! This document provides guidelines and information for contributors.

## Code of Conduct

This project and everyone participating in it is governed by our Code of Conduct. By participating, you are expected to uphold this code.

## Getting Started

### Prerequisites

- Python 3.12+
- Git
- Basic understanding of FastAPI and credit/financial systems

### Development Setup

1. Fork the repository
2. Clone your fork:
   ```bash
   git clone https://github.com/your-username/okra.git
   cd okra
   ```

3. Create a virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

4. Install dependencies:
   ```bash
   pip install -U pip
   pip install -e .[dev]
   ```

5. Run tests to ensure everything works:
   ```bash
   pytest -q
   ```

## Making Changes

### Branch Strategy

- `main`: Production-ready code
- `phase-1-foundations`: Development branch for Phase 1 features
- Feature branches: Create from `phase-1-foundations`

### Development Workflow

1. Create a feature branch:
   ```bash
   git checkout phase-1-foundations
   git checkout -b feature/your-feature-name
   ```

2. Make your changes
3. Run tests and linting:
   ```bash
   pytest -q
   ruff check .
   black .
   ```

4. Commit your changes:
   ```bash
   git add .
   git commit -m "feat: add your feature description"
   ```

5. Push your branch:
   ```bash
   git push origin feature/your-feature-name
   ```

6. Create a Pull Request to `phase-1-foundations`

## Code Standards

### Python Style

- Follow PEP 8
- Use type hints where appropriate
- Keep functions small and focused
- Write docstrings for public functions

### Testing

- Write tests for new functionality
- Aim for high test coverage
- Use descriptive test names
- Test both success and error cases

### Commit Messages

Use conventional commits format:
- `feat:` for new features
- `fix:` for bug fixes
- `docs:` for documentation changes
- `test:` for test additions/changes
- `refactor:` for code refactoring
- `chore:` for maintenance tasks

## API Design

### MCP Protocol

When adding new MCP verbs:
1. Update `mcp/manifest.json` with new capabilities
2. Implement the verb in `mcp/server.py`
3. Add tests in `tests/`
4. Update documentation

### Credit Policies

When modifying credit policies:
1. Update `policies.py`
2. Add test cases in `tests/fixtures/`
3. Update API documentation
4. Consider backward compatibility

## Documentation

- Update README.md for significant changes
- Add docstrings to new functions
- Update CHANGELOG.md for user-facing changes
- Keep API documentation current

## Pull Request Process

1. Ensure your branch is up to date with `phase-1-foundations`
2. Run all tests and linting checks
3. Update documentation as needed
4. Provide a clear description of changes
5. Link any related issues

## Release Process

Releases are managed by maintainers. If you have suggestions for releases, please open an issue.

## Questions?

- Open an issue for questions about implementation
- Join our discussions for general questions
- Check existing issues and PRs first

Thank you for contributing to Okra! 🎉
