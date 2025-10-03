from typing import ClassVar

from sqlalchemy import Column
from sqlalchemy.dialects.mysql import BIGINT, TINYINT, VARCHAR
from sqlalchemy.orm import mapped_column
from sqlmodel import Field, SQLModel

from tuto.model import AuditMixin


class UserBase(SQLModel):
    username: str = Field(
        sa_column=Column(
            VARCHAR(50, collation="utf8mb4_bin"),
            index=True,
            unique=True,
            nullable=False,
            comment="ユーザ名",
        ),
    )
    email: str = Field(
        sa_column=Column(
            VARCHAR(255, collation="utf8mb4_bin"),
            nullable=False,
            index=True,
            unique=True,
            comment="Eメールアドレス",
        )
    )
    nickname: str = Field(
        sa_column=Column(VARCHAR(50), nullable=False, comment="ニックネーム")
    )

    is_active: bool = Field(
        default=True, sa_type=TINYINT, sa_column_kwargs={"comment": "アクティブ"}
    )


class UserRecord(SQLModel):
    id: int | None = Field(
        default=None,
        sa_column=Column(
            BIGINT(unsigned=True),
            default=None,
            primary_key=True,
            comment="ID",
            dialect_kwargs={"sort_order": -1},
        ),
    )

    hashed_password: str = Field(
        sa_column_kwargs={"comment": "ハッシュ化されたパスワード"}
    )


class User(AuditMixin, UserRecord, table=True):
    __tablename__: str = "user"
    __table_args__: ClassVar[dict] = {
        "comment": "ユーザ",
        "mysql_default_charset": "utf8mb4",
        "mysql_collate": "utf8mb4_general_ci",
    }


class UserCreate(UserBase):
    password: str = Field(min_length=8, max_length=128)
