"""Simple clustering utilities for behavioral analysis."""
from typing import List, Optional
try:
    from sklearn.cluster import KMeans
    _HAS_SK = True
except Exception:
    _HAS_SK = False

import numpy as np


def kmeans_cluster(embeddings: List[List[float]], n_clusters: int = 5) -> List[int]:
    arr = np.array(embeddings, dtype=float)
    if arr.shape[0] == 0:
        return []
    if _HAS_SK:
        km = KMeans(n_clusters=min(n_clusters, arr.shape[0]), random_state=42)
        labels = km.fit_predict(arr)
        return labels.tolist()
    # fallback: simple nearest-centroid by splitting
    n = min(n_clusters, arr.shape[0])
    idx = np.arange(arr.shape[0])
    return (idx % n).tolist()
