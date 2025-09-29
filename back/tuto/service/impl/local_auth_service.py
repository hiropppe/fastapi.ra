import time
from datetime import timedelta

import jwt
from sqlmodel import Session

from tuto.auth.auth_helper import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    ALGORITHM,
    SECRET_KEY,
    create_access_token,
)
from tuto.auth.exceptions import InvalidAccessTokenError
from tuto.service.auth_protocol import AuthProtocol, Challenge, Token, TokenData


class LocalAuthService(AuthProtocol):
    def __init__(self, session: Session) -> None:
        super().__init__()
        self.session: Session = session

    async def signin(
        self,
        username: str,
        password: str,
        challenge_name: str = "",
    ) -> Token | Challenge:
        # Create access token for successful authentication
        access_token_expires: timedelta = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token: str = create_access_token(
            data={"sub": username}, expires_delta=access_token_expires
        )

        return Token(
            access_token=access_token,
            id_token=None,
            refresh_token=None,
            token_type="Bearer",
            expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            token_issued_time=time.time(),
        )

    async def respond_to_new_password_challenge(
        self,
        username: str,
        session: str,
        new_password: str,
    ):
        raise NotImplementedError

    async def respond_to_email_otp_challenge(
        self,
        username: str,
        session: str,
        email_otp_code: str,
    ):
        raise NotImplementedError

    async def refresh_token(
        self,
        access_token: str,
        refresh_token: str,
    ):
        raise NotImplementedError

    async def discard_token(
        self,
        access_token: str,
        refresh_token: str,
    ):
        raise NotImplementedError

    async def get_token_info(
        self,
        access_token: str,
        expires_in: int = 3600,
        token_issued_time: float = 0,
    ) -> TokenData:
        try:
            payload = jwt.decode(access_token, SECRET_KEY, algorithms=[ALGORITHM])
        except Exception as e:
            msg = f"Token verification error: {e}"
            raise InvalidAccessTokenError(msg) from e
        username: str = payload.get("sub")
        if username is None:
            msg = "username is None"
            raise InvalidAccessTokenError(msg)
        return TokenData(username=username)

    async def change_password(
        self,
        access_token: str,
        old_password: str,
        new_password: str,
    ):
        raise NotImplementedError

    async def forget_password(
        self,
        username: str,
        email: str = "",
    ):
        raise NotImplementedError
