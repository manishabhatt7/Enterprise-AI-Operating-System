from __future__ import annotations

import asyncio

from qdrant_client.models import (
    Filter,
    FieldCondition,
    MatchValue,
    SparseVector,
)

from app.clients.qdrant import qdrant_client
from app.core.config import settings

from app.document_processing.embedders.sparse import (
    get_sparse_model,
)
from app.document_processing.retrievers.base import BaseRetriever
from app.document_processing.schemas.processing import Chunk
from app.document_processing.schemas.retrieve import RetrievedChunk


class SparseRetriever(BaseRetriever):

    async def retrieve(
        self,
        *,
        organization_id: str,
        query: str,
        top_k: int = 20,
    ) -> list[RetrievedChunk]:

        model = get_sparse_model()

        sparse_vector = await asyncio.to_thread(
            lambda: next(model.embed(query))
        )

        response = await qdrant_client.search(
            collection_name=settings.QDRANT_COLLECTION_NAME,

            query=SparseVector(
                indices=sparse_vector.indices.tolist(),
                values=sparse_vector.values.tolist(),
            ),

            using="sparse",

            limit=top_k,

            query_filter=Filter(
                must=[
                    FieldCondition(
                        key="organization_id",
                        match=MatchValue(
                            value=organization_id,
                        ),
                    )
                ]
            ),

            with_payload=True,
        )

        retrieved_chunks: list[RetrievedChunk] = []

        for result in response.points:

            payload = result.payload

            retrieved_chunks.append(
                RetrievedChunk(
                    score=result.score,
                    chunk=Chunk(
                        chunk_id=str(result.id),
                        chunk_index=payload["chunk_index"],
                        text=payload["text"],
                        page_numbers=payload["page_numbers"],
                    ),
                )
            )

        return retrieved_chunks