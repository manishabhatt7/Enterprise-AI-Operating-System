from __future__ import annotations

from pathlib import Path

from app.document_processing.context import ProcessingContext
from app.document_processing.parsers.document_parsers.base import (
    BaseDocumentParser,
)
from app.document_processing.stages.base import ProcessingStage
from app.models.documents import Document
from app.uow.unit_of_work import UnitOfWork


class ParserStage(ProcessingStage):

    def __init__(
        self,
        parser: BaseDocumentParser,
    ) -> None:
        self.parser = parser

    async def run(
        self,
        *,
        uow: UnitOfWork,
        context: ProcessingContext,
    ) -> None:

        print("===== Parser Stage =====")
        document = context.document

        if document is None:
            raise ValueError("Document not found.")
        
        parsed_document = await self.parser.parse(
            Path(document.storage_path),
        )

        context.parsed_document = parsed_document

        document.page_count = len(
            parsed_document.pages,
        )

        await uow.commit()