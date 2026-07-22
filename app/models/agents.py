from __future__ import annotations

from sqlalchemy import (
    Boolean,
    Enum as SqlEnum,
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
from typing import TYPE_CHECKING
from app.enums.providers import ProviderEnum

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.organizations import Organization
    from app.models.users import User
    from app.models.conversations import Conversation


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

    provider: Mapped[ProviderEnum] = mapped_column(
        SqlEnum(
            ProviderEnum,
            name="provider",
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
            native_enum=False,
        ),
        nullable=False,
        default=ProviderEnum.GROQ,
    )

    model: Mapped[str] = mapped_column(
        String(100), nullable=False, default="llama-3.3-70b-versatile"
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

    organization: Mapped["Organization"] = relationship(
        back_populates="agents",
    )

    creator: Mapped["User"] = relationship(
        back_populates="created_agents",
    )

    conversations: Mapped[list["Conversation"]] = relationship(
        back_populates="agent",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return (
            f"Agent(" f"id={self.id}, " f"name='{self.name}', " f"model='{self.model}')"
        )
