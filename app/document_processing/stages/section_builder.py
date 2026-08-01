from __future__ import annotations

from app.document_processing.context import ProcessingContext
from app.document_processing.section_builders.base import (
    BaseSectionBuilder,
)
from app.document_processing.stages.base import (
    ProcessingStage,
)
from app.models.documents import Document
from app.uow.unit_of_work import UnitOfWork


class SectionBuilderStage(ProcessingStage):

    def __init__(
        self,
        builder: BaseSectionBuilder,
    ):
        self.builder = builder

    async def run(
        self,
        *,
        uow: UnitOfWork,
        context: ProcessingContext,
    ) -> None:

        print("===== Section builder Stage =====")
        if context.parsed_document is None:
            raise ValueError(
                "Parsed document not found."
            )

        context.structured_document = (
            await self.builder.build(
                context.parsed_document,
            )
        )