# Envio - AI-Native Environment Orchestrator

Envio is an AI-powered Python environment manager that combines the speed of `uv` with intelligent dependency resolution.

## Features

- **Fast Resolution**: Uses `uv` for millisecond dependency resolution
- **Self-Healing**: AI-powered conflict resolution when dependencies fail (3 attempts)
- **Hardware-Aware**: Detects GPU/CUDA and optimizes packages accordingly
- **Cross-Platform**: Works on Windows, Linux, and macOS
- **Beautiful TUI**: Rich terminal output with timestamps, tables, and progress bars
- **Optimization Modes**: Optimize for training, inference, or development
- **Multi-Platform Support**: pip, uv, and conda package managers

## Prerequisites

| Requirement | Version | Install |
|-------------|---------|---------|
| **Python** | 3.10+ | [python.org](https://python.org/downloads) |
| **uv** | Any | `pip install uv` or [astral.sh/uv](https://astral.sh/uv) |
| **OpenAI API Key** | - | [platform.openai.com](https://platform.openai.com/api-keys) |
| **conda** | Optional | [miniconda](https://docs.conda.io/en/latest/miniconda.html) |

---

## Part 1: Installing Envio

This installs **Envio itself** (the CLI tool).

### Step 1: Clone the Repository

```bash
git clone https://github.com/yourusername/envio.git
cd envio
```

### Step 2: Install Envio

```bash
# Option A: With uv (recommended, faster)
uv pip install -e .

# Option B: With pip
pip install -e .
```

This creates a `.venv/` folder in the project directory and installs `envio` there.

### Step 3: Activate Envio's Virtual Environment

```bash
# Windows CMD
.venv\Scripts\activate.bat

# Windows PowerShell
.venv\Scripts\Activate.ps1

# Linux/macOS
source .venv/bin/activate
```

You should see `(envio)` at the start of your terminal prompt.

### Step 4: Create `.env` File

Create a `.env` file in the project root directory with your API key:

```bash
# Create the file
echo "OPENAI_API_KEY=sk-your-openai-api-key-here" > .env
```

Or manually create `.env` with this content:
```
OPENAI_API_KEY=sk-your-openai-api-key
```

### Step 5: Verify Installation

```bash
# Test that envio is installed
envio --help

# Test system profiling
envio doctor
```

---

## Part 2: Using Envio

Once Envio is installed and activated, you can use it to create environments for **your projects**.

### Quick Start

```bash
# Go to your project directory
cd /path/to/your/project

# Initialize environment from requirements.txt
envio init

# Or create environment from natural language
envio prompt "web app with flask and postgres"

# Or install specific packages
envio install requests flask numpy
```

### All Commands

#### `envio doctor`
Show system hardware profile and configuration.

```bash
envio doctor
```

Output includes:
- OS, Python, Shell information
- GPU/CUDA detection (uses nvidia-smi)
- VRAM capacity
- System RAM (uses psutil for accurate detection)
- Available package managers (pip/uv/conda)
- LLM configuration (API key status)

#### `envio init`
Scan current directory and set up environment from detected files.

```bash
# Use default package manager (uv)
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

#### `envio prompt`
Set up environment from natural language prompt.

```bash
# Basic usage
envio prompt "set up a web dev environment with flask"

# With options
envio prompt "ML environment with pytorch" --name my-env --path ~/envs
envio prompt "web app with fastapi" --env-type pip --cpu-only
envio prompt "data science with pandas matplotlib" -n ds-env -p ./envs

# Optimize for specific use case
envio prompt "train model with pytorch" --optimize-for training
envio prompt "deploy transformer model" --optimize-for inference
envio prompt "web app development" --optimize-for development
```

Options:
- `--name, -n`: Environment name (default: auto-generated)
- `--path, -p`: Installation path (default: `~/Documents/envs`)
- `--env-type, -e`: Package manager (pip/conda/uv, default: uv)
- `--cpu-only`: Force CPU-only mode (ignore GPU)
- `--optimize-for`: Optimize for specific use case (training/inference/development)
- `--verbose, -v`: Enable verbose output

#### `envio install`
Install packages directly.

```bash
# Basic usage
envio install requests flask numpy

# With options
envio install torch torchvision --env-type pip --name ml-env
envio install pandas scikit-learn --path ./envs --cpu-only
envio install flask requests -e uv -n web-app -p ~/envs

# Optimize for specific use case
envio install torch transformers --optimize-for training
envio install torch onnxruntime --optimize-for inference
envio install flask django --optimize-for development
```

Options:
- `--env-type, -e`: Package manager (pip/conda/uv, default: uv)
- `--name, -n`: Environment name (default: auto-generated)
- `--path, -p`: Installation path (default: `~/Documents/envs`)
- `--cpu-only`: Force CPU-only mode (ignore GPU)
- `--optimize-for`: Optimize for specific use case (training/inference/development)
- `--verbose, -v`: Enable verbose output

---

## Testing the Commands

```bash
# Test system profiling with psutil RAM detection
envio doctor

# Test installation with optimization
envio install requests flask --optimize-for development --path ./test_envs

# Test with CPU-only mode
envio install torch numpy --cpu-only

# Test natural language prompt
envio prompt "web app with fastapi"

# Test conda installation (requires conda installed)
envio install numpy pandas --env-type conda

# Test help
envio --help
envio install --help
envio prompt --help
```

---

## Output Example

```
+-----------------------------------------------------------------------------+
|                                Envio Install                                |
+------------------------ Direct package installation ------------------------+
01:36:12 [*] Optimizing for: development
+----------------------------- Installation Plan -----------------------------+
|                                                                             |
|  01:36:17                                                                   |
|  Environment: my-env                                                        |
|  Location: C:\Users\user\Documents\envs\my-env                              |
|  Package Manager: uv                                                        |
|  Mode: development                                                          |
|  Hardware: NVIDIA GeForce RTX 4060 Laptop GPU (8188 MB VRAM)                |
|                                                                             |
|  Packages (3):                                                              |
|    - requests                                                               |
|    - flask                                                                  |
|    - numpy                                                                  |
+-----------------------------------------------------------------------------+
01:36:17 [*] Resolving dependencies...
01:36:17 [+] Environment setup completed!
01:36:17 [*] To activate the environment:
+----------------------------------- BASH ------------------------------------+
| # PowerShell: & "C:\Users\user\Documents\envs\my-env\Scripts\Activate.ps1"  |
| # CMD: "C:\Users\user\Documents\envs\my-env\Scripts\activate.bat"           |
| # Git Bash: source "C:/Users/user/Documents/envs/my-env/Scripts/activate"   |
+-----------------------------------------------------------------------------+
```

---

## Architecture

```
src/envio/
├── cli.py                      # CLI commands
├── agents/                     # AI agents
│   ├── nlp_agent.py           # NLP processing
│   ├── dependency_resolution_agent.py  # Dependency resolution (with SelfHealingLoop)
│   └── command_construction_agent.py   # Command generation
├── core/                       # Core utilities
│   ├── system_profiler.py     # System/hardware detection (uses psutil)
│   ├── executor.py            # Script execution
│   ├── script_generator.py    # Cross-platform script generation (pip/uv/conda)
│   └── virtualenv_manager.py  # Virtual environment management
├── resolution/                 # Resolution engine
│   ├── fast_resolver.py       # Fast uv-based resolution
│   └── self_healing.py        # AI-powered conflict resolution (3 attempts)
├── llm/                        # LLM abstraction layer
│   ├── client.py              # LiteLLM wrapper
│   ├── prompts.py             # All prompts
│   └── parser.py              # Response parsing
├── tools/                      # Tools for agents
│   ├── package_lookup.py      # PyPI/Conda lookup
│   └── serper_search.py       # Web search
└── ui/                         # Terminal UI
    └── console.py             # Rich console with timestamps
```

---

## CI/CD

GitHub Actions workflow runs on:
- Ubuntu, Windows, macOS
- Python 3.10, 3.11, 3.12

Tests include:
- Linting (ruff)
- Formatting (ruff format)
- Type checking (mypy)
- Unit tests (pytest)
- Doctor command verification

### Setting Up GitHub Actions Secret

For CI/CD to work with AI features, you need to add the OpenAI API key as a secret:

1. Go to your GitHub repository
2. Click **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret**
4. Add:
   - **Name**: `OPENAI_API_KEY`
   - **Value**: Your OpenAI API key (starts with `sk-`)
5. Click **Add secret**

The CI workflow will now have access to the API key for testing.

---

## Supported Package Managers

- **uv**: Fast, recommended (default)
- **pip**: Standard Python package manager
- **conda**: For scientific computing (requires conda installed)

---

## How Self-Healing Works

When a package installation fails, Envio automatically:

1. **Detects the error** from stderr
2. **Analyzes with AI** to understand the conflict
3. **Suggests fixes** (different versions, alternative packages)
4. **Retries installation** (up to 3 attempts)
5. **Reports success** or final error

Example output when healing kicks in:

```
01:45:30 [*] Executing installation...
01:45:45 [-] Installation failed (attempt 1/3)
01:45:45 [*] Analyzing error with AI...

01:45:47 [!] Healing attempt 1/3
  Error: No matching distribution found for xformers==0.0.23+cu121
01:45:50 [+] Solution found: xformers==0.0.22+cu121
01:45:50 [*] Retrying with fixed packages...
01:45:52 [*] Executing installation...
01:46:10 [+] Environment setup completed!
```

---

## Troubleshooting

### "envio" Command Not Found

```bash
# Make sure you're in the envio directory and venv is activated
cd envio
.venv\Scripts\activate.bat  # Windows CMD
source .venv/bin/activate    # Linux/macOS

# Verify
envio --help
```

### API Key Not Found

```bash
# Check your .env file exists
cat .env

# Or set manually
export OPENAI_API_KEY=sk-...  # Linux/macOS
$env:OPENAI_API_KEY="sk-..."  # Windows PowerShell
```

### uv Not Found

```bash
pip install uv
# Or visit https://astral.sh/uv
```

### Conda Not Found

```bash
# Install conda from
https://docs.conda.io/en/latest/miniconda.html

# Or use uv instead (recommended)
envio init --env-type uv
```

### GPU Not Detected

```bash
# Check if nvidia-smi works
nvidia-smi

# If not, install NVIDIA drivers from
https://www.nvidia.com/Download/index.aspx
```

### Permission Errors

```bash
# Windows: Run as Administrator
# Linux/macOS: Use sudo
sudo pip install -e .
```

---

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
- AI-powered dependency resolution with re-validation
- Self-healing mechanism (3-attempt retry loop)
- Hardware-aware package selection
- Cross-platform support (Windows, Linux, macOS)
- Rich terminal UI with timestamps
- `--optimize-for` flag for training/inference/development
- Accurate RAM detection using psutil
- GitHub Actions CI workflow
- Multi-package manager support (pip, uv, conda)
