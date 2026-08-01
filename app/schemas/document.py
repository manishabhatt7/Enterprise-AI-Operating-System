from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, field_validator


class DocumentResponse(BaseModel):

    model_config = ConfigDict(
        from_attributes=True,
    )

    id: UUID

    knowledge_base_id: UUID

    filename: str

    storage_path: str

    content_type: str

    file_size: str

    page_count: int | None

    status: str

    created_at: datetime

    updated_at: datetime

    @field_validator("file_size", mode="before")
    @classmethod
    def convert_bytes_to_mb(cls, value: int | str) -> str:
        if isinstance(value, int):
            mb_size = round(value / (1024 * 1024), 2)
            if value > 0 and mb_size == 0.0:
                mb_size = 0.01
            return f"{mb_size} MB"
        return str(value)

