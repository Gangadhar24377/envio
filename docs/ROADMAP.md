# Envio - Development Roadmap

A phase-wise todo list for transforming Envio into a production-ready open-source project.

---

## Overview

| Phase | Focus | Duration | Status |
|-------|-------|----------|--------|
| Phase 1 | Foundation & Infrastructure | Week 1 | Not Started |
| Phase 2 | Code Quality & Testing | Week 2 | Not Started |
| Phase 3 | Refactoring & Architecture | Week 3 | Not Started |
| Phase 4 | Quick Win Features | Week 4 | Not Started |
| Phase 5 | Medium-Term Features | Weeks 5-8 | Not Started |
| Phase 6 | Long-Term Vision | Ongoing | Not Started |

---

## Phase 1: Foundation & Infrastructure

**Goal:** Set up the basic infrastructure needed for any open-source project.

**Duration:** Week 1

### Tasks

- [ ] **1.1 Version Control Setup**
  - [ ] Create `.gitignore` file with Python template
    - Include: `__pycache__/`, `*.pyc`, `.env`, `.venv/`, `*.egg-info/`, `dist/`, `build/`
  - [ ] Rename `.env` to `.env.example` with placeholder values
  - [ ] Add `LICENSE` file (choose: MIT, Apache 2.0, or GPL)

- [ ] **1.2 Project Packaging**
  - [ ] Create `pyproject.toml` with:
    - Project metadata (name, version, description, authors)
    - Dependencies (migrate from `requirements.txt`)
    - Optional dependencies (dev, test, docs)
    - Tool configurations
  - [ ] Add CLI entry point (`envio` command)
  - [ ] Test installation with `pip install -e .`

- [ ] **1.3 CI/CD Setup**
  - [ ] Create `.github/workflows/ci.yml`:
    - Trigger on push and PR to main
    - Run linting
    - Run tests
    - Run type checking
  - [ ] Create `.github/ISSUE_TEMPLATE/` directory:
    - Bug report template
    - Feature request template
  - [ ] Create `.github/PULL_REQUEST_TEMPLATE.md`

- [ ] **1.4 Documentation Foundation**
  - [ ] Rewrite `README.md` with:
    - Project description and motivation
    - Installation instructions
    - Quick start example
    - Basic usage
    - License badge
  - [ ] Create `CONTRIBUTING.md`
  - [ ] Create `CODE_OF_CONDUCT.md`

### Deliverables
- [ ] Project can be installed via `pip install -e .`
- [ ] CI pipeline runs on every push
- [ ] Basic documentation exists

---

## Phase 2: Code Quality & Testing

**Goal:** Establish code quality standards and test coverage.

**Duration:** Week 2

### Tasks

- [ ] **2.1 Linting & Formatting Setup**
  - [ ] Configure `ruff` in `pyproject.toml`
  - [ ] Configure `black` in `pyproject.toml`
  - [ ] Configure `isort` in `pyproject.toml`
  - [ ] Create `.pre-commit-config.yaml`
  - [ ] Run formatters on entire codebase
  - [ ] Fix all linting errors

- [ ] **2.2 Type Checking**
  - [ ] Configure `mypy` in `pyproject.toml`
  - [ ] Add type hints to `utils/bash_executor.py`
  - [ ] Add type hints to `tools/package_lookup.py`
  - [ ] Add type hints to `tools/serper_search.py`
  - [ ] Add type hints to all agents
  - [ ] Add type hints to `main.py`
  - [ ] Achieve 0 mypy errors

- [ ] **2.3 Testing Infrastructure**
  - [ ] Create `tests/` directory structure:
    ```
    tests/
    ├── __init__.py
    ├── conftest.py
    ├── test_tools/
    │   ├── test_package_lookup.py
    │   └── test_serper_search.py
    ├── test_agents/
    │   ├── test_nlp_agent.py
    │   └── ...
    ├── test_utils/
    │   └── test_bash_executor.py
    └── test_integration/
        └── test_workflow.py
    ```
  - [ ] Create `conftest.py` with fixtures
  - [ ] Add pytest configuration to `pyproject.toml`
  - [ ] Install pytest, pytest-cov, pytest-mock

- [ ] **2.4 Unit Tests**
  - [ ] Write tests for `tools/package_lookup.py`
    - Test PyPI lookup (mocked)
    - Test Conda lookup (mocked)
    - Test error handling
  - [ ] Write tests for `tools/serper_search.py`
  - [ ] Write tests for `utils/bash_executor.py`
  - [ ] Achieve 50%+ code coverage

- [ ] **2.5 Logging Implementation**
  - [ ] Create `logging_config.py` module
  - [ ] Replace all `print()` with `logging` calls
  - [ ] Add log levels (DEBUG, INFO, WARNING, ERROR)
  - [ ] Add optional file logging
  - [ ] Add `--verbose` / `--quiet` CLI flags

### Deliverables
- [ ] All linting checks pass
- [ ] Type checking passes with 0 errors
- [ ] 50%+ test coverage
- [ ] Proper logging throughout application

---

## Phase 3: Refactoring & Architecture

**Goal:** Improve code organization and maintainability.

**Duration:** Week 3

### Tasks

- [ ] **3.1 Configuration Centralization**
  - [ ] Create `config.py` module
  - [ ] Move all environment variable access to config
  - [ ] Add validation for required variables
  - [ ] Add sensible defaults
  - [ ] Support config file (`~/.envio/config.yaml`)

- [ ] **3.2 Refactor main.py**
  - [ ] Extract CLI logic to `cli.py`
    - User prompts
    - Argument parsing (add argparse)
    - Output formatting
  - [ ] Extract orchestration to `orchestrator.py`
    - Agent workflow coordination
    - Error handling
  - [ ] Extract script generation to `script_generator.py`
    - `create_bash_script()` function
    - Template handling
  - [ ] Keep `main.py` as thin entry point

- [ ] **3.3 Dependency Injection**
  - [ ] Create `factories.py` module
  - [ ] Create LLM factory function
  - [ ] Inject LLM into agents via constructor
  - [ ] Inject tools into agents via constructor
  - [ ] Update tests to use mocked dependencies

- [ ] **3.4 Error Handling Improvement**
  - [ ] Create custom exception classes
    - `PackageNotFoundError`
    - `DependencyResolutionError`
    - `ScriptExecutionError`
    - `ConfigurationError`
  - [ ] Replace broad `except Exception` with specific types
  - [ ] Add proper error messages with suggestions
  - [ ] Ensure graceful degradation

- [ ] **3.5 Input Validation & Security**
  - [ ] Add input sanitization function
  - [ ] Validate file paths (prevent traversal)
  - [ ] Sanitize package names
  - [ ] Escape special characters in generated scripts
  - [ ] Add API key validation at startup

### Deliverables
- [ ] `main.py` under 50 lines
- [ ] Clear separation of concerns
- [ ] No hardcoded configuration
- [ ] Proper error handling throughout

---

## Phase 4: Quick Win Features

**Goal:** Add high-value features with low development effort.

**Duration:** Week 4

### Tasks

- [ ] **4.1 CLI Improvements**
  - [ ] Add `argparse` with subcommands
    - `envio create` - Create new environment
    - `envio import` - Import from requirements.txt
    - `envio --version` - Show version
    - `envio --help` - Show help
  - [ ] Add `--dry-run` flag
  - [ ] Add `--output` flag for script path
  - [ ] Add `--no-execute` flag

- [ ] **4.2 Dry-Run Mode**
  - [ ] Implement `--dry-run` functionality
  - [ ] Show packages that would be installed
  - [ ] Show commands that would be executed
  - [ ] Show script that would be generated
  - [ ] Ask for confirmation before execution

- [ ] **4.3 Requirements.txt Import**
  - [ ] Create `parsers/requirements_parser.py`
  - [ ] Parse package names and versions
  - [ ] Handle comments and blank lines
  - [ ] Support version specifiers (`>=`, `==`, `~=`, etc.)
  - [ ] Handle `-r` includes
  - [ ] Add `envio import requirements.txt` command

- [ ] **4.4 pyproject.toml Import**
  - [ ] Create `parsers/pyproject_parser.py`
  - [ ] Parse `[project.dependencies]`
  - [ ] Parse `[project.optional-dependencies]`
  - [ ] Support Poetry format `[tool.poetry.dependencies]`
  - [ ] Add `envio import pyproject.toml` command

- [ ] **4.5 Environment Templates**
  - [ ] Create `templates/` directory
  - [ ] Add templates:
    - `ml-basic.yaml` (numpy, pandas, scikit-learn)
    - `web-flask.yaml` (flask, gunicorn, jinja2)
    - `web-fastapi.yaml` (fastapi, uvicorn, pydantic)
    - `data-science.yaml` (jupyter, matplotlib, seaborn)
  - [ ] Add `envio create --template ml-basic` command
  - [ ] Add `envio templates list` command

### Deliverables
- [ ] Full CLI with subcommands
- [ ] Dry-run mode working
- [ ] Can import existing requirements.txt
- [ ] 4+ environment templates available

---

## Phase 5: Medium-Term Features

**Goal:** Add significant features that differentiate Envio.

**Duration:** Weeks 5-8

### Tasks

- [ ] **5.1 Docker Support** (Week 5)
  - [ ] Create `generators/dockerfile_generator.py`
  - [ ] Generate `Dockerfile` from environment
  - [ ] Support Python version selection
  - [ ] Support slim/alpine base images
  - [ ] Add `envio export docker` command
  - [ ] Generate `docker-compose.yml` optionally
  - [ ] Add `.dockerignore` generation

- [ ] **5.2 Package Security Scanning** (Week 5)
  - [ ] Integrate with `pip-audit` or `safety`
  - [ ] Check packages before installation
  - [ ] Show vulnerability details
  - [ ] Add `--skip-security-check` flag
  - [ ] Suggest patched versions

- [ ] **5.3 Version Conflict Detection** (Week 6)
  - [ ] Implement dependency tree analysis
  - [ ] Detect conflicting version requirements
  - [ ] Show conflict details and suggestions
  - [ ] Integration with `pip-tools`

- [ ] **5.4 History & Tracking** (Week 6)
  - [ ] Create SQLite database for history
  - [ ] Store generated environments
  - [ ] Add `envio history` command
  - [ ] Add `envio history show <id>` command
  - [ ] Add `envio history diff <id1> <id2>` command
  - [ ] Add `envio history replay <id>` command

- [ ] **5.5 Cloud Environment Export** (Week 7)
  - [ ] Create `exporters/` directory
  - [ ] GitHub Codespaces (`devcontainer.json`)
  - [ ] GitPod (`.gitpod.yml`)
  - [ ] VS Code Dev Container
  - [ ] Add `envio export codespaces` command
  - [ ] Add `envio export gitpod` command

- [ ] **5.6 Package Recommendations** (Week 7)
  - [ ] Create recommendation engine
  - [ ] Suggest related packages
  - [ ] Suggest alternatives
  - [ ] Show popularity metrics
  - [ ] Add `envio recommend <package>` command

- [ ] **5.7 Async Implementation** (Week 8)
  - [ ] Implement `_arun()` for all tools
  - [ ] Use `httpx` async client
  - [ ] Parallel package lookups
  - [ ] Progress indicators
  - [ ] Performance benchmarking

- [ ] **5.8 Caching Layer** (Week 8)
  - [ ] Implement package lookup caching
  - [ ] Cache LLM responses (same input)
  - [ ] Configure cache TTL
  - [ ] Add `envio cache clear` command
  - [ ] Cache statistics

### Deliverables
- [ ] Docker support complete
- [ ] Security scanning integrated
- [ ] History tracking working
- [ ] Cloud export (2+ platforms)
- [ ] Improved performance with caching

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

- [ ] **6.5 Local LLM Support**
  - [ ] Ollama integration
  - [ ] llama.cpp support
  - [ ] OpenAI-compatible local servers
  - [ ] Model selection in config
  - [ ] Offline mode

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
| 1 | Phase 1 | CI/CD running, project installable | Not Started |
| 2 | Phase 2 | 50% test coverage, linting passes | Not Started |
| 3 | Phase 3 | Refactored architecture | Not Started |
| 4 | Phase 4 | CLI with dry-run and import | Not Started |
| 5-6 | Phase 5a | Docker + security scanning | Not Started |
| 7-8 | Phase 5b | History + cloud export | Not Started |
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

*Last updated: February 4, 2026*
*Version: 1.0*
