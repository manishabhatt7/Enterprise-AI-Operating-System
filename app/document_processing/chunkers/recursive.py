from __future__ import annotations

from uuid import uuid4

from langchain_text_splitters import (
    RecursiveCharacterTextSplitter,
)

from app.document_processing.chunkers.base import (
    BaseChunker,
)
from app.document_processing.schemas import (
    Chunk,
    StructuredDocument,
)


class RecursiveChunker(BaseChunker):

    def __init__(
        self,
        chunk_size: int = 750,
        chunk_overlap: int = 100,
    ) -> None:

        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=[
                "\n\n",
                "\n",
                ". ",
                " ",
                "",
            ],
        )

    async def chunk(
        self,
        document: StructuredDocument,
    ) -> StructuredDocument:

        for section in document.sections:

            texts = self.splitter.split_text(
                section.markdown,
            )

            section.chunks = [
                Chunk(
                    chunk_id=str(uuid4()),
                    chunk_index=index,
                    text=text,
                    page_numbers=section.page_numbers,
                )
                for index, text in enumerate(texts)
            ]

        return document