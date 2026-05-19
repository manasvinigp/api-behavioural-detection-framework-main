"""
Progressive drift detection using time-series analysis.

Tracks API behavior over time to detect gradual degradation and predict
future drift using change point detection and forecasting.
"""

from .tracker import ProgressiveDriftTracker

__all__ = ["ProgressiveDriftTracker"]
