# Envio - Progress & Changelog

## Project Overview

**Envio** is an AI-Native Environment Orchestrator that combines the speed of `uv` with AI-powered dependency resolution. When standard resolution fails, Envio analyzes errors and automatically fixes conflicts.

---

## Architecture (Latest)

### Multi-Provider LLM Support via LiteLLM

Envio uses LiteLLM to support any LLM provider:
- OpenAI (GPT-4, GPT-4o, GPT-4o-mini)
- Anthropic (Claude)
- Google (Gemini)
- Azure OpenAI
- Local models (Ollama, llama.cpp)
- And 100+ other providers

### Configuration

Users can configure their preferred LLM in `.env`:
```bash
ENVIO_LLM_MODEL=gpt-4o-mini           # or claude-3-5-sonnet, ollama/llama3, etc.
ENVIO_LLM_API_KEY=sk-...              # or leave blank for local models
ENVIO_LLM_API_BASE=http://localhost:11434/v1  # optional for Ollama
```

### Recent Improvements (Phase 2-3)

#### Phase 3.5: Performance Optimization (Mar 27, 2026)
- **Parallel Processing**: import_analyzer.py and syntax_detector.py now use ThreadPoolExecutor
- **Dynamic Skip Indicators**: Automatically skips cache/venv directories without hardcoding
- **Rate-Limited PyPI Queries**: version_inference.py uses semaphore for controlled concurrency
- **TUI Progress**: tqdm progress bars for file scanning operations
- **Dynamic Stdlib Detection**: Uses `sys.stdlib_module_names` instead of hardcoded lists
- **Multi-Location .env Loading**: Checks cwd → project dir → ~/.envio/ for API keys
- **Package Validation**: Auto-validates packages against PyPI before installation
- **Dynamic Package Fixing**: Maps deprecated import names (PIL→Pillow) and fixes invalid versions
- **Self-Healing Integration**: All commands now trigger healing when resolution fails
- **Rich Progress Bars**: Replaced tqdm with Rich Progress for better UI integration
- **Dynamic Package Search**: AI-powered package suggestions with web search fallback
- **Tree Display**: Shows package dependencies in tree format before installation

#### CLI Fixes
- Fixed syntax errors in cli.py (missing try/except blocks from merge conflicts)
- Fixed virtualenv_manager.py syntax errors
- Added proper error handling for all 11 commands

#### Shell Injection Protection
- Removed `shell=True` from subprocess calls
- Added `shlex.quote()` for all user inputs in shell scripts
- Used list-based subprocess.run() for safer execution

#### Semantic Version Comparison
- Uses `packaging.version.Version` instead of string comparison
- Fixes incorrect results like `"1.9" > "1.82.6"`

#### Phase 4: Config System & Bug Fixes (Mar 29, 2026)

##### Configuration System
- **First-Run Setup**: Interactive setup asks for default env directory and package manager
- **`envio config` Command**: View and edit configuration (`envio config show`, `envio config set`)
- **Config File**: Stores settings in `~/.envio/config.json`
- **Smart Path Detection**: Uses XDG base directories on Linux, Documents on Windows

##### Python Version Detection
- **AI-Powered Inference**: Uses LiteLLM to determine minimum Python version from code patterns
- **Pattern Caching**: Caches pattern→version mappings in `~/.envio/cache/pattern_versions.json`
- **System Python**: Uses user's actual Python version instead of hardcoded values
- **Static Mappings**: Built-in mappings for common patterns (f_string→3.6, walrus_operator→3.8, etc.)

##### Bug Fixes
- **Inline Comments**: requirements.txt parser now handles `# comments` correctly
- **Hardcoded Paths**: Replaced 9 hardcoded `~/Documents/envs` with config-based paths
- **Temp Directory**: resurrect now saves requirements.txt to user path (not temp)
- **API Key Check**: doctor now checks both ENVIO_LLM_API_KEY and OPENAI_API_KEY
- **Dead Code**: Removed unused `_search_pypi_for_import` and `bash_executor`
- **Smart Retry**: Doesn't retry on auth errors (401, 403) - saves tokens/time
- **Package Manager Detection**: lock command now detects actual package manager from environment
- **Serper Results**: Returns top 5 results instead of just 1
- **Timeouts**: Added 10s timeouts to all HTTP requests
- **Export Sanitization**: Validates package names before embedding in Dockerfile/devcontainer
- **Network Errors**: Shows warnings when PyPI is unreachable
- **PowerShell Transcript**: Handles Start-Transcript failures gracefully
- **ScriptGenerator Caching**: Caches generator instance for performance
- **Input Validation**: Validates environment names (no path traversal, reserved names)

#### Self-Healing Improvements
- Error deduplication using hash-based detection
- Three fallback strategies: relax constraints → find alternatives → skip optionals
- Re-validation of fixes with FastResolver

#### Import-to-Package Mapping
- Dynamic PyPI lookup for imports (cv2 → opencv-python)
- Local caching for performance
- No hardcoded mappings

#### VirtualEnvManager CLI
- `envio list` - List all virtual environments
- `envio activate` - Show activation command
- `envio remove` - Uninstall packages from environment

#### Tenacity Retry Logic
- LLM calls retry up to 3 times with exponential backoff
- Graceful degradation when API key not set

#### Singleton SystemProfiler
- Caches GPU detection results
- Prevents repeated nvidia-smi calls

#### Test Coverage
- 78 tests passing
- Coverage for analysis, core, resolution, LLM, and CLI modules

---

## Roadmap Phases

### Phase 1: The Open-Source MVP (V1 Launch) - COMPLETE

- [x] **1.1 Core Infrastructure & Cleanup (P0)**
- [x] **1.2 OS-Agnostic Execution Engine (P0)**
- [x] **1.3 The Hybrid "Self-Healing" Resolver (P1)**
- [x] **1.4 Hardware-Aware ML Setup (P1)**
- [x] **1.5 Rich Terminal UI (P1)**
- [x] **1.6 CrewAI → LiteLLM Migration**

### Phase 2: Environment Management - COMPLETE

- [x] **2.1 Environment Registry** - Track all envio-created environments
- [x] **2.2 Package Import Mapping** - Dynamic cv2→opencv-python resolution
- [x] **2.3 VirtualEnvManager CLI** - envio list, remove, activate commands
- [x] **2.4 Shell Injection Protection** - sanitize.py, shlex.quote
- [x] **2.5 Singleton SystemProfiler** - Cache hardware detection
- [x] **2.6 Tenacity Retry Logic** - Resilient LLM calls

### Phase 3: Deployment & Security - COMPLETE

- [x] **3.1 Interactive Confirmation** - `--yes/-y` flag, "Proceed? [Y/n]"
- [x] **3.2 Dry-Run Mode** - `--dry-run` flag for preview
- [x] **3.3 Lockfile Generation** - `envio lock` for reproducibility
- [x] **3.4 Multi-Format Export** - `envio export` (requirements/Dockerfile/devcontainer)
- [x] **3.5 Security Audit** - `envio audit` with pip-audit integration

### Phase 4: Future Features (Growth)

- [x] 4.1 Ghost-Town Repo Resurrection
- [x] 4.2 Ollama/Local LLM Support
- [x] 4.3 Apple Silicon/MPS Detection
- [ ] 4.4 GitHub Action
- [ ] 4.5 Semantic Environment Diffing
### Phase 2: Code Quality & Stability - COMPLETE

- [x] **2.1 Shell Injection Protection**
- [x] **2.2 Semantic Version Comparison**
- [x] **2.3 Import-to-Package Mapping**
- [x] **2.4 VirtualEnvManager CLI Commands**
- [x] **2.5 Tenacity Retry Logic**
- [x] **2.6 Test Coverage (78 tests)**

### Phase 3: The "Reproducibility" Engine (Growth)

- [ ] 3.1 Ghost-Town Repo Resurrection
- [ ] 3.2 Jailbroken Local LLM Execution
- [ ] 3.3 AI-Optimized Containerization
- [ ] 3.4 Semantic Environment Diffing

### Phase 4: Team & Enterprise Workflows (Maturity)

- [ ] 4.1 The Envio GitHub Action
- [ ] 4.2 Security & CVE Profiling
- [ ] 4.3 Dependency Cost Estimation

---

## Completed Changes

### Phase 1.6 - CrewAI → LiteLLM Migration (COMPLETED: Mar 19, 2026)

#### Why Migration?
- CrewAI brought 177 packages, using <5% of its features
- Only `Agent.run()`, `Task`, and `BaseTool` were used
- No crew orchestration, delegation, or memory features
- Windows encoding issues with CrewAI internal emojis

#### New Architecture
```
src/envio/
├── llm/                        # NEW - Multi-provider LLM layer
│   ├── __init__.py
│   ├── client.py              # LiteLLM wrapper
│   ├── prompts.py             # All system/user prompts
│   └── parser.py              # JSON response parser
├── agents/                     # Rewritten - plain classes
│   ├── nlp_agent.py           # NLPProcessor (was NLPAgent)
│   ├── dependency_resolution_agent.py  # DependencyResolver
│   └── command_construction_agent.py   # CommandGenerator
├── tools/                      # Rewritten - plain classes
│   ├── package_lookup.py      # PackageLookupTool
│   └── serper_search.py       # SerperSearchTool
```

#### Before vs After
| Metric | Before | After |
|--------|--------|-------|
| Total packages | 177 | 59 |
| Dependencies | crewai, crewai-tools, langchain, langchain-openai, langchain-core, openai | litellm only |
| Windows encoding | Broken (emojis) | Fixed (ASCII) |
| Multi-provider | No | Yes (100+ providers) |
| Local LLM | No | Yes (Ollama, etc.) |

#### New Components
| Component | Purpose |
|-----------|---------|
| `LLMClient` | LiteLLM wrapper with configurable provider |
| `LLMConfig` | Dataclass for provider configuration |
| `LLMResponse` | Response object with content, model, usage |
| `ResponseParser` | JSON extraction and validation |
| `NLPProcessor` | Parse user input → package list |
| `DependencyResolver` | Hybrid uv + AI resolution |
| `CommandGenerator` | Generate install commands |

#### Removed Components
| Component | Reason |
|-----------|--------|
| `BashFileGeneratorAgent` | Unused - replaced by ScriptGeneratorFactory |
| CrewAI Agent base class | Replaced with plain classes |
| CrewAI Task class | Not needed |
| CrewAI BaseTool | Replaced with plain classes |
| `langchain` | Not needed |
| `langchain-openai` | Replaced by LiteLLM |
| `prompt_toolkit` | Replaced with simple `input()` |

---

### Phase 3 - Deployment & Security (COMPLETED: Mar 26, 2026)

#### New Commands
| Command | Purpose |
|---------|---------|
| `envio lock` | Generate reproducible lockfiles (JSON/text) |
| `envio export` | Export to requirements.txt, Dockerfile, devcontainer.json |
| `envio audit` | Scan for security vulnerabilities with pip-audit |

#### New Options
| Option | Purpose |
|--------|---------|
| `--dry-run` | Preview generated script without executing |
| `--yes, -y` | Skip confirmation prompt |

#### Implementation Details
- **Lockfile Generation**: Captures exact package versions with hardware context
- **Export Formats**: Dockerfile uses multi-stage builds; devcontainer.json includes VS Code extensions
- **Security Audit**: Integrates pip-audit for CVE scanning with auto-fix capability
- **Dry-Run Mode**: Writes script to disk but skips execution for review
- **Interactive Confirmation**: Prompts "Proceed? [Y/n]" before making changes

---

## How to Use Envio

### Interactive Mode
```bash
uv run envio interactive
```

### Direct Install
```bash
uv run envio install requests flask numpy
uv run envio install torch torchvision --env-type uv
```

### Environment Management
```bash
# List all virtual environments
uv run envio list

# Show activation command for an environment
uv run envio activate --env my-env

# Remove packages from an environment
uv run envio remove numpy pandas --env my-env
```

### Programmatic Usage
```python
from envio.core import SystemProfiler
from envio.llm import LLMClient
from envio.resolution import FastResolver
from envio.ui import ConsoleUI
from envio.analysis import ImportAnalyzer, find_package_for_import

# System profiling (singleton)
profile = SystemProfiler().profile()
print(f"GPU: {profile.gpu.name}")

# Fast resolution
resolver = FastResolver()
result = resolver.resolve(["requests", "flask"])

# LLM client (with retry)
llm = LLMClient()
response = llm.chat(user_prompt="What is Python?")
print(response.content)

# Rich console
console = ConsoleUI()
console.print_success("Setup complete!")

# Import analysis
analyzer = ImportAnalyzer()
imports = analyzer.scan_directory("/path/to/project")

# Package mapping
package = find_package_for_import("cv2")  # Returns "opencv-python"
```

---

## Testing Envio

```bash
# Run all tests (78 tests)
uv run pytest

# Run tests with verbose output
uv run pytest -v

# Run specific test module
uv run pytest src/tests/test_analysis/test_import_analyzer.py

# Verify imports work
uv run python -c "from envio.cli import main; print('OK')"

# Test system profiler
uv run python -c "from envio.core import SystemProfiler; p = SystemProfiler(); print(p.profile())"

# Test fast resolver
uv run python -c "from envio.resolution import FastResolver; r = FastResolver(); print(r.check_uv_available())"

# Test LLM client
uv run python -c "from envio.llm import LLMClient; c = LLMClient(); print(c.list_providers())"

# Test Rich console
uv run python -c "from envio.ui import ConsoleUI; c = ConsoleUI(); c.print_success('Test passed!')"

# Test package mapping
uv run python -c "from envio.analysis import find_package_for_import; print(find_package_for_import('cv2'))"

# Run linter
uv run ruff check src/

# Run all checks
uv run ruff check src/ && uv run ruff format --check src/
```

---

## Notes

- `.env` file contains sensitive API keys (already in .gitignore)
- `uv.lock` tracks exact dependency versions
- Package installable via `uv pip install -e .`
- System detects RTX 4060 Laptop GPU correctly
- PyTorch index URL auto-selected based on CUDA version
- Windows PowerShell scripts work correctly now
- No more Unicode emoji encoding issues

---

*Last updated: March 26, 2026*
