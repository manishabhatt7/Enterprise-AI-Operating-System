from __future__ import annotations

from app.models.documents import (
    Document,
    DocumentStatus,
)
from app.document_processing.stages.base import ProcessingStage
from app.document_processing.context import ProcessingContext
from app.uow.unit_of_work import UnitOfWork


class DocumentProcessingPipeline:

    def __init__(
        self,
        *,
        stages: list[ProcessingStage],
    ):
        self.stages = stages

    async def run(
        self,
        *,
        document: Document,
        uow: UnitOfWork,
    ) -> None:

        context = ProcessingContext(document=document,)

        try:

            document.status = (
                DocumentStatus.PROCESSING
            )

            await uow.commit()

            for stage in self.stages:

                print(f"\n===== Running {stage.__class__.__name__} =====")
                
                await stage.run(
                    uow=uow,
                    context=context,
                )

            document.status = (
                DocumentStatus.READY
            )

            await uow.commit()

        except Exception:

            document.status = (
                DocumentStatus.FAILED
            )

            await uow.commit()

            raise