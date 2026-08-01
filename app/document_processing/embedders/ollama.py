from __future__ import annotations

from langchain_ollama import OllamaEmbeddings

from app.document_processing.embedders.base import (
    BaseEmbedder,
)
from app.document_processing.schemas import (
    EmbeddedChunk,
    EmbeddedDocument,
    StructuredDocument,
)


class OllamaEmbedder(BaseEmbedder):

    def __init__(
        self,
        model: str = "nomic-embed-text",
    ) -> None:

        self.embeddings = OllamaEmbeddings(
            model=model,
        )

    async def embed(
        self,
        document: StructuredDocument,
    ) -> EmbeddedDocument:

        embedded_chunks: list[EmbeddedChunk] = []

        for section in document.sections:

            if not section.chunks:
                continue

            vectors = await self.embeddings.aembed_documents(
                [
                    chunk.text
                    for chunk in section.chunks
                ]
            )

            for chunk, vector in zip(
                section.chunks,
                vectors,
            ):

                embedded_chunks.append(
                    EmbeddedChunk(
                        section_id=section.id,
                        section_heading=section.heading,
                        chunk=chunk,
                        embedding=vector,
                    )
                )

        return EmbeddedDocument(
            chunks=embedded_chunks,
        )