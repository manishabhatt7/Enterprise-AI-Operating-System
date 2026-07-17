from uuid import UUID
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class OrganizationBase(BaseModel):
    """Shared organization fields."""

    name: str = Field(
        ...,
        min_length=2,
        max_length=255,
        json_schema_extra={"example": "AIOS"},
    )

    description: str | None = Field(
        default=None,
        json_schema_extra={"example": "AI-powered enterprise platform"},
    )


class OrganizationCreate(OrganizationBase):
    """Schema for creating an organization."""

    pass


class OrganizationUpdate(BaseModel):
    """Schema for updating an organization."""

    name: str | None = Field(
        default=None,
        min_length=2,
        max_length=255,
    )

    description: str | None = None


class OrganizationResponse(OrganizationBase):
    """Schema returned by the API."""

    id: UUID
    slug: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
