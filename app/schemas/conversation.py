from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.conversations import ConversationStatus


class ConversationCreate(BaseModel):
    agent_id: UUID

    title: str | None = Field(
        default=None,
        min_length=1,
        max_length=255, 
    )  


class ConversationUpdate(BaseModel):
    title: str | None = Field(
        default=None,
        min_length=1,
        max_length=255,
    )

    status: ConversationStatus | None = None


class ConversationResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
    )

    id: UUID

    organization_id: UUID

    agent_id: UUID

    user_id: UUID

    title: str

    status: ConversationStatus