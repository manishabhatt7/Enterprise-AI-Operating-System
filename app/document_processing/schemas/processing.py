from __future__ import annotations

from pydantic import BaseModel, Field
from uuid import uuid4


class PageContent(BaseModel):
    """
    Markdown extracted from a single PDF page.
    """

    page_number: int
    markdown: str


class ParsedDocument(BaseModel):
    """
    Output of the parser stage.
    """

    pages: list[PageContent]


class Chunk(BaseModel):
    """
    Small chunk that will be embedded.
    """
    chunk_id: str = Field(
        default_factory=lambda: str(uuid4())
    )
    chunk_index: int
    text: str
    page_numbers: list[int]


class ParentSection(BaseModel):
    """
    Logical section extracted from markdown headers.
    """

    id: str

    heading: str

    heading_level: int

    markdown: str

    page_numbers: list[int]

    chunks: list[Chunk] = Field(
        default_factory=list,
    )


class StructuredDocument(BaseModel):
    """
    Output of the section builder.
    """

    sections: list[ParentSection]


class EmbeddedChunk(BaseModel):
    """
    Embedded child chunk.
    """

    section_id: str

    section_heading: str

    chunk: Chunk

    embedding: list[float]


class EmbeddedDocument(BaseModel):
    """
    Output of embedding stage.
    """

    chunks: list[EmbeddedChunk]