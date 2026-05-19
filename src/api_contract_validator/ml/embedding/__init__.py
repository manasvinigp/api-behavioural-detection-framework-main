"""
Response embedding module for semantic similarity comparison.
"""

from typing import Dict, Any, List, Optional
import numpy as np
import json


class ResponseEmbedder:
    """Embeds API responses into vector space for similarity comparison."""

    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        self.model_name = model_name
        self._model = None  # Lazy load
        self._cache: Dict[str, np.ndarray] = {}

    @property
    def model(self):
        """Lazy load the sentence transformer model."""
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer
                self._model = SentenceTransformer(self.model_name)
            except ImportError:
                raise ImportError(
                    "sentence-transformers is required for embedding. "
                    "Install it with: pip install sentence-transformers"
                )
        return self._model

    def _response_to_text(self, response: Dict[str, Any]) -> str:
        """Convert API response to text representation for embedding."""
        # Sort keys for consistent serialization
        def sort_dict(obj):
            if isinstance(obj, dict):
                return {k: sort_dict(v) for k, v in sorted(obj.items())}
            elif isinstance(obj, list):
                return [sort_dict(item) for item in obj]
            return obj

        sorted_response = sort_dict(response)
        # Use compact JSON representation
        return json.dumps(sorted_response, separators=(',', ':'))

    def embed(self, response: Dict[str, Any]) -> np.ndarray:
        """Embed API response into vector space."""
        # Convert response to text
        text = self._response_to_text(response)

        # Check cache
        if text in self._cache:
            return self._cache[text]

        # Generate embedding
        embedding = self.model.encode(text, convert_to_numpy=True)

        # Cache the result
        self._cache[text] = embedding

        return embedding

    def similarity(self, response_a: Dict[str, Any], response_b: Dict[str, Any]) -> float:
        """Compute semantic similarity between two responses (0-1)."""
        embedding_a = self.embed(response_a)
        embedding_b = self.embed(response_b)

        # Cosine similarity
        dot_product = np.dot(embedding_a, embedding_b)
        norm_a = np.linalg.norm(embedding_a)
        norm_b = np.linalg.norm(embedding_b)

        # Avoid division by zero
        if norm_a == 0 or norm_b == 0:
            return 0.0

        return float(dot_product / (norm_a * norm_b))

    def clear_cache(self):
        """Clear the embedding cache."""
        self._cache.clear()


class BehaviorModel:
    """Learn expected API behavior from historical responses."""

    def __init__(self, embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"):
        self.embedder = ResponseEmbedder(embedding_model)
        self.historical_embeddings: List[np.ndarray] = []
        self.centroid: Optional[np.ndarray] = None

    def train(self, historical_responses: List[Dict[str, Any]]) -> None:
        """Train behavior model on historical API responses."""
        self.historical_embeddings = [
            self.embedder.embed(response)
            for response in historical_responses
        ]

        # Calculate centroid of historical embeddings
        if self.historical_embeddings:
            self.centroid = np.mean(self.historical_embeddings, axis=0)

    def predict(self, request_input: Dict[str, Any]) -> np.ndarray:
        """Predict expected response embedding for a given request.

        For now, returns the centroid of historical embeddings.
        Future: use request features to predict specific response.
        """
        if self.centroid is None:
            raise ValueError("Model not trained. Call train() first.")
        return self.centroid

    def detect_drift(self, expected: np.ndarray, actual: np.ndarray) -> float:
        """Detect behavioral drift (0-1, where 0 = no drift, 1 = maximum drift)."""
        # Cosine similarity
        similarity = np.dot(expected, actual) / (
            np.linalg.norm(expected) * np.linalg.norm(actual)
        )
        # Convert to drift score (1 - similarity)
        return float(1.0 - similarity)

    def is_anomalous(self, response: Dict[str, Any], threshold: float = 0.3) -> bool:
        """Check if a response is anomalous compared to historical behavior.

        Args:
            response: API response to check
            threshold: Drift threshold (0-1), higher = more tolerant

        Returns:
            True if response is anomalous (drift > threshold)
        """
        if self.centroid is None:
            raise ValueError("Model not trained. Call train() first.")

        response_embedding = self.embedder.embed(response)
        drift_score = self.detect_drift(self.centroid, response_embedding)

        return drift_score > threshold
