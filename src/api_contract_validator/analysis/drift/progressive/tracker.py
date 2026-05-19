"""Progressive drift tracking with time-series analysis."""

from datetime import datetime, timezone, timedelta
from typing import List, Dict, Optional, Tuple
from pathlib import Path
import json
import numpy as np


class ProgressiveDriftTracker:
    """Track drift metrics over time and detect progressive degradation."""

    def __init__(self, storage_path: str = "./.acv/drift_history.jsonl"):
        self.storage_path = Path(storage_path)
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)

    def record_snapshot(self, snapshot: Dict) -> None:
        """Record drift snapshot with timestamp."""
        snapshot['timestamp'] = datetime.now(timezone.utc).isoformat()
        with open(self.storage_path, 'a') as f:
            f.write(json.dumps(snapshot) + '\n')

    def get_snapshots(self, days: int = 7) -> List[Dict]:
        """Get all snapshots from the last N days."""
        if not self.storage_path.exists():
            return []

        cutoff_time = datetime.now(timezone.utc) - timedelta(days=days)
        snapshots = []

        with open(self.storage_path, 'r') as f:
            for line in f:
                if line.strip():
                    snapshot = json.loads(line)
                    snapshot_time = datetime.fromisoformat(snapshot['timestamp'])
                    if snapshot_time >= cutoff_time:
                        snapshots.append(snapshot)

        return snapshots

    def get_trend(self, metric: str, days: int = 7) -> List[float]:
        """
        Get metric trend over time.

        Args:
            metric: Metric name (e.g., "contract_drift_score", "response_time")
            days: Number of days to look back

        Returns:
            List of metric values over time (chronological order)
        """
        snapshots = self.get_snapshots(days)

        trend = []
        for snapshot in snapshots:
            # Handle nested metric paths (e.g., "drift.contract")
            value = snapshot
            for key in metric.split('.'):
                value = value.get(key)
                if value is None:
                    break

            if value is not None:
                trend.append(float(value))

        return trend

    def detect_change_point(
        self,
        metric: str,
        days: int = 7,
        min_magnitude: float = 0.2
    ) -> Optional[Dict]:
        """
        Detect change points in metric time series.

        Uses a simple statistical method to detect significant changes.
        For production, consider using the ruptures library.

        Args:
            metric: Metric to analyze
            days: Days of history to analyze
            min_magnitude: Minimum change magnitude to report

        Returns:
            Dict with change point info, or None if no change detected
        """
        trend = self.get_trend(metric, days)

        if len(trend) < 10:  # Need enough data points
            return None

        # Split into two windows: first half vs second half
        mid_point = len(trend) // 2
        first_half = trend[:mid_point]
        second_half = trend[mid_point:]

        # Calculate statistics
        mean_first = np.mean(first_half)
        mean_second = np.mean(second_half)
        std_first = np.std(first_half)

        # Detect if second half is significantly different
        if std_first > 0:
            change_magnitude = abs(mean_second - mean_first) / std_first
        else:
            change_magnitude = abs(mean_second - mean_first)

        if change_magnitude >= min_magnitude:
            return {
                "metric": metric,
                "change_detected": True,
                "change_magnitude": float(change_magnitude),
                "before_mean": float(mean_first),
                "after_mean": float(mean_second),
                "direction": "increase" if mean_second > mean_first else "decrease",
                "estimated_change_point": mid_point
            }

        return None

    def detect_change_point_ruptures(
        self,
        metric: str,
        days: int = 7,
        model: str = "l2"
    ) -> Optional[Dict]:
        """
        Detect change points using ruptures library (more accurate).

        Args:
            metric: Metric to analyze
            days: Days of history to analyze
            model: Change point detection model ("l2", "rbf", "linear")

        Returns:
            Dict with change point info, or None if no change detected
        """
        try:
            import ruptures as rpt
        except ImportError:
            # Fallback to simple method if ruptures not installed
            return self.detect_change_point(metric, days)

        trend = self.get_trend(metric, days)

        if len(trend) < 10:
            return None

        # Convert to numpy array
        signal = np.array(trend).reshape(-1, 1)

        # Detect change points
        algo = rpt.Pelt(model=model, min_size=3, jump=1).fit(signal)
        change_points = algo.predict(pen=1.0)

        if len(change_points) > 1:  # At least one change point (last is always end)
            # Return info about the most recent change point
            cp_idx = change_points[-2]  # -1 is the end point

            before_values = trend[:cp_idx]
            after_values = trend[cp_idx:]

            return {
                "metric": metric,
                "change_detected": True,
                "change_point_index": cp_idx,
                "before_mean": float(np.mean(before_values)),
                "after_mean": float(np.mean(after_values)),
                "direction": "increase" if np.mean(after_values) > np.mean(before_values) else "decrease",
                "confidence": "high"
            }

        return None

    def predict_breach(
        self,
        metric: str,
        threshold: float,
        days: int = 7
    ) -> Dict:
        """
        Predict when metric will breach threshold using linear extrapolation.

        Args:
            metric: Metric to predict
            threshold: Threshold value
            days: Days of historical data to use

        Returns:
            Dict with prediction info
        """
        trend = self.get_trend(metric, days)

        if len(trend) < 5:
            return {
                "metric": metric,
                "prediction": "insufficient_data",
                "breaches_in_days": None,
                "confidence": 0.0
            }

        # Fit linear trend
        x = np.arange(len(trend))
        y = np.array(trend)

        # Calculate linear regression
        coeffs = np.polyfit(x, y, deg=1)
        slope = coeffs[0]
        intercept = coeffs[1]

        # Current value
        current_value = trend[-1]

        # Check if we're trending towards the threshold
        if (slope > 0 and current_value >= threshold) or \
           (slope < 0 and current_value <= threshold):
            return {
                "metric": metric,
                "prediction": "already_breached",
                "current_value": float(current_value),
                "threshold": threshold,
                "breaches_in_days": 0,
                "confidence": 1.0
            }

        if abs(slope) < 1e-6:  # Flat trend
            return {
                "metric": metric,
                "prediction": "stable",
                "current_value": float(current_value),
                "threshold": threshold,
                "breaches_in_days": None,
                "confidence": 0.5
            }

        # Predict days until breach
        # threshold = slope * x + intercept
        # x = (threshold - intercept) / slope
        future_x = (threshold - intercept) / slope
        days_until_breach = future_x - len(trend) + 1

        # Calculate confidence based on R² of fit
        predicted_y = slope * x + intercept
        ss_res = np.sum((y - predicted_y) ** 2)
        ss_tot = np.sum((y - np.mean(y)) ** 2)
        r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0

        return {
            "metric": metric,
            "prediction": "will_breach" if days_until_breach > 0 else "stable",
            "current_value": float(current_value),
            "threshold": threshold,
            "breaches_in_days": int(days_until_breach) if days_until_breach > 0 else None,
            "confidence": float(max(0.0, min(1.0, r_squared))),
            "trend_slope": float(slope)
        }

    def get_summary(self, days: int = 7) -> Dict:
        """Get summary of drift trends over time period."""
        snapshots = self.get_snapshots(days)

        if not snapshots:
            return {
                "status": "no_data",
                "days_analyzed": days,
                "snapshot_count": 0
            }

        # Extract common metrics
        metrics = ["contract_drift_score", "validation_drift_score", "behavioral_drift_score"]
        trends = {}

        for metric in metrics:
            trend = self.get_trend(metric, days)
            if trend:
                trends[metric] = {
                    "current": trend[-1],
                    "mean": float(np.mean(trend)),
                    "std": float(np.std(trend)),
                    "min": float(np.min(trend)),
                    "max": float(np.max(trend)),
                    "trend": "increasing" if trend[-1] > trend[0] else "decreasing"
                }

        return {
            "status": "ok",
            "days_analyzed": days,
            "snapshot_count": len(snapshots),
            "first_snapshot": snapshots[0]["timestamp"],
            "last_snapshot": snapshots[-1]["timestamp"],
            "trends": trends
        }
