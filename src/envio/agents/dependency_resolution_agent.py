"""Dependency resolver with hybrid fast-path and AI fallback."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from envio.llm.client import LLMClient, LLMConfig
from envio.llm.parser import ResponseParser
from envio.llm.prompts import (
    DEP_CONFLICT_PROMPT,
    DEP_NOT_FOUND_PROMPT,
    DEP_RESOLVE_SYSTEM_PROMPT,
)
from envio.resolution.fast_resolver import (
    FastResolver,
    ResolutionResult,
    ResolutionStatus,
)

if TYPE_CHECKING:
    from envio.core.system_profiler import SystemProfile


class DependencyResolver:
    """Dependency resolver with hybrid fast-path and AI fallback."""

    def __init__(self, config: LLMConfig | None = None) -> None:
        self._llm = LLMClient(config)
        self._parser = ResponseParser()
        self._fast_resolver = FastResolver()

    def resolve(
        self,
        packages: list[str],
        env_type: str = "pip",
        hardware_profile: SystemProfile | None = None,
        preferences: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Resolve dependencies using hybrid approach.

        Args:
            packages: List of packages to resolve
            env_type: Environment type (pip/conda/uv)
            hardware_profile: Optional hardware profile for ML optimization
            preferences: Optional user preferences (cpu_only, gpu_optimized, etc.)

        Returns:
            Dictionary with resolved packages and metadata
        """
        # Respect user preference for CPU-only mode
        cpu_only = preferences.get("cpu_only", False) if preferences else False

        if hardware_profile and hardware_profile.gpu.available and not cpu_only:
            packages = self._optimize_for_hardware(packages, hardware_profile)

        fast_result = self._fast_resolver.resolve(packages)

        if fast_result.is_success():
            return {
                "status": "success",
                "packages": packages,
                "resolution_method": "fast_path",
            }

        if fast_result.has_conflicts():
            return self._handle_conflict(packages, fast_result, env_type, preferences)

        if fast_result.status == ResolutionStatus.NOT_FOUND:
            return self._handle_not_found(packages, fast_result, env_type)

        return self._handle_error(packages, fast_result, env_type)

    def _optimize_for_hardware(
        self, packages: list[str], profile: SystemProfile
    ) -> list[str]:
        """Optimize packages for detected hardware."""
        gpu = profile.gpu
        if not gpu.available:
            return packages

        cuda_url = self._get_cuda_index_url(gpu.cuda_version)

        optimized = []
        for pkg in packages:
            if "torch" in pkg.lower():
                optimized.append(pkg)
                if cuda_url:
                    optimized.append(f"--extra-index-url {cuda_url}")
            elif "xformers" in pkg.lower() and gpu.cuda_version:
                cuda_short = "124" if "12.4" in gpu.cuda_version else "118"
                optimized.append(f"xformers cu{cuda_short}xx")
            else:
                optimized.append(pkg)

        return optimized

    def _get_cuda_index_url(self, cuda_version: str | None) -> str | None:
        """Get PyTorch index URL for CUDA version."""
        if not cuda_version:
            return None
        if "12.4" in cuda_version:
            return "https://download.pytorch.org/whl/cu124"
        if "12.1" in cuda_version:
            return "https://download.pytorch.org/whl/cu121"
        if "11.8" in cuda_version:
            return "https://download.pytorch.org/whl/cu118"
        return "https://download.pytorch.org/whl/cu121"

    def _handle_conflict(
        self,
        packages: list[str],
        result: ResolutionResult,
        env_type: str,
        preferences: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Handle dependency conflict with AI."""
        conflict_info = "\n".join(
            f"- {c.package1} conflicts with {c.package2}: {c.reason}"
            for c in result.conflicts
        )

        pref_str = ""
        if preferences:
            if preferences.get("cpu_only"):
                pref_str = "CPU-only mode enabled - do not add CUDA packages"
            elif preferences.get("gpu_optimized"):
                pref_str = "GPU-optimized mode enabled"

        prompt = DEP_CONFLICT_PROMPT.format(
            packages=packages,
            conflict_info=conflict_info,
            env_type=env_type,
            preferences=pref_str,
        )

        try:
            response = self._llm.chat_json(
                system_prompt=DEP_RESOLVE_SYSTEM_PROMPT,
                user_prompt=prompt,
            )

            resolved_packages = self._parser.parse_packages(response)
            warnings = self._parser.parse_warnings(response)

            return {
                "status": "resolved",
                "packages": resolved_packages if resolved_packages else packages,
                "reasoning": response.get("reasoning", ""),
                "warnings": warnings,
                "resolution_method": "ai_healed",
            }
        except Exception:
            return {
                "status": "partial",
                "packages": packages,
                "resolution_method": "ai_fallback",
            }

    def _handle_not_found(
        self, packages: list[str], result: ResolutionResult, env_type: str
    ) -> dict[str, Any]:
        """Handle package not found with web search."""
        search_results = {}
        for pkg in packages:
            search_results[pkg] = self._search_web(pkg)

        prompt = DEP_NOT_FOUND_PROMPT.format(
            search_results=search_results,
            packages=packages,
            env_type=env_type,
        )

        try:
            response = self._llm.chat_json(
                system_prompt=DEP_RESOLVE_SYSTEM_PROMPT,
                user_prompt=prompt,
            )

            suggested_packages = self._parser.parse_packages(response)
            return {
                "status": "resolved",
                "packages": suggested_packages if suggested_packages else packages,
                "notes": response.get("installation_notes", ""),
                "resolution_method": "ai_search",
            }
        except Exception:
            return {
                "status": "partial",
                "packages": packages,
                "resolution_method": "ai_fallback",
            }

    def _handle_error(
        self, packages: list[str], result: ResolutionResult, env_type: str
    ) -> dict[str, Any]:
        """Handle generic error."""
        return {
            "status": "error",
            "packages": packages,
            "error": result.error_message or "Resolution failed",
            "resolution_method": "failed",
        }

    def _search_web(self, query: str) -> str:
        """Search web for package information."""
        import os

        import requests

        api_key = os.getenv("SERPER_API_KEY")
        if not api_key:
            return "Search not available (no API key)"

        try:
            response = requests.post(
                "https://google.serper.dev/search",
                headers={"X-API-KEY": api_key, "Content-Type": "application/json"},
                json={"q": f"{query} python package"},
                timeout=10,
            )
            if response.status_code == 200:
                data = response.json()
                results = data.get("organic", [])
                if results:
                    first = results[0]
                    return f"{first.get('title', '')}: {first.get('snippet', '')}"
            return "No results found"
        except Exception:
            return "Search failed"
