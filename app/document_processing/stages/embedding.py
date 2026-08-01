from __future__ import annotations

from app.document_processing.context import ProcessingContext
from app.document_processing.embedders.base import (
    BaseEmbedder,
)
from app.document_processing.stages.base import (
    ProcessingStage,
)
from app.models.documents import Document
from app.uow.unit_of_work import UnitOfWork


class EmbeddingStage(ProcessingStage):

    def __init__(
        self,
        embedder: BaseEmbedder,
    ) -> None:
        self.embedder = embedder

    async def run(
        self,
        *,
        uow: UnitOfWork,
        context: ProcessingContext,
    ) -> None:

        print("===== Embedder Stage =====")
        if context.structured_document is None:
            raise ValueError(
                "Structured document not found."
            )

        context.embedded_document = (
            await self.embedder.embed(
                context.structured_document,
            )
        )