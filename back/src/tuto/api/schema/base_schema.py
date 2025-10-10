from typing import Generic, TypeVar
from pydantic import BaseModel, Field

T = TypeVar("T")


class ResponseBase(BaseModel):
    status_code: str = Field(default="SUCCESS", title="ステータスコード")
    error_type: str | None = Field(default=None, title="")
    error_code: str | None = Field(default=None, title="")
    message: str | None = Field(default=None, title="")


class ListResponse(ResponseBase, Generic[T]):
    data: list[T] = Field(default=[], title="データ")
