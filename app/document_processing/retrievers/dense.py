from __future__ import annotations

import asyncio

from qdrant_client.models import (
    Filter,
    FieldCondition,
    MatchValue,
)

from app.clients.qdrant import qdrant_client
from app.core.config import settings

from app.document_processing.models.embedding_model import get_embedding_model
from app.document_processing.retrievers.base import BaseRetriever

from app.document_processing.schemas.processing import Chunk
from app.document_processing.schemas.retrieve import RetrievedChunk



class DenseRetriever(BaseRetriever):

    async def retrieve(
        self,
        *,
        organization_id: str,
        query: str,
        top_k: int = 3,
    ) -> list[RetrievedChunk]:

        model = get_embedding_model()
        
        query_vector = (
            await asyncio.to_thread(
                model.encode,
                query,
                normalize_embeddings=True,
            )
        ).tolist()

        response = await qdrant_client.search(
            collection_name=settings.QDRANT_COLLECTION_NAME,
            query=query_vector,
            using="dense",
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

        results = response.points

        retrieved_chunks: list[RetrievedChunk] = []

        for result in results:

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
