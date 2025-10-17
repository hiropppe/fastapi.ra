from typing import Annotated

from fastapi import Depends
from sqlalchemy import Result
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from tuto.datasource.database import get_async_session
from tuto.model.user import User
from tuto.repository.repository import RepositoryProtocol


async def get_by_username_or_email(
    username: str,
    asession: AsyncSession,
) -> User | None:
    result: Result = await asession.execute(
        select(User).where((User.username == username) | (User.email == username))
    )
    return result.scalars().first()


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

    async def get_by_username(self, username: str) -> User | None:
        result: Result = await self.asession.execute(
            select(User).where(User.username == username)
        )
        return result.scalars().first()
