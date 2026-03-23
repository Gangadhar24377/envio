# Envio - Improvements & Feature Ideas

This document outlines all the improvements needed and potential features for making Envio a robust open-source project.

---

## Table of Contents

1. [Critical Infrastructure Gaps](#critical-infrastructure-gaps)
2. [Code Quality Improvements](#code-quality-improvements)
3. [Architecture Improvements](#architecture-improvements)
4. [Security Improvements](#security-improvements)
5. [New Features - Short Term](#new-features---short-term)
6. [New Features - Medium Term](#new-features---medium-term)
7. [New Features - Long Term](#new-features---long-term)
8. [Documentation Improvements](#documentation-improvements)
9. [Dependency Cleanup](#dependency-cleanup)

---

## Critical Infrastructure Gaps

These are **must-have** items before the project can be considered open-source ready.

### 1. Version Control Hygiene

| Item | Current State | Required Action |
|------|---------------|-----------------|
| `.gitignore` | Missing | Add Python template + `.env`, `__pycache__/`, `*.pyc`, `.venv/`, etc. |
| `LICENSE` | Missing | Add open-source license (MIT, Apache 2.0, GPL, etc.) |
| `.env` handling | File exists in repo | Move to `.env.example` with placeholder values |

### 2. Project Packaging

| Item | Current State | Required Action |
|------|---------------|-----------------|
| `pyproject.toml` | Missing | Create with project metadata, dependencies, tool configs |
| `setup.py` / `setup.cfg` | Missing | Optional if using `pyproject.toml` (PEP 517/518) |
| Entry point | Only `main.py` | Add CLI entry point (`envio` command) |

### 3. Continuous Integration

| Item | Current State | Required Action |
|------|---------------|-----------------|
| GitHub Actions | None | Add workflows for linting, testing, type-checking |
| Pre-commit hooks | None | Add `.pre-commit-config.yaml` |
| Branch protection | Unknown | Enable on main/master branch |

### 4. Testing

| Item | Current State | Required Action |
|------|---------------|-----------------|
| Test framework | pytest installed but unused | Create `tests/` directory structure |
| Unit tests | None (0 test files) | Add tests for all modules |
| Integration tests | None | Add end-to-end workflow tests |
| Coverage | 0% | Aim for 70%+ coverage |
| Mocking | Not implemented | Mock external APIs (OpenAI, PyPI, Conda, Serper) |

---

## Code Quality Improvements

### 1. Linting & Formatting

| Tool | Purpose | Configuration File |
|------|---------|-------------------|
| **ruff** | Fast Python linter | `pyproject.toml` or `ruff.toml` |
| **black** | Code formatter | `pyproject.toml` |
| **isort** | Import sorting | `pyproject.toml` |
| **mypy** | Static type checking | `pyproject.toml` or `mypy.ini` |

### 2. Type Annotations

| File | Current State | Required Action |
|------|---------------|-----------------|
| `main.py` | No type hints | Add complete type annotations |
| `agents/*.py` | No type hints | Add type hints for all methods |
| `tools/*.py` | Partial coverage | Complete remaining annotations |
| `utils/*.py` | No type hints | Add type annotations |

### 3. Logging

| Current State | Required Action |
|---------------|-----------------|
| Only `print()` statements | Replace with Python `logging` module |
| No log levels | Implement DEBUG, INFO, WARNING, ERROR levels |
| No log files | Add optional file logging |
| No structured logging | Consider JSON logging for production |

### 4. Error Handling

| Issue | Location | Required Action |
|-------|----------|-----------------|
| Broad `except Exception` | `main.py:139` | Use specific exception types |
| Missing error handling | `serper_search.py` | Add try/except for HTTP requests |
| No API key validation | All agents | Validate keys before use |
| Silent failures | Various | Log and handle appropriately |

### 5. Docstrings

| File | Current State | Required Action |
|------|---------------|-----------------|
| `main.py` | No docstrings | Add module, function, class docstrings |
| `agents/*.py` | No docstrings | Document all agents and methods |
| `tools/*.py` | 2 docstrings only | Complete documentation |
| `utils/*.py` | No docstrings | Add documentation |

---

## Architecture Improvements

### 1. Refactor `main.py`

The main file is currently 251 lines handling multiple responsibilities:

| Extract To | Responsibility |
|------------|----------------|
| `cli.py` | User input/output handling |
| `orchestrator.py` | Agent workflow coordination |
| `script_generator.py` | Bash script creation logic |
| `executor.py` | Script execution and tmux management |
| `config.py` | Centralized configuration |

### 2. Dependency Injection

| Current State | Improvement |
|---------------|-------------|
| LLM hardcoded in each agent | Create factory/config for LLM instances |
| Tools instantiated inside agents | Inject tools via constructor |
| API keys accessed directly | Centralized configuration object |

### 3. Configuration Management

| Current State | Improvement |
|---------------|-------------|
| Scattered `os.getenv()` calls | Single config class/module |
| No validation | Validate required env vars at startup |
| No defaults | Provide sensible defaults |
| Single environment | Support dev/staging/prod configs |

### 4. Async Support

| Current State | Improvement |
|---------------|-------------|
| `_arun()` raises `NotImplementedError` | Implement async tool methods |
| Sequential pipeline | Allow parallel agent execution where possible |
| Blocking HTTP calls | Use `httpx` async client |

### 5. Caching Layer

| What to Cache | Benefit |
|---------------|---------|
| Package lookups (PyPI/Conda) | Faster repeated queries |
| LLM responses (with same input) | Reduced API costs |
| Dependency resolution results | Faster re-runs |

---

## Security Improvements

### Critical

| Issue | Risk Level | Fix |
|-------|------------|-----|
| `.env` in repository | HIGH | Add to `.gitignore`, create `.env.example` |
| No input sanitization | HIGH | Validate/sanitize all user inputs |
| Arbitrary path execution | HIGH | Validate paths, prevent traversal |
| Unsanitized script generation | MEDIUM | Escape special characters in generated scripts |

### Recommended

| Improvement | Benefit |
|-------------|---------|
| API key validation at startup | Fail fast with clear error messages |
| Rate limiting on API calls | Prevent abuse/overspending |
| Audit logging | Track all operations |
| Secrets management | Support secret managers (not just `.env`) |
| HTTPS certificate validation | Explicit validation for API calls |

---

## New Features - Short Term

*Quick wins that add significant value with low effort*

### 1. Dry-Run Mode
- Preview generated commands without execution
- Show what would be created/installed
- Allow user confirmation before proceeding

### 2. Requirements.txt Import
- Parse existing `requirements.txt` files
- Generate environment from existing projects
- Support version specifiers (`>=`, `==`, `~=`)

### 3. pyproject.toml Support
- Parse `pyproject.toml` dependencies
- Support both `[project.dependencies]` and poetry format
- Extract optional dependencies

### 4. Interactive Mode
- Step-by-step confirmation
- Allow skipping/modifying individual packages
- Show progress indicators

### 5. Verbose/Quiet Modes
- `-v` / `--verbose` for detailed output
- `-q` / `--quiet` for minimal output
- Configurable log levels via CLI

### 6. Config File Support
- `~/.envio/config.yaml` for user preferences
- Default environment type (pip/conda)
- Default Python version
- Preferred package sources

### 7. Export to File Only
- Generate script without executing
- Output to stdout for piping
- Custom output file path

---

## New Features - Medium Term

*Significant features requiring moderate development effort*

### 1. Docker Support
- Generate `Dockerfile` from environment
- Create `docker-compose.yml`
- Support multi-stage builds
- Base image selection

### 2. Multi-Language Support
- **Node.js**: npm/yarn/pnpm package.json generation
- **Ruby**: Gemfile generation
- **Rust**: Cargo.toml generation
- **Go**: go.mod generation

### 3. Environment Templates
- Pre-built configurations:
  - Machine Learning (numpy, pandas, scikit-learn, tensorflow/pytorch)
  - Web Development (flask/django, gunicorn, celery)
  - Data Science (jupyter, matplotlib, seaborn)
  - API Development (fastapi, pydantic, uvicorn)
- Custom template creation and sharing

### 4. Version Conflict Detection
- Analyze dependency compatibility
- Warn about known conflicts
- Suggest compatible version combinations
- Integration with pip-tools or pip-compile

### 5. Package Recommendations
- Suggest related packages
- Recommend alternatives (e.g., requests vs httpx)
- Security-focused suggestions (e.g., suggest `python-dotenv` for env management)

### 6. History & Rollback
- Track all generated environments
- Store in local SQLite database
- Rollback to previous configurations
- Diff between environments

### 7. Cloud Environment Export
- GitHub Codespaces (`devcontainer.json`)
- GitPod (`.gitpod.yml`)
- Replit (`replit.nix`)
- VS Code Dev Containers

### 8. Package Security Scanning
- Check for known vulnerabilities (CVE database)
- Integration with `safety` or `pip-audit`
- Block/warn on vulnerable packages
- Suggest patched versions

---

## New Features - Long Term

*Major features for differentiation and growth*

### 1. Web Interface
- Browser-based UI (FastAPI + React/Vue)
- Visual environment builder
- Drag-and-drop package selection
- Share environments via URL

### 2. VS Code Extension
- Integrated into editor
- Right-click to add packages
- Environment status in status bar
- Quick actions for common tasks

### 3. Team Collaboration
- Shared environment configurations
- Team templates
- Version control integration
- Comments/annotations on configs

### 4. API Service
- REST API for programmatic access
- Webhook integrations
- GitHub App for auto-environment setup
- Slack/Discord bot integration

### 5. Plugin System
- Extensible architecture
- Custom agent plugins
- Custom tool plugins
- Community plugin marketplace

### 6. Cost Estimation
- Estimate cloud compute costs
- Compare environment sizes
- Optimize for cost/performance
- Integration with cloud pricing APIs

### 7. AI Improvements
- Fine-tuned models for package management
- Local LLM support (Ollama, llama.cpp)
- Reduced API dependency
- Offline mode with local models

---

## Documentation Improvements

### README.md Overhaul

Current: 5 lines
Required:

- [ ] Project logo/banner
- [ ] Badges (build status, coverage, license, Python version)
- [ ] Clear project description
- [ ] Features list
- [ ] Quick start guide
- [ ] Installation instructions (pip, from source)
- [ ] Usage examples with GIFs/screenshots
- [ ] Configuration options
- [ ] Architecture overview
- [ ] Contributing section
- [ ] License information
- [ ] Acknowledgments

### Additional Documentation

| Document | Purpose |
|----------|---------|
| `CONTRIBUTING.md` | How to contribute, code style, PR process |
| `CODE_OF_CONDUCT.md` | Community guidelines |
| `CHANGELOG.md` | Version history and changes |
| `SECURITY.md` | Security policy, vulnerability reporting |
| `docs/` directory | Detailed documentation (architecture, API, tutorials) |

### Code Documentation

- Complete docstrings (Google or NumPy style)
- Inline comments for complex logic
- Type hints for all functions
- Example usage in docstrings

---

## Dependency Cleanup

### Currently Unused (Consider Removing)

| Package | Installed Version | Notes |
|---------|------------------|-------|
| tensorflow | 2.17.0 | Heavy, not used in current code |
| chromadb | 0.4.24 | Vector DB, not implemented |
| lancedb | 0.5.7 | Vector DB, not implemented |
| qdrant-client | 1.11.2 | Vector DB, not implemented |
| neo4j | 5.24.0 | Graph DB, not implemented |
| selenium | 4.25.0 | Browser automation, not used |
| auth0-python | 4.7.2 | Auth, not implemented |
| bcrypt | 4.2.0 | Auth, not implemented |
| alembic | 1.13.3 | DB migrations, no DB |

### Keep for Future

| Package | Reason |
|---------|--------|
| fastapi | Planned web UI |
| uvicorn | ASGI server for FastAPI |
| sqlalchemy | Future history/tracking feature |

### Recommended Final Count

- **Production dependencies**: ~30-40 packages
- **Development dependencies**: ~15-20 packages (pytest, mypy, ruff, black, etc.)

---

## Priority Matrix

| Priority | Category | Impact | Effort |
|----------|----------|--------|--------|
| P0 | `.gitignore`, `LICENSE` | High | Low |
| P0 | Testing setup | High | Medium |
| P0 | CI/CD | High | Medium |
| P1 | README overhaul | High | Low |
| P1 | Linting setup | Medium | Low |
| P1 | Logging implementation | Medium | Medium |
| P2 | Refactor `main.py` | Medium | Medium |
| P2 | Type annotations | Medium | Medium |
| P2 | Dry-run mode | Medium | Low |
| P3 | Docker support | Medium | High |
| P3 | Web interface | High | High |

---

*Last updated: February 4, 2026*
