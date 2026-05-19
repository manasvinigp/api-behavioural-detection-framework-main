"""Simple embedding stub.

This module provides a minimal, test-friendly embedding interface.
Replace with a real model (sentence-transformers or other) for production.
"""
from typing import List
import numpy as np


def embed_texts(model_name: str, texts: List[str]) -> List[List[float]]:
    """Return dummy embeddings (zeros) with deterministic shape.

    Args:
        model_name: name of embedding model (not used in stub)
        texts: list of strings to embed

    Returns:
        list of float vectors
    """
    dim = 384
    embeddings = [ [0.0]*dim for _ in texts ]
    return embeddings


def cosine_similarity(a: List[float], b: List[float]) -> float:
    """Compute cosine similarity for two vectors (safe stub).
    """
    a_arr = np.array(a, dtype=float)
    b_arr = np.array(b, dtype=float)
    na = np.linalg.norm(a_arr)
    nb = np.linalg.norm(b_arr)
    if na == 0 or nb == 0:
        return 0.0
    return float(np.dot(a_arr, b_arr) / (na * nb))
