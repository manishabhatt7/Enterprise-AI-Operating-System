from __future__ import annotations

from app.models.documents import Document
from app.enums.document import DocumentStatus
from app.document_processing.stages.base import ProcessingStage
from app.document_processing.context import ProcessingContext
from app.document_processing.stages.indexing import IndexingStage
from app.uow.unit_of_work import UnitOfWork
import logging

logger = logging.getLogger(__name__)

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
        organization_id: str,
        uow: UnitOfWork,
    ) -> None:

        context = ProcessingContext(
            document=document,
        )

        try:
            document.status = DocumentStatus.PROCESSING
            await uow.commit()

            for stage in self.stages:

                logger.info(
                    f"\n===== Running {stage.__class__.__name__} ====="
                )

                if isinstance(stage, IndexingStage):
                    await stage.run(
                        uow=uow,
                        organization_id=organization_id,
                        context=context,
                    )
                else:
                    await stage.run(
                        uow=uow,
                        context=context,
                    )

            document.status = DocumentStatus.READY
            await uow.commit()

        except Exception:
            document.status = DocumentStatus.FAILED
            await uow.commit()
            raise