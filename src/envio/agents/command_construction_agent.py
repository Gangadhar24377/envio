"""Command generator for package installation."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

from envio.llm.client import LLMClient, LLMConfig
from envio.llm.parser import ResponseParser
from envio.llm.prompts import COMMAND_SYSTEM_PROMPT, COMMAND_USER_PROMPT

if TYPE_CHECKING:
    from envio.core.system_profiler import SystemProfile


class CommandGenerator:
    """Generator for package installation commands."""

    def __init__(self, config: LLMConfig | None = None) -> None:
        self._llm = LLMClient(config)
        self._parser = ResponseParser()

    def generate(
        self,
        packages: list[str],
        env_type: str = "pip",
        hardware_profile: SystemProfile | None = None,
        preferences: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Generate installation commands.

        Args:
            packages: List of packages to install
            env_type: Environment type (pip/conda/uv)
            hardware_profile: Optional hardware profile for ML optimization
            preferences: Optional user preferences (cpu_only, gpu_optimized, etc.)

        Returns:
            Dictionary with commands, environment_type, warnings
        """
        hw_context = self._build_hardware_context(hardware_profile, preferences)

        # Build preferences string for prompt
        pref_str = ""
        if preferences:
            if preferences.get("cpu_only"):
                pref_str = (
                    "CPU-only mode enabled - do not add CUDA packages or index URLs"
                )
            elif preferences.get("gpu_optimized"):
                pref_str = "GPU-optimized mode enabled - include CUDA support"
            else:
                pref_str = "No specific preference - use defaults"

        prompt = COMMAND_USER_PROMPT.format(
            packages=json.dumps(packages, indent=2),
            env_type=env_type,
            hardware_context=hw_context,
            preferences=pref_str,
        )

        try:
            response = self._llm.chat_json(
                system_prompt=COMMAND_SYSTEM_PROMPT,
                user_prompt=prompt,
            )

            return {
                "commands": response.get("commands", []),
                "environment_type": env_type,
                "warnings": response.get("warnings", []),
            }
        except Exception:
            fallback_commands = [f"{env_type} install {' '.join(packages)}"]
            return {
                "commands": fallback_commands,
                "environment_type": env_type,
                "warnings": ["AI generation failed, using fallback"],
            }

    def _build_hardware_context(
        self, profile: SystemProfile | None, preferences: dict[str, Any] | None = None
    ) -> str:
        """Build hardware context string."""
        if not profile:
            return ""

        lines = ["Hardware Profile:"]
        lines.append(f"- OS: {profile.os_type.value}")
        lines.append(f"- Python: {profile.python_version}")

        cpu_only = preferences.get("cpu_only", False) if preferences else False

        if profile.gpu.available and not cpu_only:
            lines.append(f"- GPU: {profile.gpu.name}")
            if profile.gpu.vram_mb:
                lines.append(f"- VRAM: {profile.gpu.vram_mb} MB")
            if profile.gpu.cuda_version:
                lines.append(f"- CUDA: {profile.gpu.cuda_version}")
            if profile.ml_config.pytorch_index_url:
                lines.append(f"- PyTorch Index: {profile.ml_config.pytorch_index_url}")
        elif profile.gpu.available and cpu_only:
            lines.append(
                f"- GPU: {profile.gpu.name} (detected but CPU-only mode requested)"
            )
            lines.append("- CPU-only mode: Do not add CUDA packages")
        else:
            lines.append("- GPU: None (CPU-only)")

        return "\n".join(lines)
