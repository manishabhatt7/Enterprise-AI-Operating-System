from uuid import UUID

from app.utils.slug import slugify

from app.exceptions.agent import ConflictException, NotFoundException
from app.models.agents import Agent
from app.models.users import User
from app.schemas.agent import (
    AgentCreate,
    AgentUpdate,
)
from app.uow.unit_of_work import UnitOfWork


class AgentService:
    def __init__(
        self,
        uow: UnitOfWork,
    ):
        self.uow = uow

    async def create(
        self,
        data: AgentCreate,
        current_user: User,
    ) -> Agent:

        slug = slugify(data.name)

        existing = await self.uow.agents.get_by_slug(
            organization_id=current_user.organization_id,
            slug=slug,
        )

        if existing:
            raise ConflictException(
                detail="Agent with this name already exists.",
            )

        agent = Agent(
            organization_id=current_user.organization_id,
            created_by=current_user.id,
            name=data.name,
            slug=slug,
            description=data.description,
            system_prompt=data.system_prompt,
            model=data.model,
            temperature=data.temperature,
        )

        await self.uow.agents.create(agent)
        await self.uow.commit()

        return agent

    async def list(
        self,
        current_user: User,
    ) -> list[Agent]:

        return await self.uow.agents.list_by_organization(
            current_user.organization_id,
        )

    async def get(
        self,
        agent_id: UUID,
        current_user: User,
    ) -> Agent:

        agent = await self.uow.agents.get(agent_id)

        if (
            not agent
            or agent.organization_id != current_user.organization_id
        ):
            raise NotFoundException(
                detail="Agent not found.",
            )

        return agent

    async def update(
        self,
        agent_id: UUID,
        data: AgentUpdate,
        current_user: User,
    ) -> Agent:

        agent = await self.get(
            agent_id,
            current_user,
        )

        update_data = data.model_dump(
            exclude_unset=True,
        )

        if (
            "name" in update_data
            and update_data["name"] != agent.name
        ):
            slug = slugify(update_data["name"])

            existing = await self.uow.agents.get_by_slug(
                current_user.organization_id,
                slug,
            )

            if existing and existing.id != agent.id:
                raise ConflictException(
                    detail="Agent name already exists.",
                )

            update_data["slug"] = slug

        await self.uow.agents.update(
            agent,
            **update_data,
        )

        await self.uow.commit()

        return agent

    async def delete(
        self,
        agent_id: UUID,
        current_user: User,
    ) -> None:

        agent = await self.get(
            agent_id,
            current_user,
        )

        await self.uow.agents.delete(agent)

        await self.uow.commit()