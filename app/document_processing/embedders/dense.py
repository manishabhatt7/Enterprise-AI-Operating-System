from __future__ import annotations

import asyncio

from app.document_processing.models.embedding_model import get_embedding_model

from app.document_processing.embedders.base import BaseEmbedder

from app.document_processing.schemas.processing import (
    EmbeddedChunk,
    EmbeddedDocument,
    StructuredDocument,
)


class DenseEmbedder(BaseEmbedder):

    async def embed(
        self,
        document: StructuredDocument,
    ) -> EmbeddedDocument:

        model = get_embedding_model()

        embedded_chunks: list[EmbeddedChunk] = []
        texts = []
        chunk_refs = []

        for section in document.sections:
            if not section.chunks:
                continue

            for chunk in section.chunks:
                texts.append(chunk.text)
                chunk_refs.append((section, chunk))

        if not texts:
            return EmbeddedDocument(chunks=[])


        vectors = await asyncio.to_thread(
            model.encode,
            texts,
            normalize_embeddings=True,
            convert_to_numpy=True,
        )

        for (section, chunk), vector in zip(
            chunk_refs,
            vectors,
        ):
            embedded_chunks.append(
                EmbeddedChunk(
                    section_id=section.id,
                    section_heading=section.heading,
                    chunk=chunk,
                    embedding=vector.tolist(),
                )
            )

        return EmbeddedDocument(
            chunks=embedded_chunks,
        )