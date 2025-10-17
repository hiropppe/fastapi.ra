import re
from typing import TYPE_CHECKING, Any

import sqlalchemy
from sqlalchemy import Result, Row, text
from sqlalchemy.ext.asyncio import AsyncSession

from tuto.core.finder import FinderProtocol, PaginationResult, remove_spaces

if TYPE_CHECKING:
    from collections.abc import Sequence


class UserFinder(FinderProtocol[int]):
    def __init__(self, asession: AsyncSession) -> None:
        super().__init__()
        self.asession: AsyncSession = asession

    async def get_by_id(self, pk: int) -> Row | None:
        sql = """
            SELECT
                u.id,
                u.username,
                u.email,
                u.nickname,
                u.is_active,
                u.created_at,
                u.updated_at
            FROM
                user u
            WHERE
                u.id = :pk
            AND u.deleted_at IS NULL
        """
        sql = remove_spaces(sql)

        result: Result = await self.asession.execute(text(sql), {"pk": pk})
        try:
            return result.one()
        except sqlalchemy.exc.NoResultFound:
            return None

    async def find(
        self,
        criteria: dict,
        sort: list | None = None,
        query_range: list | None = None,
    ) -> PaginationResult:
        sql = """
            SELECT
                u.id,
                u.username,
                u.email,
                u.nickname,
                u.is_active,
                u.created_at,
                u.updated_at
            FROM
                user u
            WHERE
                u.deleted_at IS NULL
        """
        params = {}

        count_sql = re.findall(
            r"SELECT(?:.+)FROM(?:.+)(?:WHERE(?:.*))?",
            sql,
            flags=re.IGNORECASE | re.DOTALL,
        )[0]

        count_sql = re.sub(
            r"SELECT(.+)FROM",
            "SELECT COUNT(1) FROM",
            count_sql,
            flags=re.IGNORECASE | re.DOTALL,
        )
        count_sql = remove_spaces(count_sql)

        result: Result = await self.asession.execute(text(count_sql), params=params)
        total_rows: int = result.scalar_one()

        if sort and sort[0] in ("id",):
            sql += f"""
                ORDER BY u.id {sort[1]}
            """
        else:
            sql += """
                ORDER BY u.id DESC
            """

        if query_range:
            sql += """
                LIMIT :offset, :limit
            """
            offset = query_range[0]
            end = query_range[1]
            params["limit"] = end - offset + 1
            params["offset"] = offset
        else:
            offset = 0
            end = total_rows

        sql = remove_spaces(sql)

        result: Result = await self.asession.execute(text(sql), params=params)
        data: Sequence[Row[tuple[Any, ...]]] = result.all()

        return PaginationResult(
            total=total_rows,
            start=offset,
            end=min(end, total_rows),
            data=data,
        )
