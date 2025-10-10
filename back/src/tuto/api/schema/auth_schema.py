from pydantic import BaseModel, Field


class LoginUser(BaseModel):
    username: str = Field(title="ユーザ名")
    password: str = Field(title="パスワード")
    challenge_name: str = Field(title="チャレンジ名")


class AuthUser(BaseModel):
    id: int = Field(title="id")

    username: str = Field(title="ユーザ名")
    email: str = Field(title="Eメールアドレス")
    nickname: str = Field(title="ニックネーム")
