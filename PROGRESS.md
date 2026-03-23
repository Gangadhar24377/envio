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

---

## Roadmap Phases

### Phase 1: The Open-Source MVP (V1 Launch) - COMPLETE

- [x] **1.1 Core Infrastructure & Cleanup (P0)**
- [x] **1.2 OS-Agnostic Execution Engine (P0)**
- [x] **1.3 The Hybrid "Self-Healing" Resolver (P1)**
- [x] **1.4 Hardware-Aware ML Setup (P1)**
- [x] **1.5 Rich Terminal UI (P1)**
- [x] **1.6 CrewAI → LiteLLM Migration**

### Phase 2: The "Reproducibility" Engine (Growth)

- [ ] 2.1 Ghost-Town Repo Resurrection
- [ ] 2.2 Jailbroken Local LLM Execution
- [ ] 2.3 AI-Optimized Containerization
- [ ] 2.4 Semantic Environment Diffing

### Phase 3: Team & Enterprise Workflows (Maturity)

- [ ] 3.1 The Envio GitHub Action
- [ ] 3.2 Security & CVE Profiling
- [ ] 3.3 Dependency Cost Estimation

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

### Programmatic Usage
```python
from envio.core import SystemProfiler
from envio.llm import LLMClient
from envio.resolution import FastResolver
from envio.ui import ConsoleUI

# System profiling
profile = SystemProfiler().profile()
print(f"GPU: {profile.gpu.name}")

# Fast resolution
resolver = FastResolver()
result = resolver.resolve(["requests", "flask"])

# LLM client
llm = LLMClient()
response = llm.chat(user_prompt="What is Python?")
print(response.content)

# Rich console
console = ConsoleUI()
console.print_success("Setup complete!")
```

---

## Testing Envio

```bash
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

*Last updated: March 19, 2026*
