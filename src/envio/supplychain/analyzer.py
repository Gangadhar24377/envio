"""LLM-powered diff analysis for supply chain security."""

from __future__ import annotations

from dataclasses import dataclass, field

SYSTEM_PROMPT = """You are a security analyst reviewing changes between two versions of a Python package published on PyPI. Your job is to detect supply chain attacks, backdoors, and malicious code.

Analyze the diff report for these threat categories:

1. OBFUSCATION: Base64-encoded payloads, eval/exec usage, dynamic imports, string concatenation to hide function names
2. NETWORK CALLS: New HTTP requests, socket connections, DNS queries, data exfiltration patterns
3. PERSISTENCE: Cron jobs, startup scripts, systemd services, registry modifications
4. CREDENTIAL ACCESS: Reading .env files, SSH keys, AWS credentials, browser data, password managers
5. SYSTEM MODIFICATION: PATH manipulation, alias injection, environment variable changes
6. PACKAGE MANIPULATION: setup.py hooks, .pth files, import hooks, monkey patching
7. TYPOSQUATTING: Package name mimicking popular packages, suspicious naming patterns
8. DEPENDENCY INJECTION: Adding new dependencies that could be malicious

For each category found, provide:
- The specific files and lines that trigger it
- Why it's suspicious
- Severity (critical, high, medium, low)

Respond with a JSON object in this exact format:
{
  "verdict": "safe" | "suspicious" | "malicious",
  "risk_score": 0-100,
  "categories_found": ["OBFUSCATION", "NETWORK_CALLS", ...],
  "findings": [
    {
      "category": "NETWORK_CALLS",
      "file": "path/to/file.py",
      "description": "What was found and why it's suspicious",
      "severity": "critical|high|medium|low"
    }
  ],
  "summary": "Brief explanation of the overall assessment"
}

If the diff only contains normal changes (bug fixes, features, documentation, tests), mark it as "safe" with a low risk score.
If the diff contains suspicious patterns but could be legitimate, mark it as "suspicious" with explanation.
If the diff clearly contains malicious code, mark it as "malicious" with high risk score."""


@dataclass
class AnalysisFinding:
    category: str
    file: str
    description: str
    severity: str


@dataclass
class DiffAnalysis:
    package: str
    old_version: str
    new_version: str
    verdict: str  # "safe", "suspicious", "malicious"
    risk_score: int
    categories_found: list[str] = field(default_factory=list)
    findings: list[AnalysisFinding] = field(default_factory=list)
    summary: str = ""
    error: str | None = None


def analyze_diff(
    package: str,
    old_version: str,
    new_version: str,
    diff_report: str,
) -> DiffAnalysis:
    """Analyze a package diff using the configured LLM.

    Uses whatever LLM provider the user has configured via envio config.
    """
    try:
        from envio.llm.client import LLMClient

        client = LLMClient()
    except Exception as exc:
        return DiffAnalysis(
            package=package,
            old_version=old_version,
            new_version=new_version,
            verdict="unknown",
            risk_score=0,
            error=f"LLM not configured: {exc}",
        )

    user_prompt = f"""Review the following diff report between {package} {old_version} and {new_version}:

{diff_report}

Provide your security assessment in the required JSON format."""

    try:
        response = client.chat_json(
            system_prompt=SYSTEM_PROMPT,
            user_prompt=user_prompt,
        )

        verdict = response.get("verdict", "unknown")
        risk_score = int(response.get("risk_score", 0))
        summary = response.get("summary", "")
        categories = response.get("categories_found", [])
        raw_findings = response.get("findings", [])

        findings = []
        for f in raw_findings:
            findings.append(
                AnalysisFinding(
                    category=f.get("category", "UNKNOWN"),
                    file=f.get("file", "unknown"),
                    description=f.get("description", ""),
                    severity=f.get("severity", "unknown"),
                )
            )

        return DiffAnalysis(
            package=package,
            old_version=old_version,
            new_version=new_version,
            verdict=verdict,
            risk_score=min(risk_score, 100),
            categories_found=categories,
            findings=findings,
            summary=summary,
        )

    except Exception as exc:
        return DiffAnalysis(
            package=package,
            old_version=old_version,
            new_version=new_version,
            verdict="unknown",
            risk_score=0,
            error=f"LLM analysis failed: {exc}",
        )
