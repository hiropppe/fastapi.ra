from typing import Protocol

from fastapi import Depends
from pydantic import BaseModel
from sqlmodel import Session

from tuto.datasource.database import get_session
from tuto.service.impl.cognito_auth_service import CognitoAuthService
from tuto.service.impl.local_auth_service import LocalAuthService


class Token(BaseModel):
    access_token: str
    id_token: str | None
    refresh_token: str | None
    token_type: str
    expires_in: int
    token_issued_time: float


class Logedin(BaseModel):
    exp: int
    iss: float
    rtk: bool


class Challenge(BaseModel):
    challenge_name: str
    username: str
    session: str


class TokenData(BaseModel):
    username: str


class AuthProtocol(Protocol):
    """Authentication Protocol Interface"""

    async def signin(
        self, username: str, password: str, challenge_name: str
    ) -> Token | Challenge: ...

    async def respond_to_new_password_challenge(
        self,
        username: str,
        session: str,
        new_password: str,
    ) -> Token | Challenge: ...

    async def respond_to_email_otp_challenge(
        self,
        username: str,
        session: str,
        email_otp_code: str,
    ) -> Token: ...

    async def refresh_token(self, access_token: str, refresh_token: str) -> Token: ...

    async def discard_token(
        self,
        access_token: str,
        refresh_token: str,
    ) -> bool: ...

    async def get_token_info(
        self,
        access_token: str,
        expires_in: int = 3600,
        token_issued_time: float = 0,
    ) -> TokenData: ...

    async def change_password(
        self,
        access_token: str,
        old_password: str,
        new_password: str,
    ) -> None: ...


def get_auth_service(
    username: str,
    session: Session = Depends(get_session),
) -> AuthProtocol:
    if username.endswith("@example.com"):
        return LocalAuthService(session)
    else:
        return CognitoAuthService()
