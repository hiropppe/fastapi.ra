from typing import Protocol, TypeVar

from sqlalchemy.ext.asyncio import AsyncSession

PK = TypeVar("PK")  # primary key
T = TypeVar("T")  # model instance


class RepositoryProtocol(Protocol[PK, T]):
    async def get_by_id(self, pk: PK, asession: AsyncSession) -> T: ...

    async def create(self, model: T, asession: AsyncSession) -> PK: ...

    async def update(self, model: T, asession: AsyncSession) -> None: ...

    async def delete_by_id(self, pk: PK, asession: AsyncSession) -> None: ...
