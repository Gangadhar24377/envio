# Envio

<p align="center">
[![PyPI Version](https://img.shields.io/pypi/v/envio)](https://pypi.org/project/envio/)
[![Python Versions](https://img.shields.io/pypi/pyversions/envio)](https://pypi.org/project/envio/)
[![License](https://img.shields.io/pypi/l/envio)](LICENSE)
[![Downloads](https://img.shields.io/pypi/dm/envio)](https://pypi.org/project/envio/)
</p>

> AI-Powered Python Environment Manager that understands what you want, not just what you type.
Ever spent hours fixing dependency conflicts? Wish you could just tell your computer "I need a web app with Flask" and have everything just work? That's Envio.

## Why You'll Love Envio
| Problem | Envio's Solution |
|---------|------------------|
| "What package provides `import cv2`?" | Auto-detects common imports (`cv2` -> `opencv-python`) |
| Dependency conflicts | AI resolves them automatically (3 attempts) |
| Wrong package names | Self-healing finds the correct one |
| GPU vs CPU packages | Hardware-aware installation |
| Security vulnerabilities | Built-in `envio audit` |

## Installation

```bash
pip install envio
```

That's it. You're ready to go.

## Quick Demo

```
# Tell Envio what you want
$ envio prompt "data science environment with pandas and sklearn"
# It figures out:
# -> pandas, numpy, scikit-learn, scipy, joblib...
# -> Full dependency tree with versions
# -> Optimized for your GPU if you have one
# -> Creates the environment ready to use
```

## Commands at a Glance

| Command | What it does |
|---------|-------------|
| `envio prompt "flask api"` | Create env from natural language |
| `envio init .` | Create env from requirements.txt |
| `envio install numpy pandas` | Install packages directly |
| `envio list` | See all your environments |
| `envio activate my-env` | Get activation command |
| `envio audit` | Check for security vulnerabilities |
| `envio lock` | Generate reproducible lockfile |

## Configuration

```bash
# One-time setup
envio config api sk-your-openai-key
# Optional: Set your model
envio config model gpt-4o-mini
# Optional: Serper for web search enhancement
envio config serper-api your-key
```

## Features That Make Life Easier

### Natural Language Environment Creation

```bash
envio prompt "machine learning with pytorch and transformers"
```

Just describe what you need. Envio understands domains (AI Agents, Web Dev, Data Science, etc.) and picks the right packages.

### Self-Healing

When things go wrong, Envio doesn't just fail - it tries to fix itself:
- Wrong package name? -> Finds the correct one
- Version conflict? -> Suggests compatible versions
- Package not found? -> Searches for alternatives

### Hardware-Aware

Envio detects your GPU (NVIDIA, Apple Silicon, etc.) and installs the right packages:
- `torch` + CUDA for NVIDIA
- `torch` + Metal for Apple Silicon
- `torch-cpu` for CPU-only

### Security Built-In

```bash
envio audit -n my-env
```

Scans for known vulnerabilities in your dependencies.

### Multiple Export Formats

```bash
envio export -n my-env --format dockerfile
envio export -n my-env --format devcontainer
envio export -n my-env --format requirements
```

## Supported Tools

- **Package Managers**: pip, uv (default), conda
- **LLM Providers**: OpenAI, Anthropic, Together AI, Ollama (local)
- **Platforms**: Windows, Linux, macOS

## Environment Variables

```bash
# Quiet mode (great for CI/CD)
export ENVIO_QUIET=1
# No colors
export NO_COLOR=1
```

## Documentation

- [Command Reference](COMMANDS.md) - Every command explained
- [Contributing](CONTRIBUTING.md) - Want to contribute?
- [Security](SECURITY.md) - Vulnerability reporting

## License

MIT - use it however you want.
---
<p align="center">
Made with alot of caffiene by <a href="https://github.com/Gangadhar24377">Gangadhar Kambhamettu</a>
</p>