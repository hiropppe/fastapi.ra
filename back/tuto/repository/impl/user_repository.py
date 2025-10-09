from sqlalchemy.ext.asyncio import AsyncSession

from tuto.model.user import User
from tuto.repository.repository import RepositoryProtocol


class UserRepository(RepositoryProtocol[int, User]):
    async def get_by_id(self, pk: int, asession: AsyncSession) -> User:
        user: User | None = await asession.get(User, pk)
        if user is None:
            raise ValueError(f"User with id {pk} not found")
        return user

    async def create(self, model: User, asession: AsyncSession) -> int:
        asession.add(model)
        await asession.commit()
        await asession.refresh(model)
        return model.id  # type: ignore

    async def update(self, model: User, asession: AsyncSession) -> None:
        await asession.merge(model)
        await asession.commit()

    async def delete_by_id(self, pk: int, asession: AsyncSession) -> None:
        obj = await self.get_by_id(pk, asession)
        if obj:
            await asession.delete(obj)
            await asession.commit()
