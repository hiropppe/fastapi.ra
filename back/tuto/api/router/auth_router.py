import os
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlmodel import Session

from tuto.api.schema.auth_schema import AuthUser, LoginUser
from tuto.auth.auth_helper import (
    SECURE_HTTP_ONLY_COOKIE,
    OAuth2PasswordOTPBearerUsingCookie,
    encode_cookie_data,
)
from tuto.auth.ip_restriction import is_password_reset_restricted, verify_ip_access
from tuto.datasource.database import get_session
from tuto.service.auth_protocol import (
    AuthProtocol,
    Challenge,
    Logedin,
    Token,
    TokenData,
)
from tuto.service.impl.local_auth_service import LocalAuthService

router = APIRouter()

oauth2_scheme = OAuth2PasswordOTPBearerUsingCookie(tokenUrl="/auth/token")

MAX_AUTH_SESSION_AGE = 24 * 60 * 60  # 1 day
MAX_AUTH_COOKIE_AGE_MARGIN = 60 * 60 * 24 * 30  # 30 days


async def get_current_user(
    token: tuple[str, str | None, int, int] = Depends(oauth2_scheme),
    session: Session = Depends(get_session),
) -> AuthUser:
    access_token: str = token[0]
    expires_in: int = token[2]
    token_issued_time: float = token[3]

    auth_service: AuthProtocol = LocalAuthService(session)

    token_data: TokenData = await auth_service.get_token_info(
        access_token, expires_in, token_issued_time
    )
    api_user: AuthUser = get_user(token_data.username, session)

    if api_user is None:
        msg = f"There is no user named {token_data.username} (from token verification) in database"
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=msg,
            headers={"WWW-Authenticate": "Bearer"},
        )

    return api_user


@router.get("/check_password_reset_availability")
async def check_password_reset_availability(
    request: Request,
) -> dict:
    """
    クライアントIPからパスワードリセット機能の利用可否を確認
    メールアドレス未設定の取引先IPの場合はパスワードリセット機能を利用不可とする
    """
    is_restricted = await is_password_reset_restricted(request)

    if is_restricted:
        return {
            "password_reset_available": False,
            "reason": "お客様の環境ではパスワードリセット機能をご利用いただけません。パスワードを忘れた場合はお問い合わせください。",
        }

    return {
        "password_reset_available": True,
        "reason": None,
    }


@router.post("/token")
async def login_for_access_token(
    # login_user: LoginUser,
    request: Request,
    response: Response,
    session: Session = Depends(get_session),
) -> Logedin | Challenge:
    form_data = await request.form()
    username: str = form_data["username"]
    password: str = form_data["password"]
    challenge_name: str = form_data["challenge_name"]

    # username: str = login_user.username
    # password: str = login_user.password
    # challenge_name: str = login_user.challenge_name

    auth_service: AuthProtocol = LocalAuthService(session)
    token_or_challenge: Token | Challenge = await auth_service.signin(
        username, password, challenge_name
    )
    loggedin_or_challenge: Logedin | Challenge = set_auth_data_in_http_only_cookie(
        response, token_or_challenge
    )
    return loggedin_or_challenge


@router.get(
    "/users/me",
    summary="",
    description="",
    response_model=AuthUser,
    response_description="",
    response_model_exclude_none=True,
)
async def read_users_me(
    request: Request,
    current_user: AuthUser = Depends(get_current_user),
) -> AuthUser:
    await verify_ip_access(request, current_user.username)
    return current_user


def set_auth_data_in_http_only_cookie(
    response: Response, token_or_challenge: Token | Challenge
) -> Logedin | Challenge:
    response_data: Logedin | Challenge
    if isinstance(token_or_challenge, Token):
        token: Token = token_or_challenge
        max_cookie_age: int = token.expires_in * 60
        max_cookie_age += MAX_AUTH_COOKIE_AGE_MARGIN

        cookies = {
            "at": token.access_token,
            "tt": token.token_type,
            "exp": str(token.expires_in),
            "iss": str(token.token_issued_time),
        }

        set_auth_cookie(response, cookies, max_cookie_age)

        response_data = Logedin(
            exp=token.expires_in,
            iss=token.token_issued_time,
            rtk=False,
        )
    else:
        challenge: Challenge = token_or_challenge

        cookies = {
            "user": challenge.username,
            "sess": challenge.session,
        }

        set_auth_cookie(response, cookies, MAX_AUTH_SESSION_AGE)

        response_data = challenge

    return response_data


def set_auth_cookie(response: Response, token_data: dict, max_age: int) -> None:
    """認証情報を1つのCookieに設定"""
    encoded_data = encode_cookie_data(token_data)
    response.set_cookie(
        key="ad",
        value=encoded_data,
        max_age=max_age,
        httponly=True,
        secure=SECURE_HTTP_ONLY_COOKIE,  # 本番 (https) のみ True
        samesite="lax",
        path="/",
    )


def get_user(username: str, session: Session) -> AuthUser:
    return AuthUser(
        username=username, id=1, nickname=username, email=f"{username}@test.com"
    )
