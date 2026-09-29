from __future__ import annotations

import asyncio

from app.document_processing.retrievers.base import BaseRetriever
from app.document_processing.retrievers.dense import DenseRetriever
from app.document_processing.retrievers.sparse import SparseRetriever
from app.document_processing.schemas.retrieve import RetrievedChunk


class HybridRetriever(BaseRetriever):

    def __init__(self) -> None:

        self.dense = DenseRetriever()
        self.sparse = SparseRetriever()

    async def retrieve(
        self,
        *,
        organization_id: str,
        query: str,
        top_k: int = 10,
    ) -> list[RetrievedChunk]:

        dense_results, sparse_results = await asyncio.gather(
            self.dense.retrieve(
                organization_id=organization_id,
                query=query,
                top_k=top_k,
            ),
            self.sparse.retrieve(
                organization_id=organization_id,
                query=query,
                top_k=top_k,
            ),
        )

        return self._fuse(
            dense_results=dense_results,
            sparse_results=sparse_results,
        )

    def _fuse(
    self,
    *,
    dense_results: list[RetrievedChunk],
    sparse_results: list[RetrievedChunk],
    k: int = 60,
) -> list[RetrievedChunk]:

        scores: dict[str, float] = {}
        chunks: dict[str, RetrievedChunk] = {}

        for rank, result in enumerate(dense_results, start=1):

            chunk_id = result.chunk.chunk_id

            scores[chunk_id] = scores.get(chunk_id, 0.0) + 1 / (k + rank)

            chunks[chunk_id] = result

        for rank, result in enumerate(sparse_results, start=1):

            chunk_id = result.chunk.chunk_id

            scores[chunk_id] = scores.get(chunk_id, 0.0) + 1 / (k + rank)

            chunks[chunk_id] = result

        fused = sorted(
            chunks.values(),
            key=lambda x: scores[x.chunk.chunk_id],
            reverse=True,
        )

        return fused