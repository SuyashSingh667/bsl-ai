"""
Single shared sentence-transformer instance. RAG retrieval and the
classifier both need semantic embeddings — loading two separate copies of
the same model would double memory for no benefit, so both go through this
module instead of instantiating SentenceTransformer themselves.
"""

import numpy as np
from sentence_transformers import SentenceTransformer

from app.config import EMBEDDING_MODEL_NAME

_model: SentenceTransformer | None = None


def get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        try:
            _model = SentenceTransformer(EMBEDDING_MODEL_NAME, local_files_only=True)
        except Exception:
            _model = SentenceTransformer(EMBEDDING_MODEL_NAME)
    return _model


def encode(texts: list[str]) -> np.ndarray:
    return np.asarray(get_model().encode(texts, normalize_embeddings=True), dtype="float32")
