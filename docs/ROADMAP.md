# Envio - Development Roadmap

A phase-wise todo list for transforming Envio into a production-ready open-source project.

---

## Overview

| Phase | Focus | Duration | Status |
|-------|-------|----------|--------|
| Phase 1 | Foundation & Infrastructure | Week 1 | Completed |
| Phase 2 | Code Quality & Testing | Week 2 | Completed |
| Phase 3 | Refactoring & Architecture | Week 3 | Completed |
| Phase 4 | Quick Win Features | Week 4 | Completed |
| Phase 5 | Medium-Term Features | Weeks 5-8 | In Progress |
| Phase 6 | Long-Term Vision | Ongoing | Not Started |

---

## Phase 1: Foundation & Infrastructure

**Goal:** Set up the basic infrastructure needed for any open-source project.

**Duration:** Week 1

### Tasks

- [x] **1.1 Version Control Setup**
  - [x] Create `.gitignore` file with Python template
    - Include: `__pycache__/`, `*.pyc`, `.env`, `.venv/`, `*.egg-info/`, `dist/`, `build/`
  - [x] Rename `.env` to `.env.example` with placeholder values
  - [x] Add `LICENSE` file (choose: MIT, Apache 2.0, or GPL)

- [x] **1.2 Project Packaging**
  - [x] Create `pyproject.toml` with:
    - Project metadata (name, version, description, authors)
    - Dependencies (migrate from `requirements.txt`)
    - Optional dependencies (dev, test, docs)
    - Tool configurations
  - [x] Add CLI entry point (`envio` command)
  - [x] Test installation with `pip install -e .`

- [x] **1.3 CI/CD Setup**
  - [x] Create `.github/workflows/ci.yml`:
    - Trigger on push and PR to main
    - Run linting
    - Run tests
    - Run type checking
  - [x] Create `.github/ISSUE_TEMPLATE/` directory:
    - Bug report template
    - Feature request template
  - [x] Create `.github/PULL_REQUEST_TEMPLATE.md`

- [x] **1.4 Documentation Foundation**
  - [x] Rewrite `README.md` with:
    - Project description and motivation
    - Installation instructions
    - Quick start example
    - Basic usage
    - License badge
  - [x] Create `CONTRIBUTING.md`
  - [ ] Create `CODE_OF_CONDUCT.md`

### Deliverables
- [x] Project can be installed via `pip install -e .`
- [x] CI pipeline runs on every push
- [x] Basic documentation exists

---

## Phase 2: Code Quality & Testing

**Goal:** Establish code quality standards and test coverage.

**Duration:** Week 2

### Tasks

- [x] **2.1 Linting & Formatting Setup**
  - [x] Configure `ruff` in `pyproject.toml`
  - [x] Configure `black` in `pyproject.toml`
  - [x] Configure `isort` in `pyproject.toml`
  - [x] Create `.pre-commit-config.yaml`
  - [x] Run formatters on entire codebase
  - [x] Fix all linting errors

- [x] **2.2 Type Checking**
  - [x] Configure `mypy` in `pyproject.toml`
  - [x] Add type hints to `utils/bash_executor.py`
  - [x] Add type hints to `tools/package_lookup.py`
  - [x] Add type hints to `tools/serper_search.py`
  - [x] Add type hints to all agents
  - [x] Add type hints to `main.py`
  - [x] Achieve 0 mypy errors

- [x] **2.3 Testing Infrastructure**
  - [x] Create `tests/` directory structure:
  - [x] Create `conftest.py` with fixtures
  - [x] Add pytest configuration to `pyproject.toml`
  - [x] Install pytest, pytest-cov, pytest-mock

- [x] **2.4 Unit Tests**
  - [x] Write tests for `tools/package_lookup.py`
    - Test PyPI lookup (mocked)
    - Test Conda lookup (mocked)
    - Test error handling
  - [x] Write tests for `tools/serper_search.py`
  - [x] Write tests for `utils/bash_executor.py`
  - [x] Achieve 50%+ code coverage

- [x] **2.5 Logging Implementation**
  - [x] Create `logging_config.py` module
  - [x] Replace all `print()` with `logging` calls
  - [x] Add log levels (DEBUG, INFO, WARNING, ERROR)
  - [x] Add optional file logging
  - [x] Add `--verbose` / `--quiet` CLI flags

### Deliverables
- [x] All linting checks pass
- [x] Type checking passes with 0 errors
- [x] 50%+ test coverage
- [x] Proper logging throughout application

---

## Phase 3: Refactoring & Architecture

**Goal:** Improve code organization and maintainability.

**Duration:** Week 3

### Tasks

- [x] **3.1 Configuration Centralization**
  - [x] Create `config.py` module
  - [x] Move all environment variable access to config
  - [x] Add validation for required variables
  - [x] Add sensible defaults
  - [x] Support config file (`~/.envio/config.yaml`)

- [x] **3.2 Refactor main.py**
  - [x] Extract CLI logic to `cli.py`
    - User prompts
    - Argument parsing (add argparse)
    - Output formatting
  - [x] Extract orchestration to `orchestrator.py`
    - Agent workflow coordination
    - Error handling
  - [x] Extract script generation to `script_generator.py`
    - `create_bash_script()` function
    - Template handling
  - [x] Keep `main.py` as thin entry point

- [x] **3.3 Dependency Injection**
  - [x] Create `factories.py` module
  - [x] Create LLM factory function
  - [x] Inject LLM into agents via constructor
  - [x] Inject tools into agents via constructor
  - [x] Update tests to use mocked dependencies

- [x] **3.4 Error Handling Improvement**
  - [x] Create custom exception classes
    - `PackageNotFoundError`
    - `DependencyResolutionError`
    - `ScriptExecutionError`
    - `ConfigurationError`
  - [x] Replace broad `except Exception` with specific types
  - [x] Add proper error messages with suggestions
  - [x] Ensure graceful degradation

- [x] **3.5 Input Validation & Security**
  - [x] Add input sanitization function
  - [x] Validate file paths (prevent traversal)
  - [x] Sanitize package names
  - [x] Escape special characters in generated scripts
  - [x] Add API key validation at startup

### Deliverables
- [x] `main.py` under 50 lines
- [x] Clear separation of concerns
- [x] No hardcoded configuration
- [x] Proper error handling throughout

---

## Phase 4: Quick Win Features

**Goal:** Add high-value features with low development effort.

**Duration:** Week 4

### Tasks

- [x] **4.1 CLI Improvements**
  - [x] Add `argparse` with subcommands
    - `envio create` - Create new environment
    - `envio import` - Import from requirements.txt
    - `envio --version` - Show version
    - `envio --help` - Show help
  - [x] Add `--dry-run` flag
  - [x] Add `--output` flag for script path
  - [x] Add `--no-execute` flag

- [x] **4.2 Dry-Run Mode**
  - [x] Implement `--dry-run` functionality
  - [x] Show packages that would be installed
  - [x] Show commands that would be executed
  - [x] Show script that would be generated
  - [x] Ask for confirmation before execution

- [x] **4.3 Requirements.txt Import**
  - [x] Create `parsers/requirements_parser.py`
  - [x] Parse package names and versions
  - [x] Handle comments and blank lines
  - [x] Support version specifiers (`>=`, `==`, `~=`, etc.)
  - [x] Handle `-r` includes
  - [x] Add `envio import requirements.txt` command

- [x] **4.4 pyproject.toml Import**
  - [x] Create `parsers/pyproject_parser.py`
  - [x] Parse `[project.dependencies]`
  - [x] Parse `[project.optional-dependencies]`
  - [x] Support Poetry format `[tool.poetry.dependencies]`
  - [x] Add `envio import pyproject.toml` command

- [x] **4.5 Environment Templates**
  - [x] Create `templates/` directory
  - [x] Add templates:
    - `ml-basic.yaml` (numpy, pandas, scikit-learn)
    - `web-flask.yaml` (flask, gunicorn, jinja2)
    - `web-fastapi.yaml` (fastapi, uvicorn, pydantic)
    - `data-science.yaml` (jupyter, matplotlib, seaborn)
  - [x] Add `envio create --template ml-basic` command
  - [x] Add `envio templates list` command

### Deliverables
- [x] Full CLI with subcommands
- [x] Dry-run mode working
- [x] Can import existing requirements.txt
- [x] 4+ environment templates available

---

## Phase 5: Medium-Term Features

**Goal:** Add significant features that differentiate Envio.

**Duration:** Weeks 5-8

### Tasks

- [x] **5.1 Docker Support** (Week 5)
  - [x] Create `generators/dockerfile_generator.py`
  - [x] Generate `Dockerfile` from environment
  - [x] Support Python version selection
  - [x] Support slim/alpine base images
  - [x] Add `envio export docker` command
  - [x] Generate `docker-compose.yml` optionally
  - [x] Add `.dockerignore` generation

- [x] **5.2 Package Security Scanning** (Week 5)
  - [x] Integrate with `pip-audit` or `safety`
  - [x] Check packages before installation
  - [x] Show vulnerability details
  - [x] Add `--skip-security-check` flag
  - [x] Suggest patched versions

- [x] **5.3 Version Conflict Detection** (Week 6)
  - [x] Implement dependency tree analysis
  - [x] Detect conflicting version requirements
  - [x] Show conflict details and suggestions
  - [x] Integration with `pip-tools`

- [x] **5.4 History & Tracking** (Week 6)
  - [x] Create SQLite database for history
  - [x] Store generated environments
  - [x] Add `envio history` command
  - [x] Add `envio history show <id>` command
  - [x] Add `envio history diff <id1> <id2>` command
  - [x] Add `envio history replay <id>` command

- [x] **5.5 Cloud Environment Export** (Week 7)
  - [x] Create `exporters/` directory
  - [x] GitHub Codespaces (`devcontainer.json`)
  - [x] GitPod (`.gitpod.yml`)
  - [x] VS Code Dev Container
  - [x] Add `envio export codespaces` command
  - [x] Add `envio export gitpod` command

- [x] **5.6 Package Recommendations** (Week 7)
  - [x] Create recommendation engine
  - [x] Suggest related packages
  - [x] Suggest alternatives
  - [x] Show popularity metrics
  - [x] Add `envio recommend <package>` command

- [ ] **5.7 Async Implementation** (Week 8)
  - [ ] Implement `_arun()` for all tools
  - [ ] Use `httpx` async client
  - [ ] Parallel package lookups
  - [ ] Progress indicators
  - [ ] Performance benchmarking

- [x] **5.8 Caching Layer** (Week 8)
  - [x] Implement package lookup caching
  - [x] Cache LLM responses (same input)
  - [x] Configure cache TTL
  - [x] Add `envio cache clear` command
  - [x] Cache statistics

### Deliverables
- [x] Docker support complete
- [x] Security scanning integrated
- [x] History tracking working
- [x] Cloud export (2+ platforms)
- [x] Improved performance with caching

---

## Phase 6: Long-Term Vision

**Goal:** Major features for project growth and differentiation.

**Duration:** Ongoing (Months 3+)

### Tasks

- [ ] **6.1 Web Interface**
  - [ ] Set up FastAPI backend
  - [ ] Create REST API endpoints
  - [ ] Build React/Vue frontend
  - [ ] User authentication (optional)
  - [ ] Environment sharing via URL
  - [ ] Deploy to cloud (Vercel, Railway, etc.)

- [ ] **6.2 VS Code Extension**
  - [ ] Create VS Code extension project
  - [ ] Integrate with Envio CLI
  - [ ] Add commands to command palette
  - [ ] Status bar integration
  - [ ] Publish to VS Code Marketplace

- [ ] **6.3 Multi-Language Support**
  - [ ] Node.js (package.json)
  - [ ] Ruby (Gemfile)
  - [ ] Rust (Cargo.toml)
  - [ ] Go (go.mod)
  - [ ] Abstract language-agnostic interface

- [ ] **6.4 Plugin System**
  - [ ] Design plugin architecture
  - [ ] Plugin discovery mechanism
  - [ ] Plugin API documentation
  - [ ] Example plugins
  - [ ] Plugin registry

- [x] **6.5 Local LLM Support**
  - [x] Ollama integration
  - [x] llama.cpp support
  - [x] OpenAI-compatible local servers
  - [x] Model selection in config
  - [x] Offline mode

- [ ] **6.6 Team Features**
  - [ ] Team/organization accounts
  - [ ] Shared templates
  - [ ] Environment approval workflow
  - [ ] Audit logging
  - [ ] Access control

### Deliverables
- [ ] Web UI accessible
- [ ] VS Code extension published
- [ ] 2+ additional languages supported
- [ ] Plugin system documented

---

## Progress Tracking

### Weekly Checkpoints

| Week | Phase | Key Milestone | Status |
|------|-------|---------------|--------|
| 1 | Phase 1 | CI/CD running, project installable | Completed |
| 2 | Phase 2 | 50% test coverage, linting passes | Completed |
| 3 | Phase 3 | Refactored architecture | Completed |
| 4 | Phase 4 | CLI with dry-run and import | Completed |
| 5-6 | Phase 5a | Docker + security scanning | Completed |
| 7-8 | Phase 5b | History + cloud export | Completed |
| 9+ | Phase 6 | Long-term features | Not Started |

### Status Legend

- Not Started
- In Progress
- Completed
- Blocked
- Deferred

---

## Notes

### Dependencies Between Tasks

```
Phase 1 (Foundation)
    └── Phase 2 (Quality)
        └── Phase 3 (Refactor)
            └── Phase 4 (Features)
                └── Phase 5 (Advanced)
                    └── Phase 6 (Vision)
```

- Each phase builds on the previous
- Don't skip phases
- Complete each phase before moving on

### Time Estimates

| Task Type | Estimate |
|-----------|----------|
| Simple config file | 30 min - 1 hr |
| Module refactor | 2-4 hrs |
| New feature (small) | 4-8 hrs |
| New feature (medium) | 1-2 days |
| New feature (large) | 3-5 days |
| Full system (Web UI) | 2-4 weeks |

### Resources

- [Python Packaging Guide](https://packaging.python.org/)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [pytest Documentation](https://docs.pytest.org/)
- [ruff Documentation](https://docs.astral.sh/ruff/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)

---

*Last updated: March 29, 2026*
*Version: 1.0*
