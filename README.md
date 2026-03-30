# Envio

<p align="center">
  <a href="https://pypi.org/project/envio-ai/"><img src="https://img.shields.io/pypi/v/envio-ai" alt="PyPI Version"></a>
  <a href="https://pypi.org/project/envio-ai/"><img src="https://img.shields.io/pypi/pyversions/envio-ai" alt="Python Versions"></a>
  <a href="LICENSE"><img src="https://img.shields.io/pypi/l/envio-ai" alt="License"></a>
  <a href="https://pypi.org/project/envio-ai/"><img src="https://img.shields.io/pypi/dm/envio-ai" alt="Downloads"></a>
  <a href="https://github.com/Gangadhar24377/envio/actions/workflows/ci.yml"><img src="https://github.com/Gangadhar24377/envio/actions/workflows/ci.yml/badge.svg?branch=master" alt="CI"></a>
</p>

<p align="center">
  <strong>AI-Native Environment Orchestrator</strong><br>
  <em>"It understands what you want, not just what you type."</em>
</p>

---

## Why Envio?

Ever spent hours fixing dependency conflicts? Wish you could just tell your computer "I need a web app with Flask" and have everything just work? That's Envio.

| Problem | Envio's Solution |
|---------|------------------|
| "What package provides `import cv2`?" | Auto-detects common imports (`cv2` -> `opencv-python`) |
| Dependency conflicts | AI resolves them automatically (3 attempts with self-healing) |
| Wrong package names | Self-healing finds the correct one |
| GPU vs CPU packages | Hardware-aware installation |
| Security vulnerabilities | Built-in `envio audit` |
| Finding existing environments | Registry tracks all created environments |

---

## Installation

```bash
pip install envio-ai
```

That's it. You're ready to go.

---

## Quick Start

```bash
# Configure your API key (optional - enables AI features)
envio config api sk-your-openai-key

# Optional: Enable web search for better package suggestions
# Without this, the app still works with just AI (LLM)
envio config serper-api your-serper-key

# Create environment from natural language
envio prompt "data science with pandas and sklearn"

# Or from existing requirements.txt
envio init .

# Or install packages directly
envio install requests flask
```

---

## Commands at a Glance

| Command | Description |
|---------|-------------|
| `envio prompt "flask api"` | Create env from natural language |
| `envio init .` | Initialize from requirements.txt |
| `envio install numpy pandas` | Install packages directly |
| `envio list` | List all environments |
| `envio activate my-env` | Show activation commands |
| `envio audit` | Scan for vulnerabilities |
| `envio lock` | Generate reproducible lockfile |
| `envio export` | Export to dockerfile/devcontainer |
| `envio resurrect` | Analyze old repos and revive |
| `envio doctor` | Show hardware profile |

---

## File Structure

```
envio/
├── src/envio/
│   ├── cli.py                    # Main CLI entry point
│   ├── cli_helpers.py            # Shared helper functions
│   ├── config.py                 # Configuration management
│   ├── __init__.py               # Package init with version
│   ├── __main__.py               # Package entry point
│   │
│   ├── commands/                 # CLI commands (modular)
│   │   ├── __init__.py
│   │   ├── activate.py           # Show activation commands
│   │   ├── audit.py              # Security vulnerability scan
│   │   ├── config.py             # Configuration management
│   │   ├── doctor.py             # System hardware profile
│   │   ├── export.py             # Export to various formats
│   │   ├── init.py               # Initialize from project files
│   │   ├── install.py            # Direct package installation
│   │   ├── list_envs.py           # List registered environments
│   │   ├── lock.py                # Generate lockfiles
│   │   ├── prompt.py              # Natural language env creation
│   │   ├── remove.py              # Remove packages
│   │   └── resurrect.py           # Analyze and revive old repos
│   │
│   ├── agents/                   # AI agents
│   │   ├── nlp_agent.py           # Natural language processing
│   │   ├── dependency_resolution_agent.py
│   │   └── command_construction_agent.py
│   │
│   ├── analysis/                 # Code analysis
│   │   ├── import_analyzer.py    # Scan for imports
│   │   ├── syntax_detector.py    # Detect deprecated patterns
│   │   ├── version_inference.py  # Infer package versions
│   │   └── package_mapping.py    # Import to PyPI mapping
│   │
│   ├── core/                     # Core functionality
│   │   ├── registry.py           # Environment registry
│   │   ├── virtualenv_manager.py # Venv management
│   │   ├── system_profiler.py    # Hardware detection
│   │   ├── executor.py           # Script execution
│   │   └── script_generator.py   # Installation scripts
│   │
│   ├── llm/                      # LLM integration
│   │   ├── client.py             # LLM API client
│   │   ├── parser.py             # Response parsing
│   │   └── prompts.py            # LLM prompts
│   │
│   ├── resolution/                # Dependency resolution
│   │   ├── fast_resolver.py      # Quick resolution
│   │   └── self_healing.py       # Auto-fix failures
│   │
│   ├── tools/                    # External tools
│   │   ├── serper_search.py      # Web search
│   │   └── package_lookup.py     # PyPI lookups
│   │
│   ├── ui/                       # User interface
│   │   └── console.py            # Rich console output
│   │
│   └── utils/                    # Utilities
│       ├── http_utils.py
│       ├── paths.py
│       ├── sanitize.py
│       └── version_utils.py
│
├── pyproject.toml                # Package configuration
├── COMMANDS.md                   # Detailed command reference
├── CONTRIBUTING.md               # Contribution guidelines
├── SECURITY.md                   # Security policy
└── README.md                     # This file
```

---

## Features

### Natural Language Environment Creation

```bash
envio prompt "machine learning with pytorch and transformers"
```

Just describe what you need. Envio understands domains and picks the right packages.

### Self-Healing + Web Search (Optional)

When things go wrong, Envio tries to fix itself:
- Wrong package name → Finds the correct one
- Version conflict → Suggests compatible versions
- Package not found → Searches for alternatives via web search (if Serper configured)
- Installation failure → Retries with fixes (up to 3 attempts)

The app works perfectly with just an LLM API key. Adding a free Serper API key enables enhanced web search for better package suggestions.

### Hardware-Aware

Envio detects your GPU and installs the right packages:
- NVIDIA CUDA for NVIDIA GPUs
- Metal for Apple Silicon
- CPU-only when needed

### Environment Registry

All environments created by Envio are tracked:
```bash
envio list                    # See all environments
envio audit                   # Interactive environment picker
envio export -n my-env        # Export by name
```

### Security Built-In

```bash
envio audit                   # Shows picker if no env specified
envio audit -n my-env        # Audit specific environment
envio audit -n my-env --fix  # Auto-fix vulnerabilities
```

### Multiple Export Formats

```bash
envio export -n my-env --format requirements
envio export -n my-env --format dockerfile
envio export -n my-env --format devcontainer
```

### Resurrect Old Repos

```bash
envio resurrect https://github.com/user/old-repo
envio resurrect ./path/to/old-project
```

---

## Configuration

```bash
# Required: Set API key (auto-detects provider: openai, anthropic, etc.)
envio config api sk-your-openai-key

# Set model (optional, defaults to gpt-4o-mini)
envio config model gpt-4o-mini

# Optional: Enable web search for enhanced package suggestions
# Get a free key at https://serper.dev
envio config serper-api your-key

# View configuration
envio config show

# Set defaults
envio config set default_envs_dir ~/my-envs
envio config set preferred_package_manager uv
```

---

## Supported Tools

- **Package Managers**: pip, uv (default), conda
- **LLM Providers**: OpenAI, Anthropic, Together AI, Ollama (local)
- **Platforms**: Windows, Linux, macOS

---

## Environment Variables

```bash
# Quiet mode (great for CI/CD)
export ENVIO_QUIET=1

# No colors
export NO_COLOR=1
```

---

## Documentation

- [Command Reference](COMMANDS.md) - Every command explained
- [Contributing](CONTRIBUTING.md) - Want to contribute?
- [Security](SECURITY.md) - Vulnerability reporting

---

## License

MIT - use it however you want.

---

<p align="center">
Made with ☕ by <a href="https://github.com/Gangadhar24377">Gangadhar Kambhamettu</a>
</p>
