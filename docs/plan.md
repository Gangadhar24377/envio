# Envio: The AI-Native Environment Orchestrator

Envio is not just another Python package manager. It is an AI-native orchestrator designed to solve the most painful aspects of local development: dependency conflicts, hardware-specific ML setups, and legacy code resurrection. 

By combining the lightning-fast deterministic resolution of `uv` with the reasoning capabilities of an AI agent, Envio provides a "Self-Healing" workflow. When standard resolution fails, Envio analyzes the stack trace, rewrites the requirements, and fixes the conflict automatically.

---

## Phase 1: The Open-Source MVP (V1 Launch)
*The critical path to making Envio public, stable, and uniquely valuable.*

### 1. Core Infrastructure & Cleanup (P0)
Before adding features, the 2-year-old technical debt must be cleared to make the project approachable for open-source contributors.
* **Dependency Purge:** Remove unused heavyweights (`tensorflow`, `chromadb`, `lancedb`, `neo4j`). Reduce dependencies from ~262 down to the core ~40.
* **Packaging:** Implement `pyproject.toml` with a proper CLI entry point (`envio`).
* **Version Control Hygiene:** Add proper `.gitignore` (ignoring `.env` and `venv`), `.env.example`, and an MIT `LICENSE`.
* **Code Quality:** Set up `ruff` (linting), `black` (formatting), and `mypy` (type checking).

### 2. OS-Agnostic Execution Engine (P0)
Envio must work flawlessly across Windows, Linux, and macOS without relying on hardcoded bash scripts or Unix-only tools like `tmux`.
* **`pathlib` Migration:** Replace all `os.path` and raw string paths with `pathlib.Path` to natively handle Windows `\` and Unix `/` separators.
* **System Profiler (`system_profiler.py`):** * Detect OS (`platform.system()`).
  * Detect local hardware (NVIDIA GPU presence via `nvidia-smi`, VRAM capacity, and Python version).
* **Cross-Platform Executor (`executor.py`):** Abstract shell execution using Python's `subprocess.run()`, dynamically executing commands based on the detected OS (e.g., PowerShell for Windows, Bash for Linux).

### 3. The Hybrid "Self-Healing" Resolver (P1)
The core differentiator of Envio. 
* **The Fast Path (`uv` Integration):** Envio first attempts to resolve and install dependencies using `uv` for millisecond performance.
* **The AI Fallback (Self-Healing Loop):** If `uv` fails due to a version conflict:
  1. The error `stderr` is caught and passed to the AI Agent.
  2. The Agent searches PyPI/web for compatibility matrices.
  3. The Agent rewrites the requirements and retries the installation (max 3 loops).

### 4. Hardware-Aware ML Setup (P1)
Targeting the Machine Learning niche by automating the worst part of local AI development.
* **NVIDIA/CUDA Focus:** Envio detects the local dGPU and automatically injects the correct `--extra-index-url` for PyTorch to match the system's CUDA toolkit.
* **Memory Constraints:** If setting up an environment for training heavy models (like custom tokenizers or transformers), Envio factors in system RAM and VRAM to suggest appropriate memory-efficient libraries (like `xformers` or `flash-attn` where applicable).

### 5. Rich Terminal UI (P1)
Masking the LLM latency with a beautiful, transparent user experience.
* **Streaming Status:** Implement the `Rich` library to show dynamic spinners and live updates of the Agent's "thought process" (e.g., *"⚠️ Conflict detected in xformers... 🔍 Agent analyzing PyTorch compatibility matrix..."*).

---

## Phase 2: The "Reproducibility" Engine (Growth)
*Features to expand the user base and lock them into the Envio ecosystem.*

### 1. "Ghost-Town" Repo Resurrection
* **Concept:** Point Envio at a 3-year-old unmaintained AI research repo with a broken `requirements.txt`.
* **Action:** The AI scans the `.py` files, extracts imports, infers the timeline based on deprecated syntax, and generates a historically accurate, locked environment that actually runs today.

### 2. "Jailbroken" Local LLM Execution
* **Concept:** Remove the reliance on paid OpenAI/Anthropic APIs.
* **Action:** Integrate local LLM support (via Ollama or `llama.cpp`) using highly quantized, task-specific models tuned strictly for package resolution. 

### 3. AI-Optimized Containerization
* **Concept:** Smarter Dockerfiles.
* **Action:** Envio generates highly optimized, multi-stage Dockerfiles that separate OS dependencies from Python dependencies, selecting the slimmest possible base images based on required C-bindings.

### 4. Semantic Environment Diffing
* **Concept:** Human-readable changelogs for environments.
* **Action:** Instead of showing standard version bumps, Envio explains the impact: *"Updated `pydantic` to V2. Warning: This introduces breaking changes. Flagged 3 files requiring syntax updates."*

---

## Phase 3: Team & Enterprise Workflows (Maturity)
*Features designed for organizational adoption and CI/CD pipelines.*

### 1. The Envio GitHub Action (CI Guardian)
* A bot that analyzes Pull Requests modifying dependencies. It tests the resolution, calculates a "bloat score," and suggests lighter or safer alternatives before the code is merged.

### 2. Security & CVE Profiling
* Before finalizing an environment, Envio cross-references selected packages against vulnerability databases and blocks/warns on critical CVEs, suggesting patched versions.

### 3. Dependency Cost Estimation
* Estimates the compute costs of running the requested environment on cloud providers based on the necessary hardware (e.g., AWS EC2 instances required for the specific CUDA/PyTorch matrix).

---

## Future / Blue-Sky Features
* **Multi-Language Support:** Expanding the AI resolver to handle `npm/yarn` for Node.js or `cargo` for Rust.
* **Web UI / Visual Builder:** A FastAPI + React dashboard to visually drag-and-drop packages and share environment URLs.
* **VS Code / Cursor Extension:** Right-click context menus to let the agent auto-resolve the environment directly within the IDE.