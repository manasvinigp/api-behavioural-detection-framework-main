"""
Chaos testing and differential testing for API resilience.

Injects faults (latency, failures, timeouts) and compares API behavior
across versions or environments.
"""

from .interceptor import ChaosInterceptor
from .differential import DifferentialTester

__all__ = ["ChaosInterceptor", "DifferentialTester"]
