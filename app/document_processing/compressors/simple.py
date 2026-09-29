from __future__ import annotations

from app.document_processing.compressors.base import BaseCompressor
from app.document_processing.schemas.retrieve import RetrievedChunk


class SimpleContextCompressor(BaseCompressor):

    def __init__(
        self,
        max_chunks: int = 5,
    ):
        self.max_chunks = max_chunks

    async def compress(
        self,
        chunks: list[RetrievedChunk],
    ) -> list[RetrievedChunk]:

        seen = set()
        compressed = []

        for chunk in chunks:

            text = chunk.chunk.text.strip()

            if text in seen:
                continue

            seen.add(text)
            compressed.append(chunk)

            if len(compressed) >= self.max_chunks:
                break

        return compressed