from __future__ import annotations

from sqlalchemy import (
    Boolean,
    Float,
    ForeignKey,
    String,
    Text,
)
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from uuid import UUID

from app.models.base import BaseModel


class Agent(BaseModel):
    __tablename__ = "agents"

    organization_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey(
            "organizations.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    created_by: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey(
            "users.id",
            ondelete="SET NULL",
        ),
        nullable=True,
        index=True,
    )

    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    slug: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    system_prompt: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    model: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    temperature: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0.7,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )

    organization = relationship(
        "Organization",
        back_populates="agents",
    )

    creator = relationship(
        "User",
        back_populates="created_agents",
    )

    def __repr__(self) -> str:
        return (
            f"Agent("
            f"id={self.id}, "
            f"name='{self.name}', "
            f"model='{self.model}')"
        )