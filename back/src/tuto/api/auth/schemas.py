import re

from pydantic import BaseModel, Field, validator


class Me(BaseModel):
    id: int = Field(title="id")

    username: str = Field(title="ユーザ名")
    email: str = Field(title="Eメールアドレス")
    nickname: str = Field(title="ニックネーム")


class ForgotPasswordRequest(BaseModel):
    email: str = Field(
        ...,
        title="Email address",
        description="Email address",
        min_length=1,
        max_length=255,
    )

    @validator("email")
    def validate_email(cls, v):
        if not re.match(r"^[^@]+@[^@]+\.[^@]+$", v):
            raise ValueError("Please enter a valid email address")
        return v


class ForgotPasswordResponse(BaseModel):
    message: str = Field(..., title="Message", description="Response message")
    delivery: dict | None = Field(
        None, title="配信情報", description="コード配信の詳細情報"
    )
