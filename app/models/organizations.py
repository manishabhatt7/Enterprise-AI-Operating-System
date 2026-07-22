from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.users import User
    from app.models.agents import Agent
    from app.models.conversations import Conversation


class Organization(BaseModel):
    __tablename__ = "organizations"

    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
    )

    slug: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        unique=True,
        index=True,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    users: Mapped[list["User"]] = relationship(
        back_populates="organization",
        cascade="all, delete-orphan",
    )

    agents: Mapped[list["Agent"]] = relationship(
        back_populates="organization",
        cascade="all, delete-orphan",
    )

    conversations: Mapped[list["Conversation"]] = relationship(
        back_populates="organization",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return (
            f"Organization("
            f"id={self.id}, "
            f"name='{self.name}', "
            f"slug='{self.slug}')"
        )
