from datetime import datetime
from sqlalchemy import Column
from sqlalchemy.dialects.mysql import BIGINT
from sqlmodel import Field, SQLModel

from tuto.utils.datetime_utils import jstnow


class TimestampMixin(SQLModel):
    created_at: datetime = Field(
        default_factory=jstnow, sa_column_kwargs={"comment": "作成日時"}
    )
    updated_at: datetime = Field(
        default_factory=jstnow,
        sa_column_kwargs={"comment": "更新日時", "onupdate": jstnow},
    )
    deleted_at: datetime | None = Field(
        default=None, sa_column_kwargs={"comment": "削除日時"}
    )


class BigPrimaryKeyMixin(SQLModel):
    id: int | None = Field(
        default=None,
        sa_column=Column(
            BIGINT(unsigned=True),
            default=None,
            primary_key=True,
            comment="ID",
        ),
    )


from .user import User
