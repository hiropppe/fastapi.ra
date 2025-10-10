from pydantic import BaseModel, Field


class Me(BaseModel):
    id: int = Field(title="id")

    username: str = Field(title="ユーザ名")
    email: str = Field(title="Eメールアドレス")
    nickname: str = Field(title="ニックネーム")
