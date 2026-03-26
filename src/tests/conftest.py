"""Shared test fixtures."""

import pytest


@pytest.fixture
def sample_packages():
    """Return a list of sample packages for testing."""
    return ["numpy", "pandas", "scikit-learn"]


@pytest.fixture
def sample_response():
    """Return a sample LLM response for testing."""
    return {
        "packages": ["numpy>=1.24.0", "pandas>=2.0.0"],
        "reasoning": "These are the recommended versions.",
        "warnings": [],
    }
