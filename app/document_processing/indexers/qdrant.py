from __future__ import annotations

from qdrant_client.models import PointStruct

from app.uow.unit_of_work import UnitOfWork
from app.clients.qdrant import qdrant_client
from app.core.config import settings
from app.document_processing.indexers.base import BaseIndexer
from app.document_processing.schemas.processing import EmbeddedDocument
from app.models.documents import Document
from app.document_processing.embedders.sparse import get_sparse_model
from qdrant_client.models import SparseVector


class QdrantIndexer(BaseIndexer):

    async def index(
        self,
        *,
        document: Document,
        embedded_document: EmbeddedDocument,
        organization_id: str,
    ) -> None:

        sparse_model = get_sparse_model()

        if not embedded_document.chunks:
            return

        await qdrant_client.ensure_collection(
            collection_name=settings.QDRANT_COLLECTION_NAME,
            vector_size=len(embedded_document.chunks[0].embedding),
        )

        points: list[PointStruct] = []

        for embedded_chunk in embedded_document.chunks:

            payload = {
                "organization_id": str(organization_id),
                "knowledge_base_id": str(document.knowledge_base_id),
                "document_id": str(document.id),
                "section_id": embedded_chunk.section_id,
                "section_heading": embedded_chunk.section_heading,
                "chunk_id": embedded_chunk.chunk.chunk_id,
                "chunk_index": embedded_chunk.chunk.chunk_index,
                "page_numbers": embedded_chunk.chunk.page_numbers,
                "text": embedded_chunk.chunk.text,
            }

            sparse_vector = next(sparse_model.embed(embedded_chunk.chunk.text))

            points.append(
                PointStruct(
                    id=embedded_chunk.chunk.chunk_id,
                    vector={
                        "dense": embedded_chunk.embedding,
                        "sparse": SparseVector(
                            indices=sparse_vector.indices.tolist(),
                            values=sparse_vector.values.tolist(),
                        ),
                    },
                    payload=payload,
                )
            )

        if points:

            await qdrant_client.upsert(
                collection_name=settings.QDRANT_COLLECTION_NAME,
                points=points,
            )
