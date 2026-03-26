# Envio - AI-Powered Development Environment Manager

## Overview

**Envio** is an AI-powered Python environment manager that combines the speed of `uv` with intelligent dependency resolution. When standard resolution fails, Envio analyzes errors and automatically fixes conflicts using AI with multiple fallback strategies.

Think of it as having an AI assistant that handles all your dependency management headaches - you just tell it what packages you need, and it handles the rest.

---

## Tech Stack and Technologies

### Core Framework
- **Python 3.10+** - Main programming language
- **LiteLLM** - Multi-provider LLM integration (supports 100+ providers)
- **uv** - Fast dependency resolution

### Key Dependencies
| Category | Packages |
|----------|----------|
| AI/LLM | `litellm`, `tenacity` |
| CLI | `click`, `rich` |
| Utilities | `python-dotenv`, `requests`, `httpx`, `pyyaml`, `psutil`, `packaging` |
| Testing | `pytest`, `pytest-asyncio` |
| Linting | `ruff`, `mypy` |

### External Services
- **OpenAI API** (or any LiteLLM-supported provider) - For LLM processing
- **Serper API** - For web search (package lookup fallback)
- **PyPI** - Python package repository lookup
- **Conda** - Alternative package manager support

---

## Directory Structure

```
src/envio/
├── __init__.py
├── __main__.py
├── cli.py                      # CLI commands (doctor, init, install, prompt, list, remove, activate)
├── agents/                     # AI agents
│   ├── nlp_agent.py           # NLP processing
│   ├── dependency_resolution_agent.py  # Dependency resolution (with SerperSearchTool)
│   └── command_construction_agent.py   # Command generation
├── analysis/                   # Code analysis
│   ├── import_analyzer.py     # Import detection (uses sys.stdlib_module_names)
│   ├── syntax_detector.py     # Code age detection
│   ├── version_inference.py   # Version compatibility
│   └── package_mapping.py     # Import-to-package name mapping (dynamic PyPI lookup)
├── commands/                   # CLI command implementations
│   └── resurrect.py           # Repository resurrection
├── core/                       # Core utilities
│   ├── system_profiler.py     # System/hardware detection (singleton, uses psutil)
│   ├── executor.py            # Script execution
│   ├── script_generator.py    # Cross-platform script generation (pip/uv/conda)
│   └── virtualenv_manager.py  # Virtual environment management
├── resolution/                 # Resolution engine
│   ├── fast_resolver.py       # Fast uv-based resolution
│   └── self_healing.py        # AI-powered conflict resolution (3 attempts, fallback strategies)
├── llm/                        # LLM abstraction layer
│   ├── client.py              # LiteLLM wrapper (with tenacity retry)
│   ├── prompts.py             # All prompts
│   └── parser.py              # Response parsing
├── tools/                      # Tools for agents
│   ├── package_lookup.py      # PyPI/Conda lookup
│   └── serper_search.py       # Web search (wired into DependencyResolver)
├── ui/                         # Terminal UI
│   └── console.py             # Rich console with timestamps
└── utils/                      # Utilities
    ├── __init__.py
    ├── sanitize.py            # Shell input sanitization (shlex.quote)
    └── bash_executor.py       # Safe subprocess execution (no shell=True)
```

---

## Main Features and Functionality

### 1. Natural Language Input
Users can describe their package needs in plain English. For example:
- "I need tensorflow with GPU support and scikit-learn for a data science project"
- "Set up a fastapi web server with uvicorn and sqlalchemy"

### 2. Hardware-Aware Installation
- Detects GPU/CUDA automatically
- Optimizes PyTorch installation for detected hardware
- Supports CPU-only mode for testing

### 3. Self-Healing Resolution
When installation fails, Envio:
1. Detects the error
2. Checks for duplicate errors (hash-based deduplication)
3. Applies fallback strategies:
   - Relax version constraints
   - Find alternative packages
   - Skip optional dependencies
4. Validates fixes using FastResolver
5. Retries up to 3 times

### 4. Environment Management
- `envio list` - List all virtual environments
- `envio activate` - Show activation command
- `envio remove` - Uninstall packages from environment

### 5. Import-to-Package Mapping
- Dynamic PyPI lookup for imports (cv2 → opencv-python, PIL → Pillow)
- Local caching for performance
- No hardcoded mappings

### 6. Cross-Platform Support
- Windows (PowerShell/CMD)
- Linux (Bash)
- macOS (Bash/Zsh)

---

## CLI Commands

### `envio doctor`
Show system hardware profile and configuration.

### `envio init`
Scan current directory and set up environment from detected files.

### `envio prompt`
Set up environment from natural language prompt.

```bash
envio prompt "ML environment with pytorch" --name my-env --path ~/envs
envio prompt "web app with fastapi" --env-type pip --cpu-only
envio prompt "train model with pytorch" --optimize-for training
```

### `envio install`
Install packages directly.

```bash
envio install requests flask numpy
envio install torch torchvision --env-type pip --name ml-env
envio install torch transformers --optimize-for training
```

### `envio list`
List all virtual environments.

```bash
envio list
envio list --path /path/to/envs
```

### `envio activate`
Show activation command for a virtual environment.

```bash
envio activate --env my-env
envio activate --path /path/to/.venv
```

### `envio remove`
Remove packages from a virtual environment.

```bash
envio remove numpy pandas --env my-env
envio remove requests --path /path/to/.venv
```

---

## Workflow

```
User Input (Natural Language or Package List)
        ↓
    NLP Agent (Extract packages, env type, versions)
        ↓
Dependency Resolution Agent (PyPI lookup + Serper search fallback)
        ↓
Command Construction Agent (Generate pip/conda/uv commands)
        ↓
Script Generator (Create cross-platform setup script)
        ↓
Execute script (with self-healing retry on failure)
```

---

## Configuration

### Environment Variables (`.env`)
Create a `.env` file with the following:

```env
# Required for AI features
OPENAI_API_KEY=your_openai_api_key_here

# Optional: For web search fallback
SERPER_API_KEY=your_serper_api_key_here

# Optional: LLM configuration
ENVIO_LLM_MODEL=gpt-4o-mini
ENVIO_LLM_API_KEY=your_api_key_here
ENVIO_LLM_API_BASE=http://localhost:11434/v1  # For local models
```

### Requirements
Install dependencies:
```bash
uv pip install -e .
```

---

## Testing

```bash
# Run all tests
uv run pytest

# Run tests with verbose output
uv run pytest -v

# Run specific test module
uv run pytest src/tests/test_analysis/test_import_analyzer.py

# Run linter
uv run ruff check src/
```

---

## License

MIT License - see [LICENSE](LICENSE) for details.
