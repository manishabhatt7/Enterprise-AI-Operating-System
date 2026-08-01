from __future__ import annotations

from qdrant_client import AsyncQdrantClient
from qdrant_client.models import PointStruct

from app.core.config import settings

from qdrant_client.models import VectorParams, Distance
from qdrant_client.http.exceptions import UnexpectedResponse


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
            collection_name=collection_name,
            vectors_config=VectorParams(
                size=vector_size,
                distance=Distance.COSINE,
            ),
        )

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


qdrant_client = QdrantClient()