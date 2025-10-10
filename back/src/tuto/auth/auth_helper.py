import base64
import gzip
import json
import logging
import os
import sys
from datetime import UTC, datetime, timedelta, timezone
from typing import Annotated, Any, cast

import jwt
from fastapi import Response
from fastapi.exceptions import HTTPException
from fastapi.openapi.models import OAuthFlows as OAuthFlowsModel
from fastapi.security import OAuth2
from passlib.context import CryptContext
from sqlalchemy import Result, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import Session
from starlette.requests import Request
from starlette.status import HTTP_401_UNAUTHORIZED

# TODO: import from typing when deprecating Python 3.9
from typing_extensions import Doc

logger = logging.getLogger(__name__)
formatter = logging.Formatter("%(levelname)s: %(asctime)s - %(message)s")
handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.INFO)
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.INFO)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# to get a string like this run:
# openssl rand -hex 32
SECRET_KEY = "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 12

SECURE_HTTP_ONLY_COOKIE = (
    os.environ.get("SECURE_HTTP_ONLY_COOKIE", "False").lower() == "true"
)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """パスワードの検証"""
    return pwd_context.verify(plain_password, hashed_password)


def hash_password(password: str) -> str:
    """パスワードをハッシュ化"""
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(UTC) + expires_delta
    else:
        expire = datetime.now(UTC) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def encode_cookie_data(data: dict[str, Any]) -> str:
    """複数の値を1つのCookieにエンコード"""
    json_str = json.dumps(data, separators=(",", ":"))
    compressed = gzip.compress(json_str.encode("utf-8"))
    return base64.b64encode(compressed).decode("utf-8")


def decode_cookie_data(cookie_value: str) -> dict[str, Any]:
    """エンコードされたCookieデータをデコード"""
    try:
        compressed = base64.b64decode(cookie_value.encode("utf-8"))
        json_str = gzip.decompress(compressed).decode("utf-8")
        return json.loads(json_str)
    except Exception:
        logger.exception("Failed to decode cookie data unexpectedly")
        return {}


class OAuth2PasswordOTPBearerUsingCookie(OAuth2):
    """
    OAuth2 flow for authentication using a bearer token obtained with a password.
    An instance of it would be used as a dependency.

    Read more about it in the
    [FastAPI docs for Simple OAuth2 with Password and Bearer](https://fastapi.tiangolo.com/tutorial/security/simple-oauth2/).
    """

    def __init__(
        self,
        tokenUrl: Annotated[
            str,
            Doc(
                """
                The URL to obtain the OAuth2 token. This would be the *path operation*
                that has `OAuth2PasswordRequestForm` as a dependency.
                """,
            ),
        ],
        scheme_name: Annotated[
            str | None,
            Doc(
                """
                Security scheme name.

                It will be included in the generated OpenAPI (e.g. visible at `/docs`).
                """,
            ),
        ] = None,
        scopes: Annotated[
            dict[str, str] | None,
            Doc(
                """
                The OAuth2 scopes that would be required by the *path operations* that
                use this dependency.
                """,
            ),
        ] = None,
        description: Annotated[
            str | None,
            Doc(
                """
                Security scheme description.

                It will be included in the generated OpenAPI (e.g. visible at `/docs`).
                """,
            ),
        ] = None,
        auto_error: Annotated[
            bool,
            Doc(
                """
                By default, if no HTTP Authorization header is provided, required for
                OAuth2 authentication, it will automatically cancel the request and
                send the client an error.

                If `auto_error` is set to `False`, when the HTTP Authorization header
                is not available, instead of erroring out, the dependency result will
                be `None`.

                This is useful when you want to have optional authentication.

                It is also useful when you want to have authentication that can be
                provided in one of multiple optional ways (for example, with OAuth2
                or in a cookie).
                """,
            ),
        ] = True,
    ):
        if not scopes:
            scopes = {}
        flows = OAuthFlowsModel(
            password=cast("Any", {"tokenUrl": tokenUrl, "scopes": scopes}),
        )
        super().__init__(
            flows=flows,
            scheme_name=scheme_name,
            description=description,
            auto_error=auto_error,
        )

    async def __call__(
        self, request: Request
    ) -> tuple[str, str | None, int, float] | None:
        auth_data: str | None = request.cookies.get("ad")
        if not auth_data:
            if self.auto_error:
                raise HTTPException(
                    status_code=HTTP_401_UNAUTHORIZED,
                    detail="Not authenticated",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            return None

        auth_dict: dict[str, Any] = decode_cookie_data(auth_data)
        if any(key not in auth_dict for key in ("at", "tt", "exp", "iss")):
            if self.auto_error:
                raise HTTPException(
                    status_code=HTTP_401_UNAUTHORIZED,
                    detail="Not authenticated",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            return None

        token_type: str = auth_dict["tt"]
        access_token: str = auth_dict["at"]
        refresh_token: str | None = auth_dict.get("rt")
        expires_in: int = int(auth_dict["exp"])
        token_issued_time: float = float(auth_dict["iss"])

        if token_type.lower() != "bearer":
            if self.auto_error:
                raise HTTPException(
                    status_code=HTTP_401_UNAUTHORIZED,
                    detail="Not authenticated",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            return None

        return access_token, refresh_token, expires_in, token_issued_time
