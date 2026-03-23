"""Console UI for Envio - simplified for compatibility."""

from __future__ import annotations

from collections.abc import Generator
from contextlib import contextmanager

from rich.console import Console


class ConsoleUI:
    """Console UI for Envio with fallback to plain text."""

    def __init__(self, verbose: bool = True) -> None:
        self._verbose = verbose
        try:
            self._console = Console(stderr=True)
        except Exception:
            self._console = None
        self._use_rich = True

    def _print(self, message: str) -> None:
        """Print with fallback to plain print."""
        if self._console and self._use_rich:
            try:
                self._console.print(message)
            except Exception:
                self._use_rich = False
                print(message)
        else:
            print(message)

    def print_header(self, title: str) -> None:
        """Print a header panel."""
        print(f"\n=== {title} ===\n")

    def print_success(self, message: str) -> None:
        """Print a success message."""
        self._print(f"[+] {message}")

    def print_error(self, message: str) -> None:
        """Print an error message."""
        self._print(f"[-] ERROR: {message}")

    def print_warning(self, message: str) -> None:
        """Print a warning message."""
        self._print(f"[!] {message}")

    def print_info(self, message: str) -> None:
        """Print an info message."""
        self._print(f"[*] {message}")

    def print_agent_thought(self, agent: str, thought: str) -> None:
        """Print an agent's thought process."""
        if self._verbose:
            print(f"  [{agent}] {thought}")

    def print_system_profile(self, profile: dict) -> None:
        """Print system profile."""
        print("\n--- System Profile ---")
        for key, value in profile.items():
            if value is not None and value is not False:
                print(f"  {key.replace('_', ' ').title()}: {value}")
        print("")

    def print_packages(self, packages: list[str], title: str = "Packages") -> None:
        """Print packages in a list."""
        if packages:
            print(f"\n{title}:")
            for pkg in packages:
                print(f"  - {pkg}")
            print("")

    def print_conflicts(self, conflicts: list[dict]) -> None:
        """Print conflict information."""
        if conflicts:
            print("\n--- Detected Conflicts ---")
            for conflict in conflicts:
                print(
                    f"  {conflict.get('package1', 'unknown')} vs {conflict.get('package2', 'unknown')}: {conflict.get('reason', 'conflict')}"
                )
            print("")

    def print_code_block(self, code: str, language: str = "bash") -> None:
        """Print code in a block."""
        print(f"\n--- {language.upper()} ---")
        print(code)
        print("---\n")

    @contextmanager
    def status(self, message: str) -> Generator:
        """Context manager for showing status - simplified."""
        print(f"[{message}]...")
        try:
            yield None
        except Exception as e:
            print(f"Status error: {e}")
            yield None

    @contextmanager
    def progress(self) -> Generator:
        """Context manager for showing progress bars - simplified."""
        yield None

    def print_resolution_result(
        self, status: str, packages: list[str], method: str
    ) -> None:
        """Print resolution result."""
        if status == "success":
            self.print_success(f"Resolution successful via {method}")
        elif status == "resolved":
            self.print_warning(f"Conflicts resolved via {method}")
        elif status == "partial":
            self.print_warning(f"Partial resolution via {method}")
        else:
            self.print_error(f"Resolution failed: {method}")
        self.print_packages(packages)

    def print_step(self, step: int, total: int, description: str) -> None:
        """Print a step indicator."""
        print(f"\n--- Step {step}/{total}: {description} ---")


class StatusContext:
    """Simplified status context."""

    def __init__(self, console: ConsoleUI, status_text: str) -> None:
        self._console = console
        self._status_text = status_text

    def __enter__(self) -> StatusContext:
        print(f"[{self._status_text}]...")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        pass

    def update(self, message: str) -> None:
        """Update the status message."""
        print(f"  {message}")
