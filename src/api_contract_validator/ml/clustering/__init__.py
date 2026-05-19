"""
Behavioral clustering for API response patterns.
"""

from typing import List, Dict, Any, Optional
import numpy as np


class BehaviorClusterer:
    """
    Cluster API responses by behavioral similarity.

    Groups similar API behaviors to detect anomalies and drift.
    """

    def __init__(
        self,
        n_clusters: int = 5,
        method: str = "kmeans",
        random_state: int = 42
    ):
        """
        Args:
            n_clusters: Number of clusters (for kmeans)
            method: Clustering method ("kmeans" or "dbscan")
            random_state: Random seed for reproducibility
        """
        self.n_clusters = n_clusters
        self.method = method
        self.random_state = random_state
        self._model = None
        self._fitted = False
        self._cluster_centers: Optional[np.ndarray] = None

    @property
    def model(self):
        """Lazy load clustering model."""
        if self._model is None:
            try:
                if self.method == "kmeans":
                    from sklearn.cluster import KMeans
                    self._model = KMeans(
                        n_clusters=self.n_clusters,
                        random_state=self.random_state,
                        n_init=10
                    )
                elif self.method == "dbscan":
                    from sklearn.cluster import DBSCAN
                    self._model = DBSCAN(eps=0.5, min_samples=5)
                else:
                    raise ValueError(f"Unknown clustering method: {self.method}")
            except ImportError:
                raise ImportError(
                    "scikit-learn is required for clustering. "
                    "Install it with: pip install scikit-learn"
                )
        return self._model

    def _extract_features(self, responses: List[Dict[str, Any]]) -> np.ndarray:
        """Extract numerical features from responses for clustering."""
        # Use the same feature extraction as IsolationForest for consistency
        from api_contract_validator.ml.anomaly import IsolationForestDetector

        detector = IsolationForestDetector()
        features = []

        for response in responses:
            feature_vector = detector._response_to_features(response)
            features.append(feature_vector)

        return np.array(features)

    def fit(self, responses: List[Dict[str, Any]]) -> None:
        """Cluster historical responses."""
        if not responses:
            raise ValueError("Cannot fit on empty response list")

        features = self._extract_features(responses)
        self.model.fit(features)
        self._fitted = True

        # Store cluster centers for distance calculations
        if hasattr(self.model, 'cluster_centers_'):
            self._cluster_centers = self.model.cluster_centers_

    def predict_cluster(self, response: Dict[str, Any]) -> int:
        """Predict which cluster a response belongs to."""
        if not self._fitted:
            raise ValueError("Model not fitted. Call fit() first.")

        from api_contract_validator.ml.anomaly import IsolationForestDetector

        detector = IsolationForestDetector()
        features = detector._response_to_features(response)
        features_array = np.array([features])

        cluster_id = self.model.predict(features_array)[0]
        return int(cluster_id)

    def distance_to_nearest_cluster(self, response: Dict[str, Any]) -> float:
        """
        Calculate distance from response to nearest cluster centroid.

        Returns:
            Distance (Euclidean) to nearest cluster center
        """
        if not self._fitted:
            raise ValueError("Model not fitted. Call fit() first.")

        if self._cluster_centers is None:
            # DBSCAN doesn't have cluster_centers_
            # Use distance to nearest training point instead
            return 0.0

        from api_contract_validator.ml.anomaly import IsolationForestDetector

        detector = IsolationForestDetector()
        features = detector._response_to_features(response)
        features_array = np.array(features)

        # Calculate distances to all centroids
        distances = np.linalg.norm(self._cluster_centers - features_array, axis=1)

        return float(np.min(distances))

    def is_outlier(self, response: Dict[str, Any], threshold: float = 2.0) -> bool:
        """
        Detect if response is far from all cluster centroids.

        Args:
            response: API response to check
            threshold: Distance threshold (in standard deviations)

        Returns:
            True if response is an outlier
        """
        if not self._fitted:
            raise ValueError("Model not fitted. Call fit() first.")

        distance = self.distance_to_nearest_cluster(response)

        # Calculate statistics of distances for all cluster centers
        if self._cluster_centers is not None:
            # Get pairwise distances between centroids to estimate typical distance
            from scipy.spatial.distance import pdist
            centroid_distances = pdist(self._cluster_centers)

            if len(centroid_distances) > 0:
                mean_dist = np.mean(centroid_distances)
                std_dist = np.std(centroid_distances)

                # Response is outlier if distance > mean + threshold * std
                return distance > (mean_dist + threshold * std_dist)

        # Fallback: use absolute threshold if we can't calculate statistics
        return distance > threshold


class BehavioralPatternAnalyzer:
    """
    Analyze behavioral patterns across clustered API responses.

    Identifies common behaviors and detects deviations.
    """

    def __init__(self, clusterer: BehaviorClusterer):
        self.clusterer = clusterer
        self.cluster_labels: Dict[int, str] = {}

    def analyze_clusters(
        self,
        responses: List[Dict[str, Any]],
        cluster_ids: List[int]
    ) -> Dict[int, Dict[str, Any]]:
        """
        Analyze characteristics of each cluster.

        Args:
            responses: API responses
            cluster_ids: Cluster assignments for each response

        Returns:
            Dict mapping cluster_id to cluster characteristics
        """
        cluster_stats = {}

        for cluster_id in set(cluster_ids):
            # Get responses in this cluster
            cluster_responses = [
                resp for resp, cid in zip(responses, cluster_ids)
                if cid == cluster_id
            ]

            # Calculate statistics
            stats = {
                "size": len(cluster_responses),
                "percentage": len(cluster_responses) / len(responses) * 100,
                "avg_response_size": np.mean([
                    len(str(r)) for r in cluster_responses
                ]),
                "sample_response": cluster_responses[0] if cluster_responses else None
            }

            cluster_stats[cluster_id] = stats

        return cluster_stats

    def label_cluster(self, cluster_id: int, label: str) -> None:
        """Assign human-readable label to a cluster."""
        self.cluster_labels[cluster_id] = label

    def get_cluster_summary(self) -> Dict[str, Any]:
        """Get summary of all clusters with labels."""
        return {
            "n_clusters": self.clusterer.n_clusters,
            "labels": self.cluster_labels,
            "method": self.clusterer.method
        }
