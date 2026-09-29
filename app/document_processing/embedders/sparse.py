from __future__ import annotations

from fastembed import SparseTextEmbedding
import logging

logger = logging.getLogger(__name__)

_sparse_model = None


def get_sparse_model() -> SparseTextEmbedding:

    global _sparse_model

    if _sparse_model is None:

        logger.info("Loading BM25 model...")

        _sparse_model = SparseTextEmbedding(model_name="Qdrant/bm25")

    return _sparse_model
