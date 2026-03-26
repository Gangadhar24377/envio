"""Tests for SelfHealingLoop."""

import pytest
from unittest.mock import patch, MagicMock

from envio.resolution.self_healing import SelfHealingLoop, HealingResult
from envio.resolution.fast_resolver import ResolutionResult, ResolutionStatus


class TestSelfHealingLoop:
    """Tests for SelfHealingLoop."""

    def test_heal_success(self):
        """Test successful healing."""
        loop = SelfHealingLoop()

        # Create a mock FastResolver class that returns our mock instance
        mock_resolver = MagicMock()
        mock_resolver.resolve.return_value = ResolutionResult(
            status=ResolutionStatus.SUCCESS, packages=["numpy", "pandas"]
        )

        mock_fast_resolver_class = MagicMock(return_value=mock_resolver)

        # Patch at the location where it's imported (inside the heal method)
        with patch.dict(
            "sys.modules",
            {
                "envio.resolution.fast_resolver": MagicMock(
                    FastResolver=mock_fast_resolver_class
                )
            },
        ):
            # Also need to patch _analyze_and_fix to return a modified list
            with patch.object(
                loop, "_analyze_and_fix", return_value=["numpy==1.24.0", "pandas"]
            ):
                result = loop.heal(
                    packages=["numpy", "pandas"],
                    error_message="conflict",
                    resolution=ResolutionResult(
                        status=ResolutionStatus.CONFLICT, packages=["numpy", "pandas"]
                    ),
                )
                assert result.success is True

    def test_heal_failure_max_attempts(self):
        """Test healing failure due to max attempts."""
        loop = SelfHealingLoop()

        # Create a mock FastResolver class that returns our mock instance
        mock_resolver = MagicMock()
        mock_resolver.resolve.return_value = ResolutionResult(
            status=ResolutionStatus.ERROR,
            packages=["numpy", "pandas"],
            error_message="still failing",
        )

        mock_fast_resolver_class = MagicMock(return_value=mock_resolver)

        with patch.dict(
            "sys.modules",
            {
                "envio.resolution.fast_resolver": MagicMock(
                    FastResolver=mock_fast_resolver_class
                )
            },
        ):
            # Patch _analyze_and_fix to return unchanged packages
            with patch.object(
                loop, "_analyze_and_fix", return_value=["numpy", "pandas"]
            ):
                result = loop.heal(
                    packages=["numpy", "pandas"],
                    error_message="conflict",
                    resolution=ResolutionResult(
                        status=ResolutionStatus.CONFLICT, packages=["numpy", "pandas"]
                    ),
                )
                assert result.success is False
                assert result.final_error is not None
                assert (
                    "Could not find compatible package versions" in result.final_error
                )

    def test_error_hash_duplicate(self):
        """Test error hashing for duplicate detection."""
        loop = SelfHealingLoop()
        error1 = "Package numpy conflicts with pandas"
        error2 = "Package numpy conflicts with pandas"
        error3 = "Different error message"

        hash1 = loop._error_hash(error1)
        hash2 = loop._error_hash(error2)
        hash3 = loop._error_hash(error3)

        assert hash1 == hash2
        assert hash1 != hash3

    def test_relax_version_constraints(self):
        """Test relaxing version constraints."""
        loop = SelfHealingLoop()
        packages = ["numpy==1.24.0", "pandas>=2.0.0", "scikit-learn"]
        result = loop._relax_version_constraints(packages, "")

        assert "numpy" in result
        assert "pandas" in result
        assert "scikit-learn" in result
        assert "numpy==" not in str(result)

    def test_find_alternative_packages(self):
        """Test finding alternative packages."""
        loop = SelfHealingLoop()
        packages = ["requests", "tensorflow", "numpy"]
        result = loop._find_alternative_packages(packages, "")

        assert "httpx" in result  # Alternative for requests
        assert "torch" in result  # Alternative for tensorflow
        assert "numpy" in result  # No alternative, keep original

    def test_skip_optional_dependencies(self):
        """Test skipping optional dependencies."""
        loop = SelfHealingLoop()
        packages = ["numpy", "pandas[all]", "scikit-learn"]
        result = loop._skip_optional_dependencies(packages, "")

        assert "numpy" in result
        assert "scikit-learn" in result
        # pandas[all] should be skipped because it has extras
        assert "pandas[all]" not in result

    def test_error_hash_normalization(self):
        """Test that error hash normalizes whitespace and versions."""
        loop = SelfHealingLoop()
        error1 = "Package  numpy==1.24.0  conflicts"
        error2 = "Package numpy conflicts"
        hash1 = loop._error_hash(error1)
        hash2 = loop._error_hash(error2)
        assert hash1 == hash2

    def test_get_next_strategy(self):
        """Test getting next fallback strategy."""
        loop = SelfHealingLoop()
        assert loop._current_strategy_index == 0
        strategy1 = loop._get_next_strategy()
        assert strategy1 == "relax_version_constraints"
        assert loop._current_strategy_index == 1
        strategy2 = loop._get_next_strategy()
        assert strategy2 == "find_alternative_packages"
        assert loop._current_strategy_index == 2
        strategy3 = loop._get_next_strategy()
        assert strategy3 == "skip_optional_dependencies"
        assert loop._current_strategy_index == 3
        # After all strategies, should return "default"
        strategy4 = loop._get_next_strategy()
        assert strategy4 == "default"

    def test_healing_attempt_records(self):
        """Test that healing attempts are recorded."""
        loop = SelfHealingLoop()

        # Create a mock FastResolver class that returns our mock instance
        mock_resolver = MagicMock()
        mock_resolver.resolve.return_value = ResolutionResult(
            status=ResolutionStatus.SUCCESS, packages=["numpy", "pandas"]
        )

        mock_fast_resolver_class = MagicMock(return_value=mock_resolver)

        with patch.dict(
            "sys.modules",
            {
                "envio.resolution.fast_resolver": MagicMock(
                    FastResolver=mock_fast_resolver_class
                )
            },
        ):
            with patch.object(
                loop, "_analyze_and_fix", return_value=["numpy==1.24.0", "pandas"]
            ):
                result = loop.heal(
                    packages=["numpy", "pandas"],
                    error_message="conflict",
                    resolution=ResolutionResult(
                        status=ResolutionStatus.CONFLICT, packages=["numpy", "pandas"]
                    ),
                )
                assert len(result.attempts) == 1
                assert result.attempts[0].attempt_number == 1

    def test_heal_with_no_modification(self):
        """Test healing when _analyze_and_fix returns unchanged packages."""
        loop = SelfHealingLoop()

        # Patch _analyze_and_fix to return unchanged packages
        with patch.object(loop, "_analyze_and_fix", return_value=["numpy", "pandas"]):
            result = loop.heal(
                packages=["numpy", "pandas"],
                error_message="conflict",
                resolution=ResolutionResult(
                    status=ResolutionStatus.CONFLICT, packages=["numpy", "pandas"]
                ),
            )
            assert result.success is False
            assert len(result.attempts) > 0
