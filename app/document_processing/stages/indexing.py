from __future__ import annotations

from app.document_processing.context import ProcessingContext
from app.document_processing.indexers.base import BaseIndexer
from app.document_processing.stages.base import ProcessingStage
from app.uow.unit_of_work import UnitOfWork


class IndexingStage(ProcessingStage):

    def __init__(
        self,
        indexer: BaseIndexer,
    ) -> None:
        self.indexer = indexer

    async def run(
        self,
        *,
        uow: UnitOfWork,
        context: ProcessingContext,
    ) -> None:
        print("===== Indexer Stage =====")
        if context.document is None:
            raise ValueError("Document not found.")

        if context.embedded_document is None:
            raise ValueError("Embedded document not found.")

        await self.indexer.index(
            document=context.document,
            embedded_document=context.embedded_document,
        )