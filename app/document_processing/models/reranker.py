from sentence_transformers import CrossEncoder
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

_model = None


def get_reranker():

    global _model

    if _model is None:
        logger.info("Loading reranker...")
        _model = CrossEncoder(settings.RERANKER_MODEL)

    return _model
