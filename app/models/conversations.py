from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import Enum as SqlEnum
from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from uuid import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel
from app.enums.conversation import ConversationStatus

if TYPE_CHECKING:
    from app.models.messages import Message
    from app.models.organizations import Organization
    from app.models.users import User
    from app.models.agents import Agent


class Conversation(BaseModel):
    __tablename__ = "conversations"

    organization_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey(
            "organizations.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    agent_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey(
            "agents.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    user_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey(
            "users.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    status: Mapped[ConversationStatus] = mapped_column(
        SqlEnum(
            ConversationStatus,
            name="conversation_status",
        ),
        nullable=False,
        default=ConversationStatus.ACTIVE,
    )

    messages: Mapped[list["Message"]] = relationship(
        back_populates="conversation",
        cascade="all, delete-orphan",
        order_by="Message.created_at",
    )

    organization: Mapped["Organization"] = relationship(
        back_populates="conversations",
    )

    user: Mapped["User"] = relationship(
        back_populates="conversations",
    )

    agent: Mapped["Agent"] = relationship(
        back_populates="conversations",
    )

     
    def __repr__(self) -> str:
        return (
            f"Conversation("
            f"id={self.id}, "
            f"title='{self.title}')"
        )