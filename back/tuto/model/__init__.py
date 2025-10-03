from datetime import datetime
from sqlmodel import Field, SQLModel

from tuto.utils.datetime_utils import jstnow


class AuditMixin(SQLModel):
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


from .user import User
