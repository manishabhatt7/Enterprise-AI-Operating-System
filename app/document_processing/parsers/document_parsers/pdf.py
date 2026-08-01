from __future__ import annotations

from pathlib import Path

import pymupdf4llm

from app.document_processing.parsers.document_parsers.base import (
    BaseDocumentParser,
)
from app.document_processing.schemas import (
    PageContent,
    ParsedDocument,
)


class PDFParser(BaseDocumentParser):

    async def parse(
        self,
        file_path: Path,
    ) -> ParsedDocument:

        page_chunks = pymupdf4llm.to_markdown(
            file_path,
            page_chunks=True,
            force_text=True,
        )

        pages = [
            PageContent(
                page_number=chunk["metadata"]["page_number"],
                markdown=chunk["text"].strip(),
            )
            for chunk in page_chunks
        ]

        return ParsedDocument(
            pages=pages,
        )