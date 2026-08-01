from __future__ import annotations

from abc import ABC, abstractmethod

from app.document_processing.schemas import (
    StructuredDocument,
)


class BaseChunker(ABC):
    """
    Base interface for all chunkers.
    """

    @abstractmethod
    async def chunk(
        self,
        document: StructuredDocument,
    ) -> StructuredDocument:
        raise NotImplementedError