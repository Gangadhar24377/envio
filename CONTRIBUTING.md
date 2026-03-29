# Contributing to Envio

Thank you for your interest in contributing to Envio! This document outlines the process for contributing to the project.

## Code of Conduct

By participating in this project, you agree to abide by our [Code of Conduct](CODE_OF_CONDUCT.md). Please be respectful and constructive.

## Getting Started

### Prerequisites

- Python 3.10 or higher
- Git
- A code editor (VS Code recommended)

### Development Setup

1. **Fork the repository** on GitHub

2. **Clone your fork:**
   ```bash
   git clone https://github.com/YOUR_USERNAME/envio.git
   cd envio
   ```

3. **Create a virtual environment:**
   ```bash
   # Using uv (recommended)
   uv venv .venv
   source .venv/bin/activate  # Linux/macOS
   .venv\Scripts\activate     # Windows

   # Or using pip
   python -m venv .venv
   source .venv/bin/activate
   ```

4. **Install dependencies:**
   ```bash
   pip install -e ".[dev]"
   ```

5. **Verify installation:**
   ```bash
   envio --version
   envio doctor
   ```

## Development Workflow

### 1. Create a Branch

```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/bug-description
```

### 2. Make Changes

Follow the coding standards:
- **Formatting**: Code is formatted with `ruff` (line length: 88)
- **Type Checking**: Use type hints, verified with `mypy`
- **Testing**: Write tests for new functionality

### 3. Run Linters and Tests

```bash
# Format code
ruff check --fix .
ruff format .

# Type check
mypy src/envio

# Run tests
pytest src/tests/
```

### 4. Commit Changes

Follow conventional commit format:

```bash
git add .
git commit -m "feat: add new feature description"
git commit -m "fix: resolve bug in package resolver"
git commit -m "docs: update README with new examples"
```

**Commit types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `test`: Adding/updating tests
- `refactor`: Code refactoring
- `chore`: Maintenance tasks

### 5. Push and Create PR

```bash
git push origin your-branch-name
```

Then open a Pull Request on GitHub.

## Project Structure

```
envio/
├── src/envio/           # Main source code
│   ├── agents/          # AI agents (NLP, dependency resolution)
│   ├── analysis/        # Code analysis (imports, versions, syntax)
│   ├── commands/        # CLI commands (resurrect)
│   ├── core/            # Core utilities (executor, profiler)
│   ├── llm/             # LLM client and parser
│   ├── resolution/     # Dependency resolution
│   ├── ui/              # Console UI
│   └── utils/           # Utilities
├── src/tests/           # Test suite
├── docs/                # Documentation
└── pyproject.toml      # Project configuration
```

## Coding Standards

### Type Hints

- Use type hints for all function signatures
- Use `| None` instead of `Optional[]` for Python 3.10+
- Use `X | Y` instead of `Union[X, Y]`

```python
# Good
def process_packages(packages: list[str], verbose: bool = False) -> dict[str, Any]:
    ...

# Avoid
def process_packages(packages: List[str], verbose: bool = False) -> Dict[str, Any]:
    ...
```

### Error Handling

- Catch specific exceptions, not `Exception`
- Provide meaningful error messages
- Add logging for silent fallbacks

```python
# Good
try:
    result = risky_operation()
except ValueError as e:
    logger.warning(f"Invalid input: {e}")
    return None

# Avoid
try:
    result = risky_operation()
except Exception:
    pass  # Silent failure
```

### Docstrings

Use Google-style docstrings:

```python
def resolve_packages(packages: list[str], manager: str) -> dict:
    """Resolve package dependencies.

    Args:
        packages: List of package specifications
        manager: Package manager to use (pip, uv, conda)

    Returns:
        Dictionary with resolved packages and status

    Raises:
        ValueError: If manager is not supported
    """
```

## Testing

### Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest src/tests/test_cli.py

# Run with coverage
pytest --cov=src/envio --cov-report=term-missing
```

### Writing Tests

- Place tests in `src/tests/`
- Follow naming: `test_<module>.py`
- Use fixtures from `conftest.py`
- Mock external dependencies (PyPI, LLM APIs)

```python
def test_package_resolution():
    """Test basic package resolution."""
    with patch("requests.get") as mock_get:
        mock_get.return_value.json.return_value = {
            "info": {"version": "1.0.0"}
        }
        result = resolve("requests")
        assert result["version"] == "1.0.0"
```

## API Keys for Development

For testing, set environment variables:

```bash
# .env file in project root (not committed)
OPENAI_API_KEY=sk-your-key-here
SERPER_API_KEY=your-serper-key
```

The `.env` file is in `.gitignore` and will not be committed.

## Submitting Changes

1. Ensure all tests pass
2. Run linters: `ruff check . && ruff format . && mypy src/envio`
3. Update documentation if needed
4. Commit with a clear message
5. Push and create a Pull Request

### PR Guidelines

- **One feature/fix per PR**: Keep changes focused
- **Describe your changes**: Explain what and why
- **Link issues**: Reference any related issues
- **Update CHANGELOG**: Add entry for user-facing changes

## Questions?

- Open an issue for bugs or feature requests
- Start a discussion for questions
- Check existing issues and PRs before creating new ones

---

Thank you for contributing to Envio!
