from typing import ClassVar

from sqlalchemy import Column
from sqlalchemy.dialects.mysql import TINYINT, VARCHAR
from sqlmodel import Field, SQLModel

from tuto.model import BigPrimaryKeyMixin, TimestampMixin


class UserBase(SQLModel):
    username: str = Field(
        sa_column=Column(
            VARCHAR(50, collation="utf8mb4_bin"),
            unique=True,
            nullable=False,
            comment="ユーザ名",
        ),
    )

    email: str = Field(
        sa_column=Column(
            VARCHAR(255, collation="utf8mb4_bin"),
            unique=True,
            nullable=False,
            comment="Eメールアドレス",
        ),
    )

    nickname: str = Field(
        sa_column=Column(VARCHAR(50), nullable=False, comment="ニックネーム")
    )

    is_active: bool = Field(
        default=True, sa_type=TINYINT, sa_column_kwargs={"comment": "アクティブ"}
    )

    hashed_password: str | None = Field(
        default=None, sa_column_kwargs={"comment": "ハッシュ化されたパスワード"}
    )


class User(TimestampMixin, UserBase, BigPrimaryKeyMixin, table=True):
    __tablename__: str = "user"
    __table_args__: ClassVar[dict] = {
        "comment": "ユーザ",
        "mysql_default_charset": "utf8mb4",
        "mysql_collate": "utf8mb4_general_ci",
    }

    model_config = {"from_attributes": True}


class NewUser(UserBase):
    """ユーザ作成用モデル"""

    password: str = Field(min_length=8, max_length=128)
