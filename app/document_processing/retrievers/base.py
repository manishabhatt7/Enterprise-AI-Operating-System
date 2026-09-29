from __future__ import annotations

from abc import ABC, abstractmethod

from app.document_processing.schemas.retrieve import RetrievedChunk


class BaseRetriever(ABC):

    @abstractmethod
    async def retrieve(
        self,
        *,
        organization_id: str,
        query: str,
        top_k: int = 5,
    ) -> list[RetrievedChunk]:
        ...