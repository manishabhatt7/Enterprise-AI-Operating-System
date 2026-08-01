from __future__ import annotations

from dataclasses import dataclass

from app.document_processing.schemas import (
    EmbeddedDocument,
    ParsedDocument,
    StructuredDocument,
)
from app.models.documents import Document


@dataclass
class ProcessingContext:

    document: Document | None = None

    parsed_document: ParsedDocument | None = None

    structured_document: StructuredDocument | None = None

    embedded_document: EmbeddedDocument | None = None