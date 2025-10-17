import dataclasses
import re
from collections.abc import Sequence
from typing import Any, Protocol, TypeVar

from sqlalchemy import Row

PK = TypeVar("PK", contravariant=True)  # primary key


@dataclasses.dataclass
class PaginationResult:
    total: int
    start: int
    end: int
    data: Sequence[Row[tuple[Any, ...]]]


class FinderProtocol(Protocol[PK]):
    async def get_by_id(self, pk: PK) -> Row | None: ...

    async def find(
        self,
        criteria: dict,
        sort: list | None = None,
        query_range: list | None = None,
    ) -> PaginationResult: ...


def remove_spaces(sql: str) -> str:
    return re.sub(r"[\u3000\s]+", " ", sql, flags=re.DOTALL)
