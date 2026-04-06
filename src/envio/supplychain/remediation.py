"""Suggest safe alternatives when packages are flagged."""

from __future__ import annotations

from envio.supplychain.scanner import PackageRisk


def suggest_alternative(risk: PackageRisk) -> str | None:
    """Suggest a safe alternative for a flagged package.

    Returns the suggested package name, or None if no alternative found.
    """
    typo_info = risk.details.get("typo", {})
    if typo_info.get("is_typo") and typo_info.get("suggested"):
        return typo_info["suggested"]

    for suggestion in risk.suggestions:
        if "Did you mean" in suggestion:
            import re

            match = re.search(r"'([^']+)'", suggestion)
            if match:
                return match.group(1)

    return None


def get_install_warning(risk: PackageRisk) -> str | None:
    """Generate a warning message for a flagged package during install.

    Returns warning text, or None if package is clean.
    """
    if risk.risk_score < 20:
        return None

    lines = []
    lines.append(f"Supply chain warning for '{risk.package}':")

    for flag in risk.flags:
        lines.append(f"  - {flag}")

    alternative = suggest_alternative(risk)
    if alternative:
        lines.append(f"  Suggested: install '{alternative}' instead")

    if risk.risk_score >= 70:
        lines.append(f"  Risk level: HIGH (score: {risk.risk_score}/100)")
    elif risk.risk_score >= 40:
        lines.append(f"  Risk level: MEDIUM (score: {risk.risk_score}/100)")
    else:
        lines.append(f"  Risk level: LOW (score: {risk.risk_score}/100)")

    return "\n".join(lines)
