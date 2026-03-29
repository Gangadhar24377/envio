# Envio Command Reference

Comprehensive guide to all Envio CLI commands with examples.

## Installation & Setup

### Basic Setup

```bash
# Install envio from PyPI
pip install envio

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

# With custom name and path
envio prompt "data science environment" -n my-data-env -p ~/envs

# With GPU optimization
envio prompt "machine learning with pytorch" --optimize-for training

# CPU-only mode
envio prompt "data analysis with pandas" --cpu-only

# Dry run - see what would be installed without installing
envio prompt "flask api" --dry-run

# Specify package manager
envio prompt "fastapi app" --manager uv

# Skip confirmation prompt
envio prompt "simple script" -y
```

### `envio init`

Initialize environment from existing project files (requirements.txt, etc.).

```bash
# Auto-detect requirements files in current directory
envio init .

# From specific directory
envio init /path/to/project

# Choose location (1=here, 2=default, 3=custom)
# Creates environment in selected location
envio init .

# With specific name
envio init . -n my-environment

# Specify package manager
envio init . --manager conda

# Skip confirmation
envio init . -y
```

### `envio install`

Install packages directly to an environment.

```bash
# Install to default location (~/Documents/envs)
envio install requests

# Install to existing environment by name
envio install numpy pandas -n my-env

# With explicit path
envio install flask -p /path/to/env

# Install with specific versions
envio install "numpy>=1.24" "pandas>=2.0"

# Using different package manager
envio install flask --manager pip

# Dry run
envio install flask --dry-run

# Skip confirmation
envio install flask -y
```

---

## Environment Management

### `envio list`

List all environments created by Envio.

```bash
# List all environments
envio list

# Verbose output with details
envio list -v
```

Shows:
- Environment name
- Path to environment
- Number of packages
- Package manager used
- Creation date
- Recreation commands

### `envio activate`

Show activation commands for an environment.

```bash
# By name (checks registry, then default location)
envio activate my-env

# With explicit path
envio activate -p /path/to/env

# Shows commands for PowerShell, CMD, and Git Bash
```

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

### `envio audit`

Scan environment for known security vulnerabilities.

```bash
# Audit default environment
envio audit

# Audit specific environment by name
envio audit -n my-env

# Audit with explicit path
envio audit -p /path/to/env

# Skip security fixes suggestions
envio audit -n my-env --skip-fix
```

---

## Export & Lock

### `envio export`

Export environment configuration to various formats.

```bash
# By name (checks registry first, then default location)
envio export -n my-env --format requirements

# With explicit path (for non-envio environments)
envio export -p /path/to/env --format requirements

# Export to requirements.txt
envio export -n my-env --format requirements

# Export to Dockerfile
envio export -n my-env --format dockerfile

# Export to devcontainer.json (VS Code)
envio export -n my-env --format devcontainer

# Export to docker-compose.yml
envio export -n my-env --format docker-compose

# Export to conda environment.yml
envio export -n my-env --format conda

# Custom output file
envio export -n my-env -o my-requirements.txt
```

### `envio lock`

Generate a lockfile for reproducible environments.

```bash
# By name (checks registry first, then default location)
envio lock -n my-env

# With explicit path (for non-envio environments)
envio lock -p /path/to/env

# Custom filename
envio lock -n my-env -o requirements.lock

# Using specific package manager
envio lock -n my-env --manager uv

# JSON format (default)
envio lock -n my-env --format json

# Text format
envio lock -n my-env --format text
```

---

## Advanced Features

### `envio resurrect`

Analyze dead/unmaintained repositories and generate requirements.

```bash
# From local directory
envio resurrect /path/to/old-repo

# From GitHub URL
envio resurrect https://github.com/user/old-repo

# With environment creation
envio resurrect https://github.com/user/old-repo -n revived-env

# Using conda
envio resurrect /path/to/repo --env-type conda

# With explicit path
envio resurrect . -p /path/to/save/requirements.txt
```

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

# Clear API key (switches to Ollama mode)
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
| `-v, --verbose` | Enable verbose output |
| `-y, --yes` | Skip confirmation prompts |
| `--dry-run` | Show what would happen without executing |
| `--manager` | Package manager (pip, uv, conda) |

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

# Note: API keys are now stored in config file via:
#   envio config api <key>
#   envio config serper-api <key>
# Environment variables are no longer used for API keys.
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
