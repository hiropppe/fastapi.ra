from typing import Protocol, TypeVar

PK = TypeVar("PK")  # primary key
T = TypeVar("T")  # model instance


class RepositoryProtocol(Protocol[PK, T]):
    async def get_by_id(self, pk: PK) -> T: ...

    async def create(self, model: T) -> PK: ...

    async def update(self, model: T) -> None: ...

    async def delete_by_id(self, pk: PK) -> None: ...
