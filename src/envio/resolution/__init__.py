"""Resolution module for dependency resolution."""

from envio.resolution.fast_resolver import FastResolver, ResolutionResult
from envio.resolution.self_healing import SelfHealingLoop

__all__ = ["FastResolver", "ResolutionResult", "SelfHealingLoop"]
