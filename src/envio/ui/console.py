"""Rich Console UI for Envio - Beautiful terminal output."""

from __future__ import annotations

import time
from collections.abc import Generator
from contextlib import contextmanager
from datetime import datetime
from typing import Any

from rich.console import Console
from rich.panel import Panel
from rich.progress import (
    BarColumn,
    MofNCompleteColumn,
    Progress,
    SpinnerColumn,
    TaskProgressColumn,
    TextColumn,
    TimeElapsedColumn,
)
from rich.table import Table
from rich.text import Text


def _timestamp() -> str:
    """Get formatted timestamp."""
    return datetime.now().strftime("%H:%M:%S")


class ConsoleUI:
    """Beautiful Rich console for Envio."""

    def __init__(self, verbose: bool = True, log_file: str | None = None) -> None:
        self._verbose = verbose
        self._start_time = time.time()
        try:
            self._console = Console(stderr=True)
            self._use_rich = True
        except Exception:
            self._console = None
            self._use_rich = False

    def _safe_print(self, message: Any, **kwargs) -> None:
        """Print with fallback - accepts Rich objects or strings."""
        if self._console and self._use_rich:
            try:
                self._console.print(message, **kwargs)
            except Exception:
                print(str(message))
        else:
            print(str(message))

    def _print_with_time(self, message: str, style: str = "") -> None:
        """Print message with timestamp prefix."""
        ts = _timestamp()
        if self._use_rich:
            if style:
                self._safe_print(f"[dim]{ts}[/dim] {style}{message}")
            else:
                self._safe_print(f"[dim]{ts}[/dim] {message}")
        else:
            print(f"[{ts}] {message}")

    def print_header(self, title: str, subtitle: str | None = None) -> None:
        """Print a beautiful header panel."""
        ts = _timestamp()
        if self._use_rich:
            panel = Panel(
                Text(title, style="bold cyan", justify="center"),
                subtitle=subtitle,
                border_style="cyan",
                padding=(1, 2),
            )
            self._safe_print(panel)
        else:
            print(f"\n[{ts}] {'=' * 60}")
            print(f"  {title}")
            if subtitle:
                print(f"  {subtitle}")
            print(f"[{ts}] {'=' * 60}\n")

    def print_success(self, message: str) -> None:
        """Print success message with timestamp."""
        ts = _timestamp()
        if self._use_rich:
            self._safe_print(f"[dim]{ts}[/dim] [bold green][+][/bold green] {message}")
        else:
            print(f"[{ts}] [+] {message}")

    def print_error(self, message: str) -> None:
        """Print error message with timestamp."""
        ts = _timestamp()
        if self._use_rich:
            self._safe_print(f"[dim]{ts}[/dim] [bold red][-][/bold red] {message}")
        else:
            print(f"[{ts}] [-] {message}")

    def print_warning(self, message: str) -> None:
        """Print warning message with timestamp."""
        ts = _timestamp()
        if self._use_rich:
            self._safe_print(
                f"[dim]{ts}[/dim] [bold yellow][!][/bold yellow] {message}"
            )
        else:
            print(f"[{ts}] [!] {message}")

    def print_info(self, message: str) -> None:
        """Print info message with timestamp."""
        ts = _timestamp()
        if self._use_rich:
            self._safe_print(f"[dim]{ts}[/dim] [bold blue][*][/bold blue] {message}")
        else:
            print(f"[{ts}] [*] {message}")

    def print_agent_thought(self, agent: str, thought: str) -> None:
        """Print agent's thought process with animated indicator."""
        ts = _timestamp()
        if self._verbose and self._use_rich:
            self._safe_print(
                f"  [dim]{ts}[/dim]   [dim][bold]{agent}:[/bold] {thought}[/dim]"
            )
        elif self._verbose:
            print(f"  [{ts}] [{agent}] {thought}")

    def print_streaming_status(self, message: str, status: str = "processing") -> None:
        """Print streaming status with animated indicator."""
        ts = _timestamp()
        if status == "processing":
            icon = "[bold yellow]⠧[/bold yellow]"
        elif status == "success":
            icon = "[bold green]✔[/bold green]"
        elif status == "error":
            icon = "[bold red]✖[/bold red]"
        else:
            icon = "[bold blue]ℹ[/bold blue]"

        if self._use_rich:
            self._safe_print(f"  [dim]{ts}[/dim] {icon} {message}")
        else:
            print(f"  [{ts}] {message}")

    def print_hardware_profile(self, profile) -> None:
        """Print beautiful hardware profile with VRAM bar."""
        if not self._use_rich:
            self._print_system_profile_plain(profile)
            return

        table = Table(
            title="System Profile",
            show_header=True,
            header_style="bold magenta",
            border_style="cyan",
        )
        table.add_column("Component", style="cyan", width=15)
        table.add_column("Details", style="green")

        table.add_row("OS", profile.os_type.value.title())
        table.add_row("Release", profile.os_release)
        table.add_row("Architecture", profile.architecture)
        table.add_row("Python", profile.python_version)
        table.add_row("Shell", profile.shell_type.value.title())

        if profile.gpu.available:
            table.add_row("GPU", f"[green]{profile.gpu.name}[/green]")
            if profile.gpu.vram_mb:
                vram_gb = profile.gpu.vram_mb / 1024
                table.add_row("VRAM", f"{vram_gb:.1f} GB")
            if profile.gpu.cuda_version:
                table.add_row("CUDA", f"[yellow]{profile.gpu.cuda_version}[/yellow]")
            if profile.ml_config.pytorch_index_url:
                table.add_row(
                    "PyTorch Index",
                    f"[dim]{profile.ml_config.pytorch_index_url}[/dim]",
                )
            if profile.ml_config.recommended_batch_size:
                table.add_row(
                    "Recommended Batch",
                    str(profile.ml_config.recommended_batch_size),
                )
        else:
            table.add_row("GPU", "[dim]None (CPU-only)[/dim]")

        if profile.ram_gb:
            table.add_row("System RAM", f"{profile.ram_gb} GB")

        self._safe_print(table)

    def _create_vram_bar(self, vram_mb: int, max_vram: int = 24576) -> str:
        """Create a VRAM usage bar visualization."""
        vram_gb = vram_mb / 1024
        max_gb = max_vram / 1024
        ratio = min(vram_mb / max_vram, 1.0)
        bar_length = 20
        filled = int(ratio * bar_length)
        empty = bar_length - filled

        if ratio > 0.8:
            color = "red"
        elif ratio > 0.5:
            color = "yellow"
        else:
            color = "green"

        bar = f"[{color}]{'█' * filled}{'░' * empty}[/{color}]"
        return f"{bar} {vram_gb:.1f}/{max_gb:.0f} GB"

    def _print_system_profile_plain(self, profile) -> None:
        """Fallback plain text system profile."""
        ts = _timestamp()
        print(f"\n[{ts}] --- System Profile ---")
        print(f"  OS: {profile.os_type.value}")
        print(f"  Python: {profile.python_version}")
        if profile.gpu.available:
            print(f"  GPU: {profile.gpu.name}")
            if profile.gpu.vram_mb:
                print(f"  VRAM: {profile.gpu.vram_mb} MB")
            if profile.gpu.cuda_version:
                print(f"  CUDA: {profile.gpu.cuda_version}")
        print("")

    def print_packages_table(
        self,
        packages: list[str],
        title: str = "Packages",
        show_index: bool = True,
    ) -> None:
        """Print packages in a nice table."""
        if not packages:
            return

        ts = _timestamp()
        if not self._use_rich:
            print(f"\n[{ts}] {title}:")
            for pkg in packages:
                print(f"  - {pkg}")
            print("")
            return

        table = Table(
            title=f"[dim]{ts}[/dim] {title}",
            show_header=True,
            header_style="bold cyan",
            border_style="dim",
        )
        if show_index:
            table.add_column("#", style="dim", width=4, justify="right")
        table.add_column("Package", style="green")

        for i, pkg in enumerate(packages, 1):
            if show_index:
                table.add_row(str(i), pkg)
            else:
                table.add_row(pkg)

        self._safe_print(table)

    def print_installation_plan(
        self,
        env_name: str,
        env_path: str,
        package_manager: str,
        packages: list[str],
        preferences: dict | None,
        profile,
    ) -> None:
        """Print installation plan with beautiful formatting."""
        ts = _timestamp()
        if not self._use_rich:
            self._print_plan_plain(
                env_name, env_path, package_manager, packages, preferences, profile
            )
            return

        # Build plan content
        plan_parts = []
        plan_parts.append(f"[dim]{ts}[/dim]")
        plan_parts.append(f"[bold]Environment:[/bold] {env_name}")
        plan_parts.append(f"[bold]Location:[/bold] {env_path}")
        plan_parts.append(f"[bold]Package Manager:[/bold] {package_manager}")

        # Show preferences
        if preferences:
            pref_parts = []
            if preferences.get("cpu_only"):
                pref_parts.append("[yellow]CPU-only mode[/yellow]")
            elif preferences.get("gpu_optimized"):
                pref_parts.append("[green]GPU-optimized[/green]")
            if preferences.get("optimize_for"):
                pref_parts.append(f"[cyan]{preferences['optimize_for']}[/cyan]")
            if pref_parts:
                plan_parts.append(f"[bold]Mode:[/bold] {', '.join(pref_parts)}")

        # Show hardware info
        if profile.gpu.available:
            hw_info = f"[green]{profile.gpu.name}[/green]"
            if profile.gpu.vram_mb:
                hw_info += f" ({profile.gpu.vram_mb} MB VRAM)"
            if preferences and preferences.get("cpu_only"):
                hw_info += " [dim](GPU detected but CPU-only requested)[/dim]"
            plan_parts.append(f"[bold]Hardware:[/bold] {hw_info}")
        else:
            plan_parts.append(
                "[bold]Hardware:[/bold] [dim]CPU-only (no GPU detected)[/dim]"
            )

        # Show packages
        plan_parts.append(f"\n[bold]Packages ({len(packages)}):[/bold]")
        for pkg in packages:
            plan_parts.append(f"  - {pkg}")

        plan_text = "\n".join(plan_parts)

        panel = Panel(
            plan_text,
            title="[bold cyan]Installation Plan[/bold cyan]",
            border_style="cyan",
            padding=(1, 2),
        )
        self._safe_print(panel)

    def _print_plan_plain(
        self,
        env_name: str,
        env_path: str,
        package_manager: str,
        packages: list[str],
        preferences: dict | None,
        profile,
    ) -> None:
        """Fallback plain text plan."""
        ts = _timestamp()
        print(f"\n[{ts}] {'=' * 50}")
        print("  Installation Plan")
        print(f"[{ts}] {'=' * 50}\n")
        print(f"  Environment: {env_name}")
        print(f"  Location: {env_path}")
        print(f"  Package Manager: {package_manager}")
        if preferences:
            if preferences.get("cpu_only"):
                print("  Mode: CPU-only")
        if profile.gpu.available:
            print(f"  GPU: {profile.gpu.name}")
        print(f"\n  Packages ({len(packages)}):")
        for pkg in packages:
            print(f"    - {pkg}")
        print("")

    def print_conflicts_table(self, conflicts: list[dict]) -> None:
        """Print conflicts in a table."""
        if not conflicts:
            return

        ts = _timestamp()
        if not self._use_rich:
            print(f"\n[{ts}] --- Detected Conflicts ---")
            for c in conflicts:
                print(f"  {c.get('package1', '?')} vs {c.get('package2', '?')}")
            print("")
            return

        table = Table(
            title=f"[dim]{ts}[/dim] Detected Conflicts",
            show_header=True,
            header_style="bold red",
            border_style="red",
        )
        table.add_column("Package 1", style="red")
        table.add_column("Package 2", style="red")
        table.add_column("Reason", style="yellow")

        for c in conflicts:
            table.add_row(
                c.get("package1", "unknown"),
                c.get("package2", "unknown"),
                c.get("reason", "conflict"),
            )

        self._safe_print(table)

    def print_code_block(self, code: str, language: str = "bash") -> None:
        """Print code in a block with timestamp."""
        ts = _timestamp()
        if self._use_rich:
            from rich.syntax import Syntax

            syntax = Syntax(code, language, theme="monokai", line_numbers=False)
            panel = Panel(
                syntax,
                title=f"[bold]{language.upper()}[/bold]",
                border_style="dim",
            )
            self._safe_print(f"[dim]{ts}[/dim]")
            self._safe_print(panel)
        else:
            print(f"\n[{ts}] --- {language.upper()} ---")
            print(code)
            print(f"[{ts}] ---\n")

    @contextmanager
    def spinner(self, message: str) -> Generator:
        """Context manager for showing a spinner with message."""
        ts = _timestamp()
        if self._use_rich:
            with self._console.status(
                f"[dim]{ts}[/dim] [bold cyan]{message}[/bold cyan]"
            ) as status:
                yield status
        else:
            print(f"[{ts}] [{message}]...")
            yield None

    @contextmanager
    def status(self, message: str) -> Generator:
        """Context manager for showing status (compatibility)."""
        ts = _timestamp()
        if self._use_rich:
            with self._console.status(
                f"[dim]{ts}[/dim] [bold cyan]{message}[/bold cyan]"
            ) as status:
                yield status
        else:
            print(f"[{ts}] [{message}]...")
            yield None

    @contextmanager
    def streaming_status(self, message: str) -> Generator:
        """Context manager for streaming status with live updates."""
        ts = _timestamp()
        if self._use_rich:
            from rich.live import Live

            with Live(
                Text(f"[dim]{ts}[/dim] [bold yellow]⠧[/bold yellow] {message}"),
                console=self._console,
                refresh_per_second=4,
            ) as live:
                yield live
        else:
            print(f"[{ts}] [{message}]...")
            yield None

    @contextmanager
    def progress(
        self,
        description: str = "Processing",
        total: int | None = None,
    ) -> Generator:
        """Context manager for showing progress bar."""
        ts = _timestamp()
        if self._use_rich:
            progress = Progress(
                SpinnerColumn(),
                TextColumn(
                    f"[dim]{ts}[/dim] [progress.description]{{task.description}}"
                ),
                BarColumn(),
                TaskProgressColumn(),
                MofNCompleteColumn(),
                TimeElapsedColumn(),
                console=self._console,
            )
            with progress:
                progress.add_task(description, total=total)
                yield progress
        else:
            print(f"[{ts}] [{description}]...")
            yield None

    @contextmanager
    def installation_progress(
        self,
        packages: list[str],
    ) -> Generator:
        """Context manager for installation progress with per-package tracking."""
        ts = _timestamp()
        if self._use_rich:
            progress = Progress(
                TextColumn(f"[dim]{ts}[/dim]"),
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TaskProgressColumn(),
                TimeElapsedColumn(),
                console=self._console,
            )
            with progress:
                task_id = progress.add_task(
                    "Installing packages...", total=len(packages)
                )
                yield progress, task_id
        else:
            print(f"[{ts}] Installing {len(packages)} packages...")
            yield None, None

    def confirm(self, message: str, default: bool = True) -> bool:
        """Ask for confirmation."""
        ts = _timestamp()
        prompt = f"[{ts}] {message} ({'Y/n' if default else 'y/N'}): "
        while True:
            response = input(prompt).strip().lower()
            if not response:
                return default
            if response in ("y", "yes"):
                return True
            if response in ("n", "no"):
                return False
            print("Please enter y or n")

    def print_resolution_status(
        self,
        status: str,
        method: str,
        details: str | None = None,
    ) -> None:
        """Print resolution status with styling."""
        ts = _timestamp()
        if status == "success":
            icon = "[bold green][+][/bold green]"
            label = "Resolution successful"
        elif status == "conflict":
            icon = "[bold yellow][!][/bold yellow]"
            label = "Conflict detected"
        elif status == "error":
            icon = "[bold red][-][/bold red]"
            label = "Resolution failed"
        else:
            icon = "[bold blue][*][/bold blue]"
            label = status.capitalize()

        message = f"[dim]{ts}[/dim] {icon} {label} via {method}"
        if details:
            message += f": {details}"
        self._safe_print(message)

    def print_resolution_header(self, title: str) -> None:
        """Print a section header for resolution steps."""
        ts = _timestamp()
        if self._use_rich:
            self._safe_print(f"\n[dim]{ts}[/dim] [bold]{title}[/bold]")
        else:
            print(f"\n[{ts}] {title}")

    def print_step(self, step: int, total: int, description: str) -> None:
        """Print a step indicator."""
        ts = _timestamp()
        if self._use_rich:
            self._safe_print(
                f"[dim]{ts}[/dim] [bold cyan][{step}/{total}][/bold cyan] {description}"
            )
        else:
            print(f"[{ts}] [{step}/{total}] {description}")

    def print_healing_status(self, attempt: int, max_attempts: int, error: str) -> None:
        """Print self-healing status with streaming indicator."""
        ts = _timestamp()
        if self._use_rich:
            self._safe_print(
                f"\n[dim]{ts}[/dim] [bold yellow][!] Healing attempt {attempt}/{max_attempts}[/bold yellow]"
            )
            error_preview = error[:100] + "..." if len(error) > 100 else error
            self._safe_print(f"  [dim]Error: {error_preview}[/dim]")
        else:
            print(f"\n[{ts}] [!] Healing attempt {attempt}/{max_attempts}")
            error_preview = error[:100] + "..." if len(error) > 100 else error
            print(f"  Error: {error_preview}")

    def print_healing_solution(self, solution: str) -> None:
        """Print AI's suggested solution."""
        ts = _timestamp()
        if self._use_rich:
            self._safe_print(
                f"  [dim]{ts}[/dim] [bold green]Solution found:[/bold green] {solution}"
            )
        else:
            print(f"  [{ts}] [+] Solution found: {solution}")
