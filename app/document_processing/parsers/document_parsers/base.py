from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from app.document_processing.schemas import ParsedDocument


class BaseDocumentParser(ABC):
    """
    Base interface for document parsers.
    """

    @abstractmethod
    async def parse(
        self,
        file_path: Path,
    ) -> ParsedDocument:
        raise NotImplementedError