"""Pre-commit hook and CI/CD template generator for supply chain security."""

from __future__ import annotations

from pathlib import Path

PRE_COMMIT_HOOK = """- repo: local
  hooks:
    - id: envio-supply-chain
      name: envio supply chain scan
      entry: envio supply-chain scan
      language: system
      pass_filenames: false
      always_run: true
      description: Scan environment for supply chain risks before committing
"""

GITHUB_ACTIONS_TEMPLATE = """name: Supply Chain Security

on:
  push:
    branches: [ {branch} ]
  pull_request:
    branches: [ {branch} ]
  schedule:
    - cron: '0 6 * * 1'  # Weekly on Monday at 6am UTC

jobs:
  supply-chain:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '{python_version}'

      - name: Install envio
        run: pip install envio-ai

      - name: Install project dependencies
        run: pip install -r {requirements_file}

      - name: Run supply chain scan
        run: envio supply-chain scan --all

      - name: Run supply chain scan (deep)
        run: envio supply-chain scan --deep --all
"""

GITLAB_CI_TEMPLATE = """supply-chain-scan:
  image: python:{python_version}
  script:
    - pip install envio-ai
    - pip install -r {requirements_file}
    - envio supply-chain scan --all
    - envio supply-chain scan --deep --all
  rules:
    - if: $CI_PIPELINE_SOURCE == "schedule"
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"
    - if: $CI_COMMIT_BRANCH == "{branch}"
"""


def install_pre_commit_hook(console) -> None:
    """Install pre-commit hook for supply chain scanning."""
    hook_file = Path(".pre-commit-hooks.yaml")
    if not hook_file.exists():
        config_file = Path(".pre-commit-config.yaml")
        if config_file.exists():
            content = config_file.read_text()
            if "envio-supply-chain" in content:
                console.print_info("Pre-commit hook already installed")
                return
            content += "\n" + PRE_COMMIT_HOOK
            config_file.write_text(content)
            console.print_success("Added supply chain hook to .pre-commit-config.yaml")
        else:
            config_file.write_text("repos:\n" + PRE_COMMIT_HOOK)
            console.print_success(
                "Created .pre-commit-config.yaml with supply chain hook"
            )
    else:
        console.print_warning(".pre-commit-hooks.yaml already exists")
        console.print_info("Add this to your .pre-commit-config.yaml:")
        console.print_info(PRE_COMMIT_HOOK)


def remove_pre_commit_hook(console) -> None:
    """Remove pre-commit hook for supply chain scanning."""
    config_file = Path(".pre-commit-config.yaml")
    if not config_file.exists():
        console.print_warning("No .pre-commit-config.yaml found")
        return

    content = config_file.read_text()
    if "envio-supply-chain" not in content:
        console.print_info("Supply chain hook not found")
        return

    lines = content.split("\n")
    new_lines = []
    skip = False
    for line in lines:
        if "envio-supply-chain" in line:
            skip = True
            continue
        if skip and line.startswith("  "):
            continue
        skip = False
        new_lines.append(line)

    config_file.write_text("\n".join(new_lines))
    console.print_success("Removed supply chain hook from .pre-commit-config.yaml")


def generate_ci_template(platform: str, console) -> None:
    """Generate CI/CD template for supply chain scanning."""
    import sys

    branch = "main"
    python_version = f"{sys.version_info.major}.{sys.version_info.minor}"
    requirements_file = "requirements.txt"

    if Path("pyproject.toml").exists():
        requirements_file = ". (project root)"

    if platform == "github":
        template = GITHUB_ACTIONS_TEMPLATE.format(
            branch=branch,
            python_version=python_version,
            requirements_file=requirements_file,
        )
        output_path = Path(".github/workflows/supply-chain.yml")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(template)
        console.print_success(f"Created {output_path}")
    elif platform == "gitlab":
        template = GITLAB_CI_TEMPLATE.format(
            branch=branch,
            python_version=python_version,
            requirements_file=requirements_file,
        )
        output_path = Path(".gitlab-ci-supply-chain.yml")
        output_path.write_text(template)
        console.print_success(f"Created {output_path}")
    else:
        console.print_error(f"Unknown platform: {platform}")
        console.print_info("Supported platforms: github, gitlab")
