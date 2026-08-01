from __future__ import annotations

from uuid import UUID

from app.exceptions.knowledge_base import (
    KnowledgeBaseNotFound,
)
from app.models.knowledge_bases import KnowledgeBase
from app.models.users import User
from app.schemas.knowledge_base import (
    KnowledgeBaseCreate,
    KnowledgeBaseUpdate,
)
from app.uow.unit_of_work import UnitOfWork


class KnowledgeBaseService:

    def __init__(
        self,
        uow: UnitOfWork,
    ):
        self.uow = uow

    async def create(
        self,
        *,
        data: KnowledgeBaseCreate,
        current_user: User,
    ) -> KnowledgeBase:

        kb = KnowledgeBase(
            organization_id=current_user.organization_id,
            name=data.name,
            description=data.description,
        )

        await self.uow.knowledge_bases.create(
            kb,
        )

        await self.uow.commit()

        return kb

    async def get(
        self,
        *,
        knowledge_base_id: UUID,
        current_user: User,
    ) -> KnowledgeBase:

        kb = await self.uow.knowledge_bases.get(
            knowledge_base_id,
        )

        if (
            kb is None
            or kb.organization_id
            != current_user.organization_id
        ):
            raise KnowledgeBaseNotFound()

        return kb

    async def list(
        self,
        *,
        current_user: User,
    ) -> list[KnowledgeBase]:

        return await self.uow.knowledge_bases.list_by_organization(
            current_user.organization_id,
        )

    async def update(
        self,
        *,
        knowledge_base_id: UUID,
        data: KnowledgeBaseUpdate,
        current_user: User,
    ) -> KnowledgeBase:

        kb = await self.get(
            knowledge_base_id=knowledge_base_id,
            current_user=current_user,
        )

        update_data = data.model_dump(
            exclude_unset=True,
        )

        for key, value in update_data.items():
            setattr(
                kb,
                key,
                value,
            )

        await self.uow.commit()

        return kb

    async def delete(
        self,
        *,
        knowledge_base_id: UUID,
        current_user: User,
    ) -> None:

        kb = await self.get(
            knowledge_base_id=knowledge_base_id,
            current_user=current_user,
        )

        await self.uow.knowledge_bases.delete(
            kb,
        )

        await self.uow.commit()