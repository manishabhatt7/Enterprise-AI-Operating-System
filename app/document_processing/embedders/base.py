from __future__ import annotations

from abc import ABC, abstractmethod

from app.document_processing.schemas import (
    EmbeddedDocument,
    StructuredDocument,
)


class BaseEmbedder(ABC):
    """
    Base interface for embedding providers.
    """

    @abstractmethod
    async def embed(
        self,
        document: StructuredDocument,
    ) -> EmbeddedDocument:
        raise NotImplementedError