"""
Smart test selection based on git diff and historical failure rates.

Uses Bayesian inference to prioritize high-risk tests for faster CI/CD execution.
"""

from .selector import SmartTestSelector

__all__ = ["SmartTestSelector"]
