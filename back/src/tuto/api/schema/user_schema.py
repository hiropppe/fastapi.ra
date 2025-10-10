from pydantic import BaseModel


class UserSchema(BaseModel):
    id: int
    username: str
    email: str
    nickname: str
    is_active: bool

    model_config = {"from_attributes": True}
