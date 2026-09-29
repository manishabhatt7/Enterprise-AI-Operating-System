from __future__ import annotations

from app.document_processing.rerankers.base import BaseReranker
from app.document_processing.schemas.retrieve import RetrievedChunk
from app.document_processing.models.reranker import get_reranker


class BGEReranker(BaseReranker):

    async def rerank(
        self,
        *,
        query: str,
        chunks: list[RetrievedChunk],
        top_k: int,
    ) -> list[RetrievedChunk]:

        model = get_reranker()

        if not chunks:
            return []

        pairs = [
            (
                query,
                chunk.chunk.text,
            )
            for chunk in chunks
        ]

        scores = model.predict(pairs)

        for chunk, score in zip(chunks, scores):
            chunk.score = float(score)

        chunks.sort(
            key=lambda c: c.score,
            reverse=True,
        )

        return chunks[:top_k]