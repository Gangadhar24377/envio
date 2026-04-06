# Envio Command Reference

Comprehensive guide to all Envio CLI commands with examples.

---

## Installation & Setup

### Basic Setup

```bash
# Install envio from PyPI
pip install envio-ai

# Or install from source
git clone https://github.com/Gangadhar24377/envio.git
cd envio
pip install -e .

# Verify installation
envio --version
```

### Configure API Key

```bash
# Set OpenAI API key (auto-detects provider)
envio config api sk-your-openai-key

# Set Anthropic API key
envio config api sk-ant-your-anthropic-key

# Set model
envio config model gpt-4o-mini

# Set Serper API key (for web search enhancement)
envio config serper-api your-serper-key

# View configuration
envio config show

# Set default environments directory
envio config set default_envs_dir ~/my-envs

# Set preferred package manager
envio config set preferred_package_manager uv
```

---

## Core Commands

### `envio prompt`

Create an environment from natural language description.

```bash
# Basic usage - describe what you want
envio prompt "web app with flask and react"

# With custom name
envio prompt "data science environment" -n my-data-env

# With custom path
envio prompt "data science environment" -p ~/envs

# With GPU optimization
envio prompt "machine learning with pytorch" --optimize-for training

# CPU-only mode
envio prompt "data analysis with pandas" --cpu-only

# Dry run - see what would be installed without installing
envio prompt "flask api" --dry-run

# Specify package manager
envio prompt "fastapi app" -e uv

# Skip confirmation prompt
envio prompt "simple script" -y
```

**How it works:**
1. Analyzes your request using NLP
2. Detects your hardware (GPU, VRAM, CUDA)
3. Resolves dependencies with AI
4. Creates environment with self-healing if needed

---

### `envio init`

Initialize environment from existing project files (requirements.txt, pyproject.toml, etc.).

```bash
# Auto-detect requirements files in current directory
envio init .

# From specific directory
envio init /path/to/project

# With specific name
envio init . -n my-environment

# Specify package manager
envio init . -e conda

# Skip confirmation
envio init . -y
```

**Detects:**
- `requirements.txt`
- `pyproject.toml`
- `setup.py`
- `environment.yml`
- Python imports (scans `.py` files)

---

### `envio install`

Install packages directly to an environment.

```bash
# Install (prompts for name and path)
envio install requests

# With name and path
envio install numpy pandas -n my-env -p ~/envs

# With explicit path only
envio install flask -p /path/to/env

# Install with specific versions
envio install "numpy>=1.24" "pandas>=2.0"

# Using different package manager
envio install flask -e pip

# Dry run
envio install flask --dry-run

# Skip confirmation
envio install flask -y
```

**Note:** If no name/path provided, prompts interactively for both.

---

### `envio add`

Add packages to the current project and install them into `.venv`.

```bash
# Add packages (creates pyproject.toml if none exists)
envio add requests flask

# Add with natural language
envio add "fastapi with postgres and redis"

# Add to a dependency group
envio add pytest --group dev
envio add black isort --group test

# Force requirements.txt mode even if pyproject.toml exists
envio add requests --legacy

# Dry run - see what would happen without making changes
envio add flask --dry-run

# Skip confirmation prompt
envio add numpy -y
```

**Decision tree:**
1. `pyproject.toml` present → edits `[project.dependencies]` (or optional group)
2. `requirements.txt` present → edits `requirements.txt`
3. Neither exists → creates a minimal `pyproject.toml`, then installs

**How it works:**
1. Detects existing project format (pyproject.toml, requirements.txt, or none)
2. Resolves packages (supports natural language via NLP agent)
3. Validates package names against PyPI
4. Updates the project file
5. Installs into `./.venv` using uv

---

### `envio sync`

Sync the environment with the current project file. Installs exactly the packages declared in `pyproject.toml` or `requirements.txt`.

```bash
# Sync default dependencies only
envio sync

# Sync including a specific dependency group
envio sync --group dev
envio sync --group dev --group test

# Sync all optional dependency groups
envio sync --all-groups

# Dry run - see what would be installed
envio sync --dry-run

# Skip confirmation prompt
envio sync -y
```

**Behavior by project mode:**
- **pyproject.toml**: installs `[project.dependencies]` + any requested groups
- **requirements.txt**: installs everything in the file
- **No project file**: errors — run `envio add <packages>` first

**When to use:** After cloning a repo, switching branches, or updating dependency declarations to ensure your `.venv` matches the project file exactly.

---

### `envio migrate`

Convert any Python project format to a standards-compliant PEP 621 `pyproject.toml`.

```bash
# Auto-detect format and migrate
envio migrate

# Migrate a specific directory
envio migrate /path/to/project

# Force a specific source format
envio migrate --from Poetry
envio migrate --from Pipenv
envio migrate --from conda

# Dry run - see what would be written
envio migrate --dry-run

# Keep original project files after migration
envio migrate --keep
```

**Supported source formats:**
- `requirements.txt` (+ `requirements-dev.txt`, `requirements-test.txt`, etc.)
- `[tool.poetry]` in pyproject.toml (Poetry)
- `Pipfile` / `Pipfile.lock` (Pipenv)
- `environment.yml` / `environment.yaml` (conda)
- `setup.py` + `setup.cfg` (legacy setuptools)
- `requirements.in` (pip-tools)
- `pixi.toml` (pixi)

**What it does:**
1. Detects the source format (or uses `--from` if specified)
2. Extracts project metadata, dependencies, and dependency groups
3. Creates a PEP 621 compliant `pyproject.toml`
4. Optionally removes original project files (use `--keep` to preserve them)

**After migration:**
```bash
envio sync              # install all dependencies
envio sync --all-groups # include dev/test groups
```

---

## Environment Management

### `envio list`

List all environments created by Envio.

```bash
# List all environments
envio list
```

Shows:
- Environment name
- Path to environment
- Number of packages
- Package manager used
- Creation date
- Recreation commands

---

### `envio activate`

Show activation commands for an environment.

```bash
# By name (checks registry, then default location)
envio activate -n my-env

# With explicit path
envio activate -p /path/to/env
```

Shows commands for:
- PowerShell
- CMD
- Git Bash

---

### `envio remove`

Remove packages from an environment.

```bash
# Remove packages from environment by name
envio remove numpy pandas -n my-env

# With explicit path
envio remove flask -p /path/to/env

# Confirm removal
envio remove package1 package2 -n my-env -y
```

---

## System & Diagnostics

### `envio doctor`

Show system hardware profile and configuration status.

```bash
# Check system info
envio doctor

# Verbose output
envio doctor -v
```

Shows:
- OS type and version
- Python version
- Shell type
- GPU information (if available)
- VRAM
- CUDA version
- Recommended batch sizes
- Available package managers
- LLM configuration status

---

### `envio audit`

Scan environment for known security vulnerabilities.

```bash
# Shows interactive picker (lists all environments)
envio audit

# Audit specific environment by name
envio audit -n my-env

# Audit with explicit path
envio audit -p /path/to/env

# Auto-fix vulnerabilities
envio audit -n my-env --fix

# Filter by severity
envio audit -n my-env --severity high
```

**When no environment specified:**
- Shows current directory `.venv` if exists
- Lists all registered environments
- Explains how to specify: `-n <name>` or `-p <path>`

---

## Export & Lock

### `envio export`

Export environment configuration to various formats.

```bash
# Shows interactive picker (lists all environments)
envio export

# By name
envio export -n my-env --format requirements

# With explicit path
envio export -p /path/to/env --format requirements

# Export to requirements.txt (default)
envio export -n my-env

# Export to Dockerfile
envio export -n my-env --format dockerfile

# Export to devcontainer.json (VS Code)
envio export -n my-env --format devcontainer

# Custom output file
envio export -n my-env -o my-requirements.txt
```

---

### `envio lock`

Generate a lockfile for reproducible environments.

```bash
# By name
envio lock -n my-env

# With explicit path
envio lock -p /path/to/env

# Custom filename
envio lock -n my-env -o requirements.lock

# Text format (default)
envio lock -n my-env --format text

# JSON format
envio lock -n my-env --format json
```

---

## Advanced Features

### `envio resurrect`

Analyze dead/unmaintained repositories and generate requirements.

```bash
# From local directory
envio resurrect /path/to/old-repo

# From current directory
envio resurrect .

# From GitHub URL
envio resurrect https://github.com/user/old-repo

# With environment creation
envio resurrect https://github.com/user/old-repo -n revived-env

# Using conda
envio resurrect /path/to/repo -e conda

# With explicit path
envio resurrect . -p /path/to/save
```

**What it does:**
1. Scans Python files for imports
2. Maps imports to PyPI packages
3. Detects deprecated patterns
4. Infers Python version timeline
5. Finds compatible package versions
6. Generates `requirements.txt`
7. Optionally creates the environment

---

## Configuration Commands

### `envio config`

Manage Envio configuration.

```bash
# Show current configuration
envio config show

# Set API key (auto-detects provider: openai, anthropic, together, etc.)
envio config api sk-your-key

# Set specific model
envio config model gpt-4o-mini
envio config model llama3
envio config model claude-3-opus-20240229

# Set Serper API key (for web search enhancement)
envio config serper-api your-serper-key

# Set default environments directory
envio config set default_envs_dir ~/my-envs

# Set preferred package manager
envio config set preferred_package_manager uv

# Clear API key
envio config unset api

# Clear model
envio config unset model

# View help for config options
envio config --help
```

---

## Common Options

These options work across multiple commands:

| Option | Description |
|--------|-------------|
| `-n, --name` | Environment name |
| `-p, --path` | Explicit path to environment |
| `-e, --env-type` | Package manager (pip, uv, conda) |
| `-v, --verbose` | Enable verbose output |
| `-y, --yes` | Skip confirmation prompts |
| `--dry-run` | Show what would happen without executing |

---

## Environment Specification

Commands that need an environment accept it in multiple ways:

### Priority Order

1. **Explicit path**: `-p /path/to/env`
2. **Name**: `-n my-env` (checks registry, then default location)
3. **Interactive picker**: No flag provided (shows list)

### How Environment Detection Works

```bash
# 1. Explicit path (highest priority)
envio audit -p /path/to/env

# 2. Name (checks registry, then ~/Documents/envs/)
envio audit -n my-env

# 3. Interactive (shows picker if no -n or -p)
envio audit
# Output:
#   [1] Current dir: .venv
#   [2] my-env: /path/to/env
#   [3] another-env: /path/to/another
#   Select environment number:
```

---

## Environment Variables

Envio respects these environment variables:

```bash
# Quiet mode - suppress all output (for CI/CD)
export ENVIO_QUIET=1

# Or set CI mode (automatically enables quiet)
export CI=true

# Disable colors (follows NO_COLOR standard)
export NO_COLOR=1
```

---

## Troubleshooting

### Reset Configuration

```bash
# Clear all config
envio config unset api
envio config unset model
rm ~/.envio/config.json
```

### Check Environment

```bash
# Full diagnostic
envio doctor -v
envio list -v
```

### Debug Issues

```bash
# Run with verbose output
envio install numpy -v

# Check what packages would be installed
envio install numpy --dry-run
```

---

## Getting Help

- View all commands: `envio --help`
- View command help: `envio <command> --help`
- Report issues: https://github.com/Gangadhar24377/envio/issues
- View full documentation: https://github.com/Gangadhar24377/envio
