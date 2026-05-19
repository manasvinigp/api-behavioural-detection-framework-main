"""
Statistical anomaly detection for API responses.
"""

from typing import List, Dict, Any, Optional
import numpy as np
import json


class IsolationForestDetector:
    """
    Anomaly detection using Isolation Forest algorithm.

    Detects outlier API responses that deviate from normal behavior.
    """

    def __init__(self, contamination: float = 0.1, n_estimators: int = 100, random_state: int = 42):
        """
        Args:
            contamination: Expected proportion of outliers (0-0.5)
            n_estimators: Number of base estimators in the ensemble
            random_state: Random seed for reproducibility
        """
        self.contamination = contamination
        self.n_estimators = n_estimators
        self.random_state = random_state
        self._model = None
        self._fitted = False

    @property
    def model(self):
        """Lazy load sklearn IsolationForest."""
        if self._model is None:
            try:
                from sklearn.ensemble import IsolationForest
                self._model = IsolationForest(
                    contamination=self.contamination,
                    n_estimators=self.n_estimators,
                    random_state=self.random_state
                )
            except ImportError:
                raise ImportError(
                    "scikit-learn is required for IsolationForest. "
                    "Install it with: pip install scikit-learn"
                )
        return self._model

    def _extract_features(self, responses: List[Dict[str, Any]]) -> np.ndarray:
        """Extract numerical features from API responses."""
        features = []

        for response in responses:
            feature_vector = self._response_to_features(response)
            features.append(feature_vector)

        return np.array(features)

    def _response_to_features(self, response: Dict[str, Any]) -> List[float]:
        """Convert a single response to feature vector."""
        features = []

        # Feature 1: Response size (number of keys)
        features.append(self._count_keys(response))

        # Feature 2: Response depth (nesting level)
        features.append(self._max_depth(response))

        # Feature 3: Number of string fields
        features.append(self._count_type(response, str))

        # Feature 4: Number of numeric fields
        features.append(self._count_type(response, (int, float)))

        # Feature 5: Number of null/None fields
        features.append(self._count_type(response, type(None)))

        # Feature 6: Total string length
        features.append(self._total_string_length(response))

        # Feature 7: JSON serialization length
        features.append(len(json.dumps(response)))

        return features

    def _count_keys(self, obj: Any, count: int = 0) -> int:
        """Recursively count keys in nested dict."""
        if isinstance(obj, dict):
            count += len(obj)
            for value in obj.values():
                count = self._count_keys(value, count)
        elif isinstance(obj, list):
            for item in obj:
                count = self._count_keys(item, count)
        return count

    def _max_depth(self, obj: Any, current_depth: int = 0) -> int:
        """Calculate maximum nesting depth."""
        if isinstance(obj, dict):
            if not obj:
                return current_depth
            return max(self._max_depth(v, current_depth + 1) for v in obj.values())
        elif isinstance(obj, list):
            if not obj:
                return current_depth
            return max(self._max_depth(item, current_depth + 1) for item in obj)
        return current_depth

    def _count_type(self, obj: Any, target_type) -> int:
        """Count occurrences of a specific type."""
        count = 0
        if isinstance(obj, target_type):
            count += 1
        if isinstance(obj, dict):
            for value in obj.values():
                count += self._count_type(value, target_type)
        elif isinstance(obj, list):
            for item in obj:
                count += self._count_type(item, target_type)
        return count

    def _total_string_length(self, obj: Any) -> int:
        """Calculate total length of all strings."""
        total = 0
        if isinstance(obj, str):
            total += len(obj)
        elif isinstance(obj, dict):
            for value in obj.values():
                total += self._total_string_length(value)
        elif isinstance(obj, list):
            for item in obj:
                total += self._total_string_length(item)
        return total

    def fit(self, normal_responses: List[Dict[str, Any]]) -> None:
        """Train on normal API responses."""
        if not normal_responses:
            raise ValueError("Cannot fit on empty response list")

        features = self._extract_features(normal_responses)
        self.model.fit(features)
        self._fitted = True

    def detect(self, response: Dict[str, Any]) -> float:
        """
        Detect if response is anomalous.

        Returns:
            Anomaly score (0-1, where 1 = definitely anomalous)
        """
        if not self._fitted:
            raise ValueError("Model not fitted. Call fit() first.")

        features = self._response_to_features(response)
        features_array = np.array([features])

        # Get anomaly score (-1 for outliers, 1 for inliers)
        prediction = self.model.predict(features_array)[0]

        # Get decision function score (more negative = more anomalous)
        score = self.model.decision_function(features_array)[0]

        # Normalize to 0-1 range (1 = anomalous)
        # Scores typically range from -0.5 to 0.5
        normalized_score = 1.0 - (score + 0.5)
        normalized_score = np.clip(normalized_score, 0.0, 1.0)

        return float(normalized_score)


class StatisticalDriftDetector:
    """
    Statistical methods for drift detection.

    Uses KL divergence, JS divergence, and KS test to detect distribution shifts.
    """

    def compute_kl_divergence(self, p: np.ndarray, q: np.ndarray, epsilon: float = 1e-10) -> float:
        """
        Kullback-Leibler divergence between distributions.

        Args:
            p: Baseline probability distribution
            q: Current probability distribution
            epsilon: Small constant to avoid log(0)

        Returns:
            KL divergence (non-negative, 0 = identical distributions)
        """
        # Ensure valid probability distributions
        p = np.asarray(p, dtype=float)
        q = np.asarray(q, dtype=float)

        # Add epsilon to avoid division by zero
        p = p + epsilon
        q = q + epsilon

        # Normalize to sum to 1
        p = p / np.sum(p)
        q = q / np.sum(q)

        # Calculate KL divergence
        kl_div = np.sum(p * np.log(p / q))

        return float(kl_div)

    def compute_js_divergence(self, p: np.ndarray, q: np.ndarray) -> float:
        """
        Jensen-Shannon divergence (symmetric KL).

        Args:
            p: Baseline probability distribution
            q: Current probability distribution

        Returns:
            JS divergence (0-1, where 0 = identical, 1 = completely different)
        """
        p = np.asarray(p, dtype=float)
        q = np.asarray(q, dtype=float)

        # Normalize
        p = p / np.sum(p)
        q = q / np.sum(q)

        # Calculate midpoint distribution
        m = (p + q) / 2.0

        # JS divergence is average of KL(p||m) and KL(q||m)
        js_div = 0.5 * self.compute_kl_divergence(p, m) + 0.5 * self.compute_kl_divergence(q, m)

        # JS divergence is bounded [0, log(2)]
        # Normalize to [0, 1]
        js_div_normalized = js_div / np.log(2)

        return float(js_div_normalized)

    def ks_test(self, baseline: List[float], current: List[float]) -> float:
        """
        Kolmogorov-Smirnov test for distribution comparison.

        Args:
            baseline: Baseline sample
            current: Current sample

        Returns:
            p-value (< 0.05 indicates significant drift)
        """
        try:
            from scipy.stats import ks_2samp
        except ImportError:
            raise ImportError(
                "scipy is required for KS test. "
                "Install it with: pip install scipy"
            )

        if not baseline or not current:
            raise ValueError("Cannot perform KS test on empty samples")

        # Perform two-sample KS test
        statistic, p_value = ks_2samp(baseline, current)

        return float(p_value)

    def detect_drift(
        self,
        baseline: List[Dict[str, Any]],
        current: List[Dict[str, Any]],
        method: str = "js"
    ) -> float:
        """
        Detect drift between baseline and current API responses.

        Args:
            baseline: Historical baseline responses
            current: Current responses to compare
            method: Statistical method ("kl", "js", or "ks")

        Returns:
            Drift score (method-dependent, higher = more drift)
        """
        if method == "ks":
            # Extract a numerical feature for KS test (e.g., response size)
            baseline_sizes = [len(json.dumps(r)) for r in baseline]
            current_sizes = [len(json.dumps(r)) for r in current]
            return self.ks_test(baseline_sizes, current_sizes)

        # For KL/JS, create histograms of response sizes
        baseline_sizes = np.array([len(json.dumps(r)) for r in baseline])
        current_sizes = np.array([len(json.dumps(r)) for r in current])

        # Create histograms with same bins
        min_size = min(baseline_sizes.min(), current_sizes.min())
        max_size = max(baseline_sizes.max(), current_sizes.max())
        bins = np.linspace(min_size, max_size, 20)

        p_hist, _ = np.histogram(baseline_sizes, bins=bins)
        q_hist, _ = np.histogram(current_sizes, bins=bins)

        # Add pseudocount to avoid zero bins
        p_hist = p_hist + 1
        q_hist = q_hist + 1

        if method == "kl":
            return self.compute_kl_divergence(p_hist, q_hist)
        elif method == "js":
            return self.compute_js_divergence(p_hist, q_hist)
        else:
            raise ValueError(f"Unknown method: {method}. Use 'kl', 'js', or 'ks'")
