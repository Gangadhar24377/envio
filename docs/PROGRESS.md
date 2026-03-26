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

#### Shell Injection Protection
- Removed `shell=True` from subprocess calls
- Added `shlex.quote()` for all user inputs in shell scripts
- Used list-based subprocess.run() for safer execution

#### Semantic Version Comparison
- Uses `packaging.version.Version` instead of string comparison
- Fixes incorrect results like `"1.9" > "1.82.6"`

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
