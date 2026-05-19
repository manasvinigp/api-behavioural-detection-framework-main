"""Embedding model wrapper.

Uses `sentence_transformers` if available, otherwise falls back to the stub in `ml.embedding.embedder`.
"""
from typing import List

try:
    from sentence_transformers import SentenceTransformer
    _HAS_ST = True
except Exception:
    _HAS_ST = False

from api_contract_validator.ml.embedding.embedder import embed_texts as stub_embed


class EmbeddingModel:
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model_name = model_name
        self.model = None
        if _HAS_ST:
            try:
                self.model = SentenceTransformer(model_name)
            except Exception:
                self.model = None

    def embed(self, texts: List[str]) -> List[List[float]]:
        if self.model is not None:
            embeddings = self.model.encode(texts, show_progress_bar=False)
            return embeddings.tolist() if hasattr(embeddings, 'tolist') else [list(e) for e in embeddings]
        # fallback
        return stub_embed(self.model_name, texts)
