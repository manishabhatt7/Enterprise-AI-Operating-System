from __future__ import annotations

from abc import ABC, abstractmethod

from app.document_processing.schemas import (
    ParsedDocument,
    StructuredDocument,
)


class BaseSectionBuilder(ABC):
    """
    Builds logical document sections.
    """

    @abstractmethod
    async def build(
        self,
        parsed_document: ParsedDocument,
    ) -> StructuredDocument:
        raise NotImplementedError