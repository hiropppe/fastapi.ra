from datetime import datetime
from typing import ClassVar

from sqlalchemy import Column
from sqlalchemy.dialects.mysql import DATETIME, TINYINT, VARCHAR
from sqlmodel import Field, SQLModel

from tuto.core.models import BigPrimaryKeyMixin, TimestampMixin


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

    auth_method: str = Field(
        sa_column=Column(VARCHAR(50), nullable=False, comment="認証方式")
    )

    # Password reset fields
    password_is_temporary: bool = Field(
        default=False,
        sa_type=TINYINT,
        sa_column_kwargs={"comment": "一時パスワードフラグ"},
    )
    password_expires_at: datetime | None = Field(
        default=None,
        sa_column=Column(DATETIME, nullable=True, comment="パスワード有効期限"),
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
