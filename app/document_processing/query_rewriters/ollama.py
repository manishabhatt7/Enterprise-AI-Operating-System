from __future__ import annotations

from app.document_processing.models.chat_model import get_llm
from app.document_processing.prompts.query_rewrite import (
    QueryRewritePromptBuilder,
)

from app.document_processing.query_rewriters.base import (
    BaseQueryRewriter,
)
import logging

logger = logging.getLogger(__name__)


class OllamaQueryRewriter(BaseQueryRewriter):

    async def rewrite(
        self,
        query: str,
    ) -> str:

        llm = get_llm()

        logger.info(f"Using model: {llm.model}")

        prompt = QueryRewritePromptBuilder.build(query)

        response = await llm.ainvoke(prompt)

        return response.content.strip()
