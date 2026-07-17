
from app.models.organizations import Organization
from app.schemas.organization import (
    OrganizationCreate,
    OrganizationUpdate,
)
from app.uow.unit_of_work import UnitOfWork
from app.utils.slug import slugify
from app.exceptions.organization import (
    OrganizationAlreadyExists,
    OrganizationNotFound,
)


class OrganizationService:
    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    async def create(
        self,
        data: OrganizationCreate,
    ) -> Organization:

        existing = await self.uow.organizations.get_by_name(
            data.name,
        )

        if existing:
            raise OrganizationAlreadyExists()

        slug = slugify(data.name)

        counter = 1

        while await self.uow.organizations.get_by_slug(slug):
            counter += 1
            slug = f"{slugify(data.name)}-{counter}"

        organization = Organization(
            name=data.name,
            slug=slug,
            description=data.description,
        )

        await self.uow.organizations.create(
            organization,
        )

        await self.uow.commit()

        return organization

    async def get(self, organization_id):
        organization = await self.uow.organizations.get(
            organization_id,
        )

        if not organization:
            raise OrganizationNotFound()
            

        return organization

    async def list(self):
        return await self.uow.organizations.list()

    async def update(
        self,
        organization_id,
        data: OrganizationUpdate,
    ):
        organization = await self.get(
            organization_id,
        )

        values = data.model_dump(
            exclude_unset=True,
        )

        if "name" in values:
            values["slug"] = slugify(
                values["name"],
            )

        organization = await self.uow.organizations.update(
            organization,
            **values,
        )

        await self.uow.commit()

        return organization

    async def delete(
        self,
        organization_id,
    ):
        organization = await self.get(
            organization_id,
        )

        await self.uow.organizations.delete(
            organization,
        )

        await self.uow.commit()