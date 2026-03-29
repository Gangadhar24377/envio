"""Tests for SyntaxDetector."""

import pytest
from pathlib import Path

from envio.analysis.syntax_detector import SyntaxDetector, DeprecatedPattern


class TestSyntaxDetector:
    """Tests for SyntaxDetector."""

    def test_detect_patterns_f_string(self):
        """Test detecting f-strings."""
        detector = SyntaxDetector()
        code = 'name = "world"\nprint(f"Hello {name}")'
        patterns = detector.detect_patterns(code)
        assert any(p.name == "f_string" for p in patterns)

    def test_detect_patterns_print_statement(self):
        """Test detecting Python 2 print statement."""
        detector = SyntaxDetector()
        code = 'print "Hello"'  # Python 2 syntax
        patterns = detector.detect_patterns(code)
        assert any(p.name == "print_statement" for p in patterns)

    def test_detect_patterns_empty(self):
        """Test detecting patterns in empty code."""
        detector = SyntaxDetector()
        code = ""
        patterns = detector.detect_patterns(code)
        assert len(patterns) == 0

    def test_detect_from_file(self, tmp_path):
        """Test detecting patterns from a file."""
        detector = SyntaxDetector()
        test_file = tmp_path / "test.py"
        test_file.write_text('print(f"Hello")')
        patterns = detector.detect_from_file(test_file)
        assert any(p.name == "f_string" for p in patterns)

    def test_detect_from_directory(self, tmp_path):
        """Test detecting patterns from a directory."""
        detector = SyntaxDetector()
        test_file = tmp_path / "test.py"
        test_file.write_text('print(f"Hello")')
        results = detector.detect_from_directory(tmp_path)
        assert str(test_file) in results

    def test_infer_timeline_modern(self):
        """Test inferring timeline for modern code."""
        detector = SyntaxDetector()
        patterns = [
            DeprecatedPattern(
                name="f_string",
                line=1,
                code_snippet='f"Hello"',
                era="python3",
                timeline="2016+",
                weight=10,
            )
        ]
        timeline = detector.infer_timeline(patterns)
        assert "modern" in timeline

    def test_infer_timeline_python2(self):
        """Test inferring timeline for Python 2 code."""
        detector = SyntaxDetector()
        patterns = [
            DeprecatedPattern(
                name="print_statement",
                line=1,
                code_snippet='print "Hello"',
                era="python2",
                timeline="2008-2015",
                weight=10,
            )
        ]
        timeline = detector.infer_timeline(patterns)
        assert "2008" in timeline

    def test_infer_python_version_modern(self):
        """Test inferring Python version for modern code."""
        import sys

        detector = SyntaxDetector()
        patterns = [
            DeprecatedPattern(
                name="f_string",
                line=1,
                code_snippet='f"Hello"',
                era="python3",
                timeline="2016+",
                weight=10,
            )
        ]
        version, warning = detector.infer_python_version(patterns)
        expected = f"{sys.version_info.major}.{sys.version_info.minor}"
        assert version == expected

    def test_infer_python_version_empty(self):
        """Test inferring Python version for empty patterns."""
        import sys

        detector = SyntaxDetector()
        version, warning = detector.infer_python_version([])
        expected = f"{sys.version_info.major}.{sys.version_info.minor}"
        assert version == expected
