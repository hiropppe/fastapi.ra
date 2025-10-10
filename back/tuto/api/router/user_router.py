import os
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import Session

from tuto.api.router.auth_router import get_current_user
from tuto.api.schema.auth_schema import AuthUser
from tuto.api.schema.base_schema import ListResponse
from tuto.datasource.database import get_async_session

router = APIRouter()


@router.get(
    "/users",
    summary="",
    description="",
    response_description="",
    response_model_exclude_none=True,
)
async def get_list(
    criteria: Annotated[str, Query(alias="filter")],
    sort: str,
    query_range: Annotated[str, Query(alias="range")],
    current_user: Annotated[AuthUser, Depends(get_current_user)],
    response: Response,
    asession: Annotated[AsyncSession, Depends(get_async_session)],
) -> ListResponse[AuthUser]:
    """Get Users"""
    await asession.execute(text("SELECT 1"))
    data: list[AuthUser] = [
        AuthUser(id=1, email="user1@test.com", username="user1", nickname="User 1"),
        AuthUser(id=2, email="user1@test.com", username="user2", nickname="User 2"),
    ]
    response.headers["Content-Range"] = "users 1-2/2"
    response.headers["Access-Control-Expose-Headers"] = "Content-Range"
    return ListResponse(data=data)
