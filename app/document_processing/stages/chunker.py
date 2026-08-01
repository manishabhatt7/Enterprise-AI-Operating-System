from __future__ import annotations

from app.document_processing.chunkers.base import (
    BaseChunker,
)
from app.document_processing.context import (
    ProcessingContext,
)
from app.document_processing.stages.base import (
    ProcessingStage,
)
from app.models.documents import Document
from app.uow.unit_of_work import UnitOfWork


class ChunkingStage(ProcessingStage):

    def __init__(
        self,
        chunker: BaseChunker,
    ) -> None:
        self.chunker = chunker

    async def run(
        self,
        *,
        uow: UnitOfWork,
        context: ProcessingContext,
    ) -> None:

        print("===== Chunker Stage =====")
        if context.structured_document is None:
            raise ValueError(
                "Structured document not found."
            )

        context.structured_document = (
            await self.chunker.chunk(
                context.structured_document,
            )
        )