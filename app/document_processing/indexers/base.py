from __future__ import annotations

from abc import ABC, abstractmethod

from app.document_processing.schemas import EmbeddedDocument
from app.models.documents import Document


class BaseIndexer(ABC):
    """
    Stores embedded chunks into a vector database.
    """

    @abstractmethod
    async def index(
        self,
        *,
        document: Document,
        embedded_document: EmbeddedDocument,
    ) -> None:
        raise NotImplementedError