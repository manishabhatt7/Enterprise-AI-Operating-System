from sentence_transformers import SentenceTransformer
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

_model: SentenceTransformer | None = None


def get_embedding_model() -> SentenceTransformer:

    global _model

    if _model is None:
        logger.info("Loading embedding model...")
        _model = SentenceTransformer(settings.EMBEDDING_MODEL)

    return _model
