from collections.abc import Sequence
from typing import TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class ResponseBase(BaseModel):
    status_code: str = Field(default="SUCCESS", title="ステータスコード")
    error_type: str | None = Field(default=None, title="")
    error_code: str | None = Field(default=None, title="")
    message: str | None = Field(default=None, title="")


class ListResponse[T](ResponseBase):
    data: Sequence[T] = Field(default=[], title="データ")
