from __future__ import annotations

from abc import ABC, abstractmethod

from app.document_processing.schemas.retrieve import RetrievedChunk


class BaseReranker(ABC):

    @abstractmethod
    async def rerank(
        self,
        *,
        query: str,
        chunks: list[RetrievedChunk],
        top_k: int,
    ) -> list[RetrievedChunk]:
        ...