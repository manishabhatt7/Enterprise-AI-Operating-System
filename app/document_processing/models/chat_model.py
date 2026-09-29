from langchain_ollama import ChatOllama
from app.core.config import settings

import logging

logger = logging.getLogger(__name__)

_llm = None

def get_llm():
    
    global _llm

    if _llm is None:
        logger.info("Loading LLM...")

        _llm = ChatOllama(
            model=settings.OLLAMA_LLM_MODEL,
            base_url=settings.OLLAMA_BASE_URL,
            temperature=0.2,
        )

    return _llm