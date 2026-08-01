from __future__ import annotations

from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    File,
    Response,
    UploadFile,
    status,
)

from app.dependencies.auth import get_current_user
from app.dependencies.database import get_uow
from app.models.users import User
from app.schemas.document import DocumentResponse
from app.services.document.crud import DocumentService
from app.services.document.document_upload import DocumentUploadService
from app.storage.factory import get_storage
from app.uow.unit_of_work import UnitOfWork
from app.document_processing.factory import get_processing_pipeline


router = APIRouter(
    tags=["Documents"],
)


@router.post(
    "/knowledge-bases/{knowledge_base_id}/documents",
    response_model=DocumentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_document(
    knowledge_base_id: UUID,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow),
):

    service = DocumentUploadService(
        uow=uow,
        storage=get_storage(),
    )

    return await service.upload(
        knowledge_base_id=knowledge_base_id,
        file=file,
        current_user=current_user,
    )

@router.post("documents/{document_id}/process")
async def process_document(
    document_id: UUID,
    uow: UnitOfWork = Depends(get_uow),
):

    document = await uow.documents.get(document_id)


    pipeline = get_processing_pipeline()

    await pipeline.run(
        document=document,
        uow=uow,
    )

    return {"message": "Processing completed"}

@router.get(
    "/knowledge-bases/{knowledge_base_id}/documents",
    response_model=list[DocumentResponse],
)
async def list_documents(
    knowledge_base_id: UUID,
    current_user: User = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow),
):

    service = DocumentService(
        uow=uow,
        storage=get_storage(),
    )

    return await service.list(
        knowledge_base_id=knowledge_base_id,
        current_user=current_user,
    )


@router.get(
    "/documents/{document_id}",
    response_model=DocumentResponse,
)
async def get_document(
    document_id: UUID,
    current_user: User = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow),
):

    service = DocumentService(
        uow=uow,
        storage=get_storage(),
    )

    return await service.get(
        document_id=document_id,
        current_user=current_user,
    )


@router.delete(
    "/documents/{document_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_document(
    document_id: UUID,
    current_user: User = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow),
):

    service = DocumentService(
        uow=uow,
        storage=get_storage(),
    )

    await service.delete(
        document_id=document_id,
        current_user=current_user,
    )

    return Response(
        status_code=status.HTTP_204_NO_CONTENT,
    )