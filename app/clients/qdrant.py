from __future__ import annotations

from qdrant_client import AsyncQdrantClient
from qdrant_client.models import PointStruct, SparseVector, VectorParams, Distance, SparseVectorParams, Filter, PayloadSchemaType
from qdrant_client.http.exceptions import UnexpectedResponse

from app.core.config import settings


class QdrantClient:

    def __init__(self) -> None:

        self.client = AsyncQdrantClient(
            url=settings.QDRANT_URL,
            api_key=settings.QDRANT_API_KEY,
        )

    async def ensure_collection(
        self,
        collection_name: str,
        vector_size: int,
    ) -> None:
        """
        Creates the collection if it doesn't already exist.
        """

        try:
            await self.client.get_collection(collection_name)
            return

        except UnexpectedResponse as e:
            # 404 -> collection doesn't exist
            if e.status_code != 404:
                raise

        await self.client.create_collection(
            collection_name=settings.QDRANT_COLLECTION_NAME,
            vectors_config={
                "dense": VectorParams(
                    size=vector_size,
                    distance=Distance.COSINE,
                ),
            },
            sparse_vectors_config={
                "sparse": SparseVectorParams(),
            },
        )

        try:
            await self.client.create_payload_index(
                collection_name=collection_name,
                field_name="organization_id",
                field_schema=PayloadSchemaType.UUID,
            )
        except Exception:
            # Index may already exist
            pass

    async def upsert(
        self,
        *,
        collection_name: str,
        points: list[PointStruct],
    ) -> None:

        await self.client.upsert(
            collection_name=collection_name,
            points=points,
            wait=True,
        )

    async def search(
        self,
        *,
        collection_name: str,
        query: list[float] | SparseVector,
        using: str,
        limit: int = 5,
        query_filter: Filter | None = None,
        with_payload: bool = True,
    ):
        return await self.client.query_points(
            collection_name=collection_name,
            query=query,
            using=using,
            limit=limit,
            query_filter=query_filter,
            with_payload=with_payload,
        )


qdrant_client = QdrantClient()
