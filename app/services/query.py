from app.core.config import settings
from app.document_processing.compressors.simple import SimpleContextCompressor
from app.document_processing.query_rewriters.ollama import OllamaQueryRewriter
from app.document_processing.retrievers.hybrid import HybridRetriever
from app.document_processing.rerankers.bge import BGEReranker
from app.document_processing.schemas.query import QueryResponse, SourceChunk

import logging

logger = logging.getLogger(__name__)

class QueryService:

    RETRIEVAL_TOP_K = settings.RETRIEVAL_TOP_K
    RERANK_TOP_K = settings.RERANK_TOP_K

    def __init__(self):
        self.query_rewriter = OllamaQueryRewriter()
        self.retriever = HybridRetriever()
        self.reranker = BGEReranker()
        self.compressor = SimpleContextCompressor()

    async def query(
        self,
        *,
        query: str,
        organization_id: str,
    ) -> QueryResponse:

        logger.info(
            "RAG query started: query=%s organization_id=%s",
            query,
            organization_id,
        )

        rewritten_query = await self.query_rewriter.rewrite(query)

        logger.info(
            "Query rewritten: %s",
            rewritten_query,
        )

        retrieved_chunks = await self.retriever.retrieve(
            query=rewritten_query,
            organization_id=organization_id,
            top_k=self.RETRIEVAL_TOP_K,
        )

        logger.info(
            "Retrieved %d chunks from hybrid search",
            len(retrieved_chunks),
        )
        for i, chunk in enumerate(retrieved_chunks, 1):
            logger.info(
                "  [Retrieved #%d] (score=%.4f): %s",
                i,
                getattr(chunk, "score", 0.0) or 0.0,
                repr(chunk.chunk.text[:150]),
            )

        reranked_chunks = await self.reranker.rerank(
            query=rewritten_query,
            chunks=retrieved_chunks,
            top_k=self.RERANK_TOP_K,
        )

        logger.info(
            "Reranked %d chunks (top_k=%d)",
            len(reranked_chunks),
            self.RERANK_TOP_K,
        )
        for i, chunk in enumerate(reranked_chunks, 1):
            logger.info(
                "  [Reranked #%d] (rerank_score=%.4f): %s",
                i,
                chunk.score,
                repr(chunk.chunk.text[:150]),
            )

        compressed_chunks = await self.compressor.compress(
            reranked_chunks,
        )

        logger.info(
            "Compressed %d chunks",
            len(compressed_chunks),
        )
        for i, chunk in enumerate(compressed_chunks, 1):
            logger.info(
                "  [Final Chunk #%d]:\n%s",
                i,
                chunk.chunk.text.strip(),
            )

        context = "\n\n".join(
            chunk.chunk.text
            for chunk in compressed_chunks
        )

        logger.info(
            "Final RAG Context to LLM (%d chars):\n%s",
            len(context),
            context,
        )

        response = QueryResponse(
            context=context,
            sources=[
                SourceChunk(
                    text=chunk.chunk.text,
                    page_numbers=chunk.chunk.page_numbers,
                )
                for chunk in compressed_chunks
            ],
        )

        logger.info("RAG query completed successfully")

        return response