from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.messages import MessageRole


class MessageCreate(BaseModel):
    content: str


class MessageResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
    )

    id: UUID

    conversation_id: UUID

    role: MessageRole

    content: str

    metadata: dict | None = Field(alias="metadata_")

    created_at: datetime
