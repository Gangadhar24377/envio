# Envio - AI-Native Environment Orchestrator

Envio is an AI-powered Python environment manager that combines the speed of `uv` with intelligent dependency resolution.

## Features

- **Fast Resolution**: Uses `uv` for millisecond dependency resolution
- **Self-Healing**: AI-powered conflict resolution when dependencies fail
- **Hardware-Aware**: Detects GPU/CUDA and optimizes packages accordingly
- **Cross-Platform**: Works on Windows, Linux, and macOS
- **Beautiful TUI**: Rich terminal output with timestamps, tables, and progress bars

## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/envio.git
cd envio

# Install with uv
uv pip install -e .

# Or install with pip
pip install -e .
```

## Configuration

Create a `.env` file with your API keys:

```bash
# Required for AI features
OPENAI_API_KEY=sk-your-openai-api-key

# Optional - for web search fallback
SERPER_API_KEY=

# Optional - LLM configuration
ENVIO_LLM_MODEL=gpt-4o-mini
ENVIO_LLM_API_KEY=sk-...
```

## Commands

### `envio doctor`

Show system hardware profile and configuration.

```bash
envio doctor
```

Output includes:
- OS, Python, Shell information
- GPU/CUDA detection
- VRAM capacity
- Available package managers
- LLM configuration

### `envio init`

Scan current directory and set up environment from detected files.

```bash
# Use detected package manager from requirements file
envio init

# Specify package manager
envio init --env-type pip
envio init --env-type uv
envio init --env-type conda

# Verbose output
envio init --verbose
```

Scans for:
- `requirements.txt`
- `pyproject.toml`
- `setup.py`
- `environment.yml`
- Python files (auto-detects imports)

### `envio prompt`

Set up environment from natural language prompt.

```bash
# Basic usage
envio prompt "set up a web dev environment with flask"

# With options
envio prompt "ML environment with pytorch" --name my-env --path ~/envs
envio prompt "web app with fastapi" --env-type pip --cpu-only
envio prompt "data science with pandas matplotlib" -n ds-env -p ./envs
```

Options:
- `--name, -n`: Environment name (default: auto-generated)
- `--path, -p`: Installation path (default: `~/Documents/envs`)
- `--env-type, -e`: Package manager (pip/conda/uv, default: uv)
- `--cpu-only`: Force CPU-only mode (ignore GPU)
- `--verbose, -v`: Enable verbose output

### `envio install`

Install packages directly.

```bash
# Basic usage
envio install requests flask numpy

# With options
envio install torch torchvision --env-type pip --name ml-env
envio install pandas scikit-learn --path ./envs --cpu-only
envio install flask requests -e uv -n web-app -p ~/envs
```

Options:
- `--env-type, -e`: Package manager (pip/conda/uv, default: uv)
- `--name, -n`: Environment name (default: auto-generated)
- `--path, -p`: Installation path (default: `~/Documents/envs`)
- `--cpu-only`: Force CPU-only mode (ignore GPU)
- `--verbose, -v`: Enable verbose output

## Output Example

```
+-----------------------------------------------------------------------------+
|                                Envio Install                                |
+------------------------ Direct package installation ------------------------+
+----------------------------- Installation Plan -----------------------------+
|  Environment: my-env                                                        |
|  Location: C:\Users\user\Documents\envs\my-env                              |
|  Package Manager: uv                                                        |
|  Hardware: NVIDIA GeForce RTX 4060 Laptop GPU (8188 MB VRAM)                |
|                                                                             |
|  Packages (3):                                                              |
|    - requests                                                               |
|    - flask                                                                  |
|    - numpy                                                                  |
+-----------------------------------------------------------------------------+
12:34:56 [*] Resolving dependencies...
12:34:57 [+] Environment setup completed!
12:34:57 [*] To activate the environment:
+----------------------------------- BASH ------------------------------------+
| # PowerShell: & "C:\Users\user\Documents\envs\my-env\Scripts\Activate.ps1"  |
| # CMD: "C:\Users\user\Documents\envs\my-env\Scripts\activate.bat"           |
| # Git Bash: source "C:/Users/user/Documents/envs/my-env/Scripts/activate"   |
+-----------------------------------------------------------------------------+
```

## Architecture

```
src/envio/
├── cli.py                      # CLI commands
├── agents/                     # AI agents
│   ├── nlp_agent.py           # NLP processing
│   ├── dependency_resolution_agent.py  # Dependency resolution
│   └── command_construction_agent.py   # Command generation
├── core/                       # Core utilities
│   ├── system_profiler.py     # System/hardware detection
│   ├── executor.py            # Script execution
│   ├── script_generator.py    # Cross-platform script generation
│   └── virtualenv_manager.py  # Virtual environment management
├── resolution/                 # Resolution engine
│   ├── fast_resolver.py       # Fast uv-based resolution
│   └── self_healing.py        # AI-powered conflict resolution
├── llm/                        # LLM abstraction layer
│   ├── client.py              # LiteLLM wrapper
│   ├── prompts.py             # All prompts
│   └── parser.py              # Response parsing
├── tools/                      # Tools for agents
│   ├── package_lookup.py      # PyPI/Conda lookup
│   └── serper_search.py       # Web search
└── ui/                         # Terminal UI
    └── console.py             # Rich console
```

## Supported Package Managers

- **uv**: Fast, recommended (default)
- **pip**: Standard Python package manager
- **conda**: For scientific computing

## System Requirements

- Python 3.10+
- uv (optional, for fast resolution)
- OpenAI API key (for AI features)

## License

MIT License - see [LICENSE](LICENSE) for details.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Run linting: `ruff check src/`
4. Run formatting: `ruff format src/`
5. Submit a pull request

## Changelog

### v0.1.0 (Latest)
- Initial release
- CLI commands: doctor, init, install, prompt
- AI-powered dependency resolution
- Hardware-aware package selection
- Cross-platform support (Windows, Linux, macOS)
- Rich terminal UI with timestamps
