"""Syntax detector for inferring codebase age."""

from __future__ import annotations

import os
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from envio.analysis.import_analyzer import SKIP_INDICATORS


@dataclass
class DeprecatedPattern:
    """A detected pattern (deprecated or modern)."""

    name: str
    line: int
    code_snippet: str
    era: str
    timeline: str
    weight: int = 1


class SyntaxDetector:
    """Detector for syntax patterns to infer codebase age."""

    # Strong Python 2 signals (weight 10)
    PYTHON2_PATTERNS = {
        "print_statement": {
            "regex": r"^\s*print\s+[^(]",
            "era": "python2",
            "timeline": "2008-2015",
            "weight": 10,
            "description": "Python 2 print statement (no parentheses)",
        },
        "urllib2": {
            "regex": r"import\s+urllib2|from\s+urllib2",
            "era": "python2",
            "timeline": "2008-2015",
            "weight": 10,
            "description": "Python 2 urllib2 module",
        },
        "raw_input": {
            "regex": r"raw_input\s*\(",
            "era": "python2",
            "timeline": "2008-2015",
            "weight": 10,
            "description": "Python 2 raw_input() function",
        },
        "xrange": {
            "regex": r"xrange\s*\(",
            "era": "python2",
            "timeline": "2008-2015",
            "weight": 10,
            "description": "Python 2 xrange() function",
        },
        "python2_division": {
            "regex": r"from\s+__future__\s+import\s+division",
            "era": "python2",
            "timeline": "2008-2015",
            "weight": 10,
            "description": "Python 2 future division import",
        },
        "python2_unicode": {
            "regex": r"from\s+__future__\s+import\s+unicode_literals",
            "era": "python2",
            "timeline": "2008-2015",
            "weight": 10,
            "description": "Python 2 unicode_literals import",
        },
    }

    # Weak old-style patterns (weight 1) - still valid in Python 3
    OLD_STYLE_PATTERNS = {
        "old_string_format": {
            "regex": r'"[^"]*%[sd][^"]*"',
            "era": "python3",
            "timeline": "2000-2020",
            "weight": 1,
            "description": "Old-style % string formatting (still valid)",
        },
        "old_django_urlresolvers": {
            "regex": r"from\s+django\.core\.urlresolvers",
            "era": "django_old",
            "timeline": "2013-2016",
            "weight": 5,
            "description": "Django <1.10 urlresolvers import",
        },
        "old_flask_script": {
            "regex": r"from\s+flask\.ext\.script",
            "era": "flask_old",
            "timeline": "2013-2017",
            "weight": 5,
            "description": "Old Flask-Script extension",
        },
        "six_compatibility": {
            "regex": r"import\s+six|from\s+six",
            "era": "python2_3_compat",
            "timeline": "2010-2020",
            "weight": 3,
            "description": "Python 2/3 compatibility layer (six)",
        },
    }

    # Modern Python patterns (weight 10) - strong modern signals
    MODERN_PATTERNS = {
        "f_string": {
            "regex": r'f["\']',
            "era": "python3",
            "timeline": "2016+",
            "weight": 10,
            "description": "f-string (Python 3.6+)",
        },
        "walrus_operator": {
            "regex": r":=",
            "era": "python3",
            "timeline": "2019+",
            "weight": 10,
            "description": "Walrus operator (Python 3.8+)",
        },
        "match_statement": {
            "regex": r"match\s+\w+:",
            "era": "python3",
            "timeline": "2021+",
            "weight": 10,
            "description": "Match statement (Python 3.10+)",
        },
        "type_union": {
            "regex": r"(\w+)\s*\|\s*(\w+)",
            "era": "python3",
            "timeline": "2021+",
            "weight": 5,
            "description": "Type union with | (Python 3.10+)",
        },
        "typing_optional": {
            "regex": r"Optional\[",
            "era": "python3",
            "timeline": "2016+",
            "weight": 3,
            "description": "Optional type hint (Python 3.5+)",
        },
    }

    def detect_patterns(self, code: str) -> list[DeprecatedPattern]:
        """Detect patterns in code (deprecated and modern).

        Args:
            code: Python source code

        Returns:
            List of detected patterns
        """
        patterns: list[DeprecatedPattern] = []
        lines = code.split("\n")

        # Check all pattern sets
        all_patterns = {
            **self.PYTHON2_PATTERNS,
            **self.OLD_STYLE_PATTERNS,
            **self.MODERN_PATTERNS,
        }

        for line_num, line in enumerate(lines, 1):
            for pattern_name, pattern_info in all_patterns.items():
                if re.search(pattern_info["regex"], line):
                    patterns.append(
                        DeprecatedPattern(
                            name=pattern_name,
                            line=line_num,
                            code_snippet=line.strip(),
                            era=pattern_info["era"],
                            timeline=pattern_info["timeline"],
                            weight=pattern_info.get("weight", 1),
                        )
                    )

        return patterns

    def detect_from_file(self, file_path: Path) -> list[DeprecatedPattern]:
        """Detect patterns in a file.

        Args:
            file_path: Path to Python file

        Returns:
            List of detected patterns
        """
        try:
            with open(file_path, encoding="utf-8", errors="ignore") as f:
                code = f.read()
            return self.detect_patterns(code)
        except Exception:
            return []

    def should_scan(self, file_path: Path) -> bool:
        """Check if file should be scanned for patterns.

        Uses SKIP_INDICATORS from import_analyzer for consistency.

        Args:
            file_path: Path to check

        Returns:
            True if file should be scanned
        """
        from envio.analysis.import_analyzer import SKIP_INDICATORS

        if set(file_path.parts).intersection(SKIP_INDICATORS):
            return False

        if any(part.startswith(".") for part in file_path.parts):
            if ".github" not in file_path.parts:
                return False

        return True

    def detect_from_directory(
        self, directory: Path
    ) -> dict[str, list[DeprecatedPattern]]:
        """Detect patterns in all Python files in a directory.

        Uses parallel processing with progress bar.

        Args:
            directory: Path to directory

        Returns:
            Dictionary mapping file paths to patterns
        """
        results: dict[str, list[DeprecatedPattern]] = {}

        all_files = list(directory.glob("**/*.py"))
        py_files = [f for f in all_files if self.should_scan(f)]

        if not py_files:
            return results

        max_workers = min(32, (os.cpu_count() or 1) + 4)

        try:
            from tqdm import tqdm

            use_progress = True
        except ImportError:
            use_progress = False

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {executor.submit(self.detect_from_file, f): f for f in py_files}

            if use_progress:
                for future in tqdm(
                    as_completed(futures),
                    total=len(py_files),
                    desc="Analyzing code patterns",
                    unit="file",
                ):
                    py_file = futures[future]
                    try:
                        patterns = future.result()
                        if patterns:
                            results[str(py_file)] = patterns
                    except Exception:
                        continue
            else:
                for future in as_completed(futures):
                    py_file = futures[future]
                    try:
                        patterns = future.result()
                        if patterns:
                            results[str(py_file)] = patterns
                    except Exception:
                        continue

        return results

    def infer_timeline(self, patterns: list[DeprecatedPattern]) -> str:
        """Infer approximate timeline using weighted scoring.

        Modern patterns have higher weight than old-style patterns.
        Only strong Python 2 signals (weight 10) override modern signals.

        Args:
            patterns: List of detected patterns

        Returns:
            Most likely timeline string
        """
        if not patterns:
            return "modern (2020+)"

        # Calculate weighted scores
        python2_score = 0
        modern_score = 0

        for pattern in patterns:
            if pattern.era == "python2":
                python2_score += pattern.weight
            elif pattern.era == "python3" and "2016" in pattern.timeline:
                modern_score += pattern.weight
            elif pattern.era == "python3" and "2019" in pattern.timeline:
                modern_score += pattern.weight
            elif pattern.era == "python3" and "2021" in pattern.timeline:
                modern_score += pattern.weight

        # If modern score is higher or equal, assume modern
        if modern_score >= python2_score:
            if modern_score >= 10:
                return "modern (2021+)"
            elif modern_score >= 5:
                return "modern (2019+)"
            else:
                return "modern (2016+)"

        # Otherwise use Python 2 timeline
        return "2008-2015"

    def infer_python_version(self, patterns: list[DeprecatedPattern]) -> str:
        """Infer Python version using weighted scoring.

        Args:
            patterns: List of detected patterns

        Returns:
            Recommended Python version
        """
        if not patterns:
            return "3.11"

        # Calculate scores
        python2_score = sum(p.weight for p in patterns if p.era == "python2")
        modern_score = sum(p.weight for p in patterns if p.era == "python3")

        # If modern patterns exist, use modern Python
        if modern_score >= python2_score:
            return "3.11"

        # Only use Python 2 if there are strong signals
        return "2.7"
