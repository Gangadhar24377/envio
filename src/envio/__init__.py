"""Envio - AI-Native Environment Orchestrator."""

try:
    from importlib.metadata import version

    __version__ = version("envio")
except Exception:
    __version__ = "0.0.0"  # fallback for development
