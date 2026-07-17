from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.dependencies import get_db
from app.uow.unit_of_work import UnitOfWork


async def get_uow(
    session: AsyncSession = Depends(get_db),
) -> UnitOfWork:

    return UnitOfWork(session)