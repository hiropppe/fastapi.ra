from sqlalchemy.ext.asyncio import AsyncSession

from tuto.model.user import User
from tuto.repository.repository import RepositoryProtocol


class UserRepository(RepositoryProtocol[int, User]):
    def __init__(self, asession: AsyncSession) -> None:
        super().__init__()
        self.asession: AsyncSession = asession

    async def get_by_id(self, pk: int) -> User:
        user: User | None = await self.asession.get(User, pk)
        if user is None:
            raise ValueError(f"User with id {pk} not found")
        return user

    async def create(self, model: User) -> int:
        self.asession.add(model)
        await self.asession.commit()
        await self.asession.refresh(model)
        return model.id  # type: ignore

    async def update(self, model: User) -> None:
        await self.asession.merge(model)
        await self.asession.commit()

    async def delete_by_id(self, pk: int) -> None:
        obj: User = await self.get_by_id(pk)
        if obj:
            await self.asession.delete(obj)
            await self.asession.commit()
