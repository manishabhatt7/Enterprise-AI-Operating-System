from __future__ import annotations

from uuid import UUID

from app.exceptions.document import (
    DocumentNotFoundException,
)
from app.exceptions.knowledge_base import (
    KnowledgeBaseNotFound,
)
from app.models.documents import Document
from app.models.users import User
from app.storage.base import BaseStorage
from app.uow.unit_of_work import UnitOfWork


class DocumentService:
    """
    CRUD operations for documents.
    """

    def __init__(
        self,
        uow: UnitOfWork,
        storage: BaseStorage,
    ):
        self.uow = uow
        self.storage = storage

    async def list(
        self,
        *,
        knowledge_base_id: UUID,
        current_user: User,
    ) -> list[Document]:
        """
        List all documents in a Knowledge Base.
        """

        kb = await self.uow.knowledge_bases.get(
            knowledge_base_id,
        )

        if (
            kb is None
            or kb.organization_id != current_user.organization_id
        ):
            raise KnowledgeBaseNotFound()

        return await self.uow.documents.list_by_knowledge_base(
            knowledge_base_id,
        )

    async def get(
        self,
        *,
        document_id: UUID,
        current_user: User,
    ) -> Document:

        document = await self.uow.documents.get_for_organization(
            document_id=document_id,
            organization_id=current_user.organization_id,
        )

        if document is None:
            raise DocumentNotFoundException()

        return document

    async def delete(
        self,
        *,
        document_id: UUID,
        current_user: User,
    ) -> None:
        """
        Delete a document and its file.
        """

        document = await self.get(
            document_id=document_id,
            current_user=current_user,
        )

        if (
            document.storage_path
            and await self.storage.exists(
                storage_path=document.storage_path,
            )
        ):
            await self.storage.delete(
                storage_path=document.storage_path,
            )

        await self.uow.documents.delete(
            document.id,
        )

        await self.uow.commit()