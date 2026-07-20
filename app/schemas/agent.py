from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class AgentCreate(BaseModel):
    name: str = Field(
        min_length=2,
        max_length=255,
    )

    description: str | None = None

    system_prompt: str

    model: str = "gpt-4.1-mini"

    temperature: float = Field(
        default=0.7,
        ge=0,
        le=2,
    )


class AgentUpdate(BaseModel):
    name: str | None = Field(
        default=None,
        min_length=2,
        max_length=255,
    )

    description: str | None = None

    system_prompt: str | None = None

    model: str | None = None

    temperature: float | None = Field(
        default=None,
        ge=0,
        le=2,
    )

    is_active: bool | None = None


class AgentResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
    )

    id: UUID

    organization_id: UUID

    created_by: UUID | None

    name: str

    slug: str

    description: str | None

    system_prompt: str

    model: str

    temperature: float

    is_active: bool
