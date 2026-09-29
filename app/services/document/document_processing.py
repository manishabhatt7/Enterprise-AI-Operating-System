from app.enums.document import DocumentStatus
from app.uow.unit_of_work import UnitOfWork
from app.document_processing.pipeline import DocumentProcessingPipeline
from uuid import UUID
from app.models.users import User
from app.exceptions.document import DocumentNotFoundException

class DocumentProcessingService:

    def __init__(
        self,
        uow: UnitOfWork,
        pipeline: DocumentProcessingPipeline,
    ):
        self.uow = uow
        self.pipeline = pipeline

    async def process(
        self,
        *,
        document_id: UUID,
        current_user: User,
    ) -> None:

        document = await self.uow.documents.get(document_id)

        if not document:
            raise DocumentNotFoundException()

        knowledge_base = await self.uow.knowledge_bases.get(
            document.knowledge_base_id
        )

        if not knowledge_base:
            raise ValueError("Knowledge base not found")

        organization_id = knowledge_base.organization_id


        await self.uow.documents.update(
            document,
            status=DocumentStatus.PROCESSING,
        )

        await self.uow.commit()

        try:

            await self.pipeline.run(
                document=document,
                organization_id=organization_id,
                uow=self.uow,
            )

            await self.uow.documents.update(
                document,
                status=DocumentStatus.READY,
            )

            await self.uow.commit()

        except Exception:

            await self.uow.documents.update(
                document,
                status=DocumentStatus.FAILED,
            )

            await self.uow.commit()

            raise