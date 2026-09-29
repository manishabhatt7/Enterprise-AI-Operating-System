from __future__ import annotations

from pydantic import BaseModel

from app.document_processing.schemas.processing import Chunk


class RetrievedChunk(BaseModel):
    chunk: Chunk
    score: float