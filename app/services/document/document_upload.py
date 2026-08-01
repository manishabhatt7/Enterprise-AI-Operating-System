from __future__ import annotations

from uuid import UUID, uuid4

from fastapi import UploadFile

from app.exceptions.document import (
    DocumentTooLargeException,
    UnsupportedDocumentTypeException,
)
from app.exceptions.knowledge_base import KnowledgeBaseNotFound
from app.models.documents import Document
from app.enums.document import DocumentStatus

from app.models.users import User
from app.storage.base import BaseStorage
from app.uow.unit_of_work import UnitOfWork
from app.core.config import settings


class DocumentUploadService:
    """
    Handles document uploads.
    """

    ALLOWED_CONTENT_TYPES = settings.ALLOWED_DOCUMENT_TYPES

    MAX_FILE_SIZE = settings.MAX_DOCUMENT_SIZE

    def __init__(
        self,
        uow: UnitOfWork,
        storage: BaseStorage,
    ):
        self.uow = uow
        self.storage = storage

    async def upload(
        self,
        *,
        knowledge_base_id: UUID,
        file: UploadFile,
        current_user: User,
    ) -> Document:

        kb = await self.uow.knowledge_bases.get(
            knowledge_base_id,
        )

        if (
            kb is None
            or kb.organization_id != current_user.organization_id
        ):
            raise KnowledgeBaseNotFound()

        if file.content_type not in self.ALLOWED_CONTENT_TYPES:
            raise UnsupportedDocumentTypeException()

        # Determine file size 
        file_size = file.size

        if file_size > self.MAX_FILE_SIZE:
            raise DocumentTooLargeException()

        document = Document(
            id=uuid4(),
            knowledge_base_id=kb.id,
            filename=file.filename,
            content_type=file.content_type,
            file_size=file_size,
            status=DocumentStatus.PENDING,
        )

        try:

            storage_path: str = await self.storage.save(
                file=file,
                organization_id=current_user.organization_id,
                knowledge_base_id=kb.id,
                document_id=document.id,
            )

            document.storage_path = storage_path

            await self.uow.documents.create(
                document,
            )

            await self.uow.commit()

            return document

        except Exception as exc:

            if (
                document.storage_path
                and await self.storage.exists(
                    storage_path=document.storage_path,
                )
            ):
                await self.storage.delete(
                    storage_path=document.storage_path,
                )

            raise exc