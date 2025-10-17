import json
from ast import literal_eval
from collections.abc import Sequence
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.ext.asyncio import AsyncSession

from tuto.api.auth import router as auth_router
from tuto.api.auth.schemas import Me
from tuto.api.schemas import ListResponse
from tuto.api.user.schemas import UserSchema
from tuto.core.finder import PaginationResult
from tuto.core.user.finder import UserFinder
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
    current_user: Annotated[Me, Depends(auth_router.get_current_me)],
    response: Response,
    asession: Annotated[AsyncSession, Depends(get_async_session)],
) -> ListResponse[UserSchema]:
    """Get Users"""
    criteria: dict = json.loads(criteria)
    sort: list = literal_eval(sort)
    query_range: list = literal_eval(query_range)

    finder: UserFinder = UserFinder(asession)
    result: PaginationResult = await finder.find(criteria, sort, query_range)

    users: Sequence[dict] = [d._asdict() for d in result.data]
    response.headers["Content-Range"] = (
        f"appls {result.start}-{result.end}/{result.total}"
    )
    response.headers["Access-Control-Expose-Headers"] = "Content-Range"
    return ListResponse[dict](data=users)
