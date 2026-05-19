"""Anomaly detection utilities."""
from typing import List
try:
    from sklearn.ensemble import IsolationForest
    _HAS_SK = True
except Exception:
    _HAS_SK = False

import numpy as np


def isolation_forest_scores(embeddings: List[List[float]]) -> List[float]:
    arr = np.array(embeddings, dtype=float)
    if arr.shape[0] == 0:
        return []
    if _HAS_SK:
        iso = IsolationForest(random_state=42, n_estimators=50)
        iso.fit(arr)
        scores = iso.decision_function(arr)
        return scores.tolist()
    # fallback: use negative L2 norm deviation from mean
    mean = np.mean(arr, axis=0)
    deviations = np.linalg.norm(arr - mean, axis=1)
    # convert to scores where higher means less anomalous
    maxd = deviations.max() if deviations.size else 1.0
    scores = 1.0 - (deviations / (maxd + 1e-12))
    return scores.tolist()
