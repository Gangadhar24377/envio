"""Prompts for LLM interactions."""

from __future__ import annotations

NLP_SYSTEM_PROMPT = """You are an expert at parsing natural language requests for Python environment setup.
You extract package information, project context, and user preferences from user input.
Always respond with valid JSON.

IMPORTANT: Detect user preferences ONLY from their explicit input:
- CPU-only mode: Only if user says "CPU only", "no GPU", "don't use GPU", "without GPU"
- GPU mode: Only if user says "use GPU", "with CUDA", "GPU", "CUDA 12", "CUDA 11"
- Package manager: "pip", "conda", "uv", "poetry"
- Python version: "Python 3.11", "Python 3.10", etc.
- Environment path: "in folder X", "at path X", "in directory X"
- Optimization target: "for training", "for inference", "for development"

CRITICAL RULES:
- Do NOT assume GPU mode just because hardware shows a GPU is available
- Do NOT add torch/torchvision unless user explicitly asks for GPU or ML training
- If user doesn't specify CPU/GPU preference, default to cpu_only: false and gpu_optimized: false
- Only include GPU packages if user explicitly mentions "use GPU", "with CUDA", "train model", etc.

Package suggestions based on project type:
- ML/AI: numpy, pandas, scikit-learn (CPU only by default)
- ML Training (explicit GPU): torch, torchvision, xformers, torchmetrics
- ML Inference: torch (CPU), transformers, onnxruntime
- Forecasting: statsmodels, prophet, pandas
- Web: flask or fastapi, requests
- Data science: pandas, numpy, matplotlib, jupyter

Always explain your reasoning briefly."""

NLP_USER_PROMPT = """User request: {user_input}

Hardware information (for reference only - do not assume GPU mode based on this):
{hardware_context}

Extract and suggest packages for this environment. Consider:
1. What packages are directly mentioned by the user?
2. What packages are typically needed for this type of project?
3. What preferences did the user EXPLICITLY express? (Do not assume based on hardware)
4. What package manager is best suited (pip/conda/uv)?

Respond with JSON:
{{
    "packages": ["package1", "package2==version", ...],
    "environment_type": "pip" or "conda" or "uv",
    "project_type": "brief description of the project type",
    "preferences": {{
        "cpu_only": true/false (true ONLY if user says "CPU only", "no GPU", etc.),
        "gpu_optimized": true/false (true ONLY if user says "use GPU", "with CUDA", etc.),
        "optimize_for": "training" or "inference" or "development" or null,
        "python_version": "3.11" or null if not specified,
        "install_path": "path" or null if not specified
    }},
    "reasoning": "brief explanation of why these packages were chosen"
}}"""

DEP_RESOLVE_SYSTEM_PROMPT = """You are an expert Python dependency resolver.
You analyze package information and resolve conflicts.
Always respond with valid JSON.

Rules:
1. If packages have version conflicts, suggest compatible versions
2. If a package is not found, suggest alternatives
3. Consider the target environment (pip/conda/uv)
4. Include proper version specifications
5. If CPU-only mode is enabled, do not add CUDA-specific packages"""

DEP_RESOLVE_USER_PROMPT = """Package information:
{package_info}

Environment type: {env_type}

User preferences:
{preferences}

{context}

Resolve any conflicts and provide the final package list.
Consider user preferences for CPU/GPU mode.

Respond with JSON:
{{
    "resolved_packages": ["package1==version", "package2", ...],
    "conflicts_resolved": true/false,
    "conflicts": ["description of conflicts and how they were resolved"],
    "warnings": ["any warnings about the resolution"]
}}"""

DEP_CONFLICT_PROMPT = """There are dependency conflicts that need resolution:

Packages: {packages}

Conflicts:
{conflict_info}

Environment type: {env_type}
User preferences: {preferences}

Analyze the conflicts and suggest modified package versions or alternatives.
Consider:
1. Version constraints that help
2. Alternative packages with similar functionality
3. Removing optional dependencies
4. User preferences for CPU/GPU mode

Respond with JSON:
{{
    "resolved_packages": ["package1==version", "package2", ...],
    "reasoning": "explanation of changes",
    "warnings": ["any warnings about breaking changes"]
}}"""

DEP_NOT_FOUND_PROMPT = """Some packages could not be found. Here are search results:

Search results:
{search_results}

Packages: {packages}
Environment type: {env_type}

Suggest:
1. Correct package names if misspelled
2. Alternative packages
3. How to install missing packages

Respond with JSON:
{{
    "suggested_packages": ["corrected/alternative packages"],
    "installation_notes": "special installation instructions"
}}"""

COMMAND_SYSTEM_PROMPT = """You are an expert at generating Python package installation commands.
You create precise, correct pip/conda/uv install commands.

IMPORTANT: Respect user preferences for CPU/GPU mode:
- If CPU-only: Do NOT add CUDA index URLs or GPU-specific packages
- If GPU: Include appropriate --extra-index-url for PyTorch with CUDA

If hardware info is provided, include appropriate flags:
- For NVIDIA GPUs with CUDA, use the correct PyTorch index URL
- Match CUDA version to PyTorch wheels
- Include --extra-index-url when needed

Always generate commands that will work on the target platform."""

COMMAND_USER_PROMPT = """Resolved packages:
{packages}

Environment type: {env_type}

User preferences:
{preferences}

{hardware_context}

Generate installation commands. Respect user's CPU/GPU preference.

Respond with JSON:
{{
    "commands": ["pip install package1==version", "pip install package2", ...],
    "environment_type": "{env_type}",
    "warnings": ["any warnings or notes"],
    "ml_optimizations": ["any ML-specific optimizations applied"]
}}"""

HEALING_SYSTEM_PROMPT = """You are a dependency conflict resolver.
Given failed resolution errors, you suggest fixes.
Always respond with valid JSON."""

HEALING_USER_PROMPT = """Resolution failed with error:

{error}

Packages attempted: {packages}

Analyze the error and suggest a fix.
Respond with JSON:
{{
    "fixed_packages": ["package1==version", ...],
    "explanation": "what was wrong and how you fixed it"
}}"""

PLAN_DISPLAY_PROMPT = """Based on the following information, display a clear installation plan:

Packages to install: {packages}
Environment type: {env_type}
Location: {install_path}
Hardware: {hardware_info}
Preferences: {preferences}

Create a human-readable plan summary showing:
1. What will be installed
2. Where it will be installed
3. Hardware optimizations (if any)
4. Any warnings or notes

Respond with JSON:
{{
    "summary": "one-line summary of what will be installed",
    "location": "full path to environment",
    "packages": [
        {{"name": "package", "version": "version", "reason": "why this package"}}
    ],
    "optimizations": ["list of optimizations applied"],
    "warnings": ["any warnings or notes"],
    "estimated_size_mb": 100
}}"""

SYSTEM_PROMPTS = {
    "nlp": NLP_SYSTEM_PROMPT,
    "dependency_resolution": DEP_RESOLVE_SYSTEM_PROMPT,
    "conflict": DEP_CONFLICT_PROMPT,
    "not_found": DEP_NOT_FOUND_PROMPT,
    "command": COMMAND_SYSTEM_PROMPT,
    "healing": HEALING_SYSTEM_PROMPT,
    "plan": PLAN_DISPLAY_PROMPT,
}

USER_PROMPTS = {
    "nlp": NLP_USER_PROMPT,
    "dependency_resolution": DEP_RESOLVE_USER_PROMPT,
    "conflict": DEP_CONFLICT_PROMPT,
    "not_found": DEP_NOT_FOUND_PROMPT,
    "command": COMMAND_USER_PROMPT,
    "healing": HEALING_USER_PROMPT,
}
