# Envio - AI-Powered Development Environment Manager

## Overview

**Envio** is an AI-powered Python environment manager that combines the speed of `uv` with intelligent dependency resolution. It provides automated environment setup, self-healing dependency resolution, hardware-aware optimization, and cross-platform support.

## Key Features

- **Fast Resolution**: Uses `uv` for millisecond dependency resolution
- **Self-Healing**: AI-powered conflict resolution when dependencies fail (3 attempts)
- **Hardware-Aware**: Detects GPU/CUDA/Apple Silicon MPS and optimizes packages accordingly
- **Cross-Platform**: Works on Windows, Linux, and macOS (including Apple Silicon)
- **Beautiful TUI**: Rich terminal output with timestamps, tables, and progress bars
- **Optimization Modes**: Optimize for training, inference, or development
- **Multi-Platform Support**: pip, uv, and conda package managers
- **Environment Registry**: Tracks all envio-created environments in `~/.envio/environments.json`
- **Security Audit**: Scan environments for known vulnerabilities with `envio audit`
- **Reproducible Lockfiles**: Generate lockfiles with `envio lock`
- **Multiple Export Formats**: Export as requirements.txt, Dockerfile, or devcontainer.json
- **Dry-Run Mode**: Preview changes before execution with `--dry-run`
- **Interactive Confirmation**: Optional prompts before making changes
- **Multi-Provider LLM**: Supports OpenAI and Ollama with auto-detection
**Envio** is an AI-powered Python environment manager that combines the speed of `uv` with intelligent dependency resolution. When standard resolution fails, Envio analyzes errors and automatically fixes conflicts using AI with multiple fallback strategies.

## Directory Structure

```
src/envio/
├── cli.py                      # CLI commands
├── agents/                     # AI agents
│   ├── nlp_agent.py           # NLP processing
│   ├── dependency_resolution_agent.py  # Dependency resolution (with SelfHealingLoop)
│   └── command_construction_agent.py   # Command generation
├── core/                       # Core utilities
│   ├── system_profiler.py     # System/hardware detection (NVIDIA CUDA, Apple Silicon MPS)
│   ├── executor.py            # Script execution
│   ├── script_generator.py    # Cross-platform script generation (pip/uv/conda)
│   └── virtualenv_manager.py  # Virtual environment management
├── resolution/                 # Resolution engine
│   ├── fast_resolver.py       # Fast uv-based resolution
│   └── self_healing.py        # AI-powered conflict resolution (3 attempts)
├── llm/                        # LLM abstraction layer
│   ├── client.py              # LiteLLM wrapper with OpenAI/Ollama auto-detection
│   ├── prompts.py             # All prompts
│   └── parser.py              # Response parsing
├── tools/                      # Tools for agents
│   ├── package_lookup.py      # PyPI/Conda lookup
│   └── serper_search.py       # Web search
└── ui/                         # Terminal UI
    └── console.py             # Rich console with timestamps
```

## Installation

1. Clone the repository
2. Install with `pip install -e .` or `uv pip install -e .`
3. Create a `.env` file with your OpenAI API key (or use Ollama)
4. Activate the virtual environment

## Configuration
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

### OpenAI (Default)

```bash
# In .env file
OPENAI_API_KEY=sk-your-openai-api-key-here

# Optional: specify model (defaults to gpt-4o-mini)
ENVIO_LLM_MODEL=gpt-4o-mini
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

### Ollama (Local)

```bash
# Ensure Ollama is running
ollama serve

# Pull a model (if not already)
ollama pull llama3

# In .env file - model is required for Ollama
ENVIO_LLM_MODEL=llama3

# Optional: custom host
ENVIO_OLLAMA_HOST=http://localhost:11434
```

### Auto-Detection Logic

Envio automatically detects which provider to use:

1. If `OPENAI_API_KEY` is set → Uses OpenAI (default model: gpt-4o-mini)
2. If Ollama is running → Uses Ollama (default model: llama3)
3. If neither is available → Shows clear error message

## Usage Examples

```bash
# System check (shows hardware profile including Apple Silicon)
envio doctor

# Initialize from existing files
envio init

# Natural language prompt
envio prompt "web app with flask and postgres"

# Direct package installation
envio install requests flask numpy
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

# Generate lockfile
envio lock -n my-env

# Export to different formats
envio export -n my-env --format dockerfile

# Security audit
envio audit -n my-env --severity high
```

## Hardware Detection

### NVIDIA GPU
- Detects GPU name, VRAM, CUDA version via nvidia-smi
- Auto-selects PyTorch index URL based on CUDA version
- Recommends batch size and xformers based on VRAM

### Apple Silicon
- Dynamically detects chip model (M1/M2/M3/M4) via sysctl
- Checks PyTorch MPS availability
- Shows unified memory and macOS version
- Works on arm64 architecture

## Testing

Run tests with `pytest`:
```bash
pytest src/tests/
```

## Test Commands
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

```bash
# Test LLM auto-detection (OpenAI)
uv run python -c "from envio.llm import LLMConfig; c = LLMConfig.from_env(); print(f'Provider: {c.provider}, Model: {c.model}')"

# Test LLM client chat
uv run python -c "from envio.llm import LLMClient; c = LLMClient(); print(c.chat(user_prompt='Say hi').content)"

# Test system profiler (NVIDIA)
uv run python -c "from envio.core import SystemProfiler; p = SystemProfiler(); g = p.detect_gpu(); print(f'GPU: {g.name}, Backend: {g.compute_backend}')"

# Test Ollama availability check
uv run python -c "from envio.llm import is_ollama_available; print(f'Ollama running: {is_ollama_available()}')"

# Test Ollama model listing
uv run python -c "from envio.llm import list_ollama_models; print(f'Models: {list_ollama_models()}')"

# Test full profile
uv run python -c "from envio.core import SystemProfiler; print(SystemProfiler().profile())"

# Run doctor command
uv run envio doctor

# Run install command
uv run envio install requests flask

# Run linting
uv run ruff check src/envio/llm/client.py src/envio/core/system_profiler.py

# Run tests
uv run pytest src/tests/ -v
```

## CI/CD

GitHub Actions workflow runs tests on Ubuntu, Windows, and macOS with Python 3.10, 3.11, and 3.12.

## License

MIT License
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
