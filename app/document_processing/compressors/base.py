from abc import ABC, abstractmethod

from app.document_processing.schemas.retrieve import RetrievedChunk


class BaseCompressor(ABC):

    @abstractmethod
    async def compress(
        self,
        chunks: list[RetrievedChunk],
    ) -> list[RetrievedChunk]:
        ...