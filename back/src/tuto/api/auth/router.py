import logging
import sys
from typing import Annotated, Any

from fastapi import APIRouter, Cookie, Depends, HTTPException, Request, Response, status
from fastapi.security import OAuth2PasswordBearer
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from src.tuto.api.auth.enum import AuthMethod
from tuto.api.auth.schemas import ForgotPasswordRequest, ForgotPasswordResponse
from tuto.api.schema.auth_schema import Me
from tuto.auth.auth_helper import (
    SECURE_HTTP_ONLY_COOKIE,
    OAuth2PasswordOTPBearerUsingCookie,
    decode_cookie_data,
    encode_cookie_data,
    get_token_source,
)
from tuto.auth.exceptions import CodeMismatchError, NotAuthorizedError
from tuto.auth.ip_restriction import verify_ip_access
from tuto.datasource.database import get_async_session
from tuto.model.user import User
from tuto.repository.impl import user_repository
from tuto.service import get_auth_service
from tuto.service.auth_protocol import (
    AuthProtocol,
    Challenge,
    Logedin,
    Token,
    TokenData,
)
from tuto.service.impl.cognito_auth_service import CognitoAuthService
from tuto.service.impl.local_auth_service import LocalAuthService

logger = logging.getLogger(__name__)
formatter = logging.Formatter("%(levelname)s: %(asctime)s - %(message)s")
handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.INFO)
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.INFO)

router = APIRouter()

# 1. Standard OAuth2 with Bearer token
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")
# 2. OAuth2 with Bearer token stored in HttpOnly Cookie
# oauth2_scheme = OAuth2PasswordOTPBearerUsingCookie(tokenUrl="/auth/token")

MAX_AUTH_SESSION_AGE = 24 * 60 * 60  # 1 day
MAX_AUTH_COOKIE_AGE_MARGIN = 60 * 60 * 24 * 30  # 30 days


async def get_current_me(
    token: str | tuple[str, str | None, int, int] = Depends(oauth2_scheme),
    asession: AsyncSession = Depends(get_async_session),
) -> Me:
    if isinstance(oauth2_scheme, OAuth2PasswordOTPBearerUsingCookie):
        access_token: str = token[0]
        expires_in: int = token[2]
        token_issued_time: float = token[3]
    else:
        access_token: str = token
        expires_in = 0
        token_issued_time = 0

    auth_service: AuthProtocol = get_auth_service_by_token(access_token, asession)

    token_data: TokenData = await auth_service.get_token_info(
        access_token, expires_in, token_issued_time
    )
    api_user: Me = await get_me(token_data.username, asession)

    if api_user is None:
        msg = f"There is no user named {token_data.username} (from token verification) in database"
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=msg,
            headers={"WWW-Authenticate": "Bearer"},
        )

    return api_user


@router.get(
    "/users/me",
    summary="",
    description="",
    response_model=Me,
    response_description="",
    response_model_exclude_none=True,
)
async def read_users_me(
    request: Request,
    current_user: Me = Depends(get_current_me),
) -> Me:
    verify_ip_access(request, current_user.username)
    return current_user


@router.post("/token")
async def login_for_access_token(
    request: Request,
    response: Response,
    asession: AsyncSession = Depends(get_async_session),
) -> Token | Logedin | Challenge:
    form_data = await request.form()
    username: str = form_data["username"]
    password: str = form_data["password"]
    challenge_name: str = form_data.get("challenge_name", "ADMIN_USER_PASSWORD_AUTH")

    auth_service: AuthProtocol = await get_auth_service(username, asession)
    token_or_challenge: Token | Challenge = await auth_service.signin(
        username, password, challenge_name
    )

    # Set auth data in HttpOnly Cookie if using OAuth2PasswordOTPBearerUsingCookie
    if isinstance(oauth2_scheme, OAuth2PasswordOTPBearerUsingCookie):
        loggedin_or_challenge: Logedin | Challenge = set_auth_data_in_http_only_cookie(
            response, token_or_challenge
        )
        return loggedin_or_challenge
    else:
        return token_or_challenge


@router.post("/verify_totp")
async def verify_totp(
    request: Request,
    response: Response,
    ad: Annotated[str, Cookie()],
) -> Logedin:
    auth_dict: dict[str, Any] = decode_cookie_data(ad)
    username: str = auth_dict["user"]
    session: str = auth_dict["sess"]

    form_data = await request.form()
    email_otp_code: str = form_data["mfa_code"]  # type: ignore
    auth_service: AuthProtocol = CognitoAuthService()
    try:
        token: Token = await auth_service.respond_to_email_otp_challenge(
            username, session, email_otp_code
        )
        cookies = {
            "at": token.access_token,
            "rt": token.refresh_token,
            "tt": token.token_type,
            "exp": str(token.expires_in),
            "iss": str(token.token_issued_time),
        }
        max_age = token.expires_in * 60  # Convert minutes to seconds
        max_age += 60 * 60 * 24 * 7 # Set mergin for cookie expiration
        set_auth_cookie(response, cookies, max_age=max_age)
    except (CodeMismatchError, NotAuthorizedError) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)
        ) from exc
    else:
        return Logedin(
            exp=token.expires_in,
            iss=token.token_issued_time,
            rtk=True,
        )


@router.post("/refresh_token")
async def refresh_token(
    token: Annotated[tuple[str, str | None, int, int], Depends(oauth2_scheme)],
    response: Response,
    asession: AsyncSession = Depends(get_async_session),
) -> Logedin:
    access_token: str = token[0]
    refresh_token: str | None = token[1]
    auth_service: AuthProtocol = get_auth_service_by_token(access_token, asession)
    refreshed_token: Token = await auth_service.refersh_token(access_token, refresh_token) # type: ignore
    cookies = {
        "at": refreshed_token.access_token,
        "rt": refreshed_token.refresh_token,
        "tt": refreshed_token.token_type,
        "exp": str(refreshed_token.expires_in),
        "iss": str(refreshed_token.token_issued_time),
    }
    max_age = refreshed_token.expires_in * 60  # Convert minutes to seconds
    max_age += 60 * 60 * 24 * 7 # Set mergin for cookie expiration
    set_auth_cookie(response, cookies, max_age=max_age)
    return Logedin(
        exp=refreshed_token.expires_in,
        iss=refreshed_token.token_issued_time,
        rtk=True,
    )


@router.post("/discard_token")
async def discard_token(
    token: Annotated[tuple[str, str | None, int, int], Depends(oauth2_scheme)],
    asession: AsyncSession = Depends(get_async_session),
) -> JSONResponse:
    access_token: str = token[0]
    refresh_token: str | None = token[1]
    auth_service: AuthProtocol = get_auth_service_by_token(access_token, asession)
    success = await auth_service.discard_token(access_token, refresh_token) # type: ignore

    json_response = JSONResponse(
        content=jsonable_encoder({
            "success": success,
            "message": "Token successfully discarded" if success else "Failed to discard token - please clear local storage",
        }),
    )

    delete_auth_cookie(json_response)

    return json_response


@router.post("/set_new_password")
async def set_new_password(
    request: Request,
    response: Response,
    ad: Annotated[str, Cookie()],
    asession: AsyncSession = Depends(get_async_session),
) -> Logedin | Challenge:
    auth_dict: dict[str, Any] = decode_cookie_data(ad)
    username: str = auth_dict["user"]
    auth_session: str = auth_dict["sess"]

    form_data = await request.form()
    new_password: str = form_data["new_password"]

    auth_service = get_auth_service(username, asession)
    token_or_challenge: Token | Challenge = await auth_service.respond_to_new_password_challenge(username, auth_session, new_password)

    loggedin_or_challenge: Logedin | Challenge = set_auth_data_in_http_only_cookie(response, token_or_challenge)
    return loggedin_or_challenge


@router.post("/change_password")
async def change_password(
    token: Annotated[tuple[str, str | None, int, int], Depends(oauth2_scheme)],
    request: Request,
    asession: AsyncSession = Depends(get_async_session),
) -> JSONResponse:
    access_token: str = token[0]
    refresh_token: str | None = token[1]

    form_data = await request.form()
    previous_password: str = form_data["old_password"] # type: ignore
    proposed_password: str = form_data["new_password"] # type: ignore

    auth_service: AuthProtocol = get_auth_service_by_token(access_token, asession)
    try:
        await auth_service.change_password(access_token, previous_password, proposed_password)
    except NotAuthorizedError:
        token_info: Token = await auth_service.refersh_token(access_token, refresh_token) # type: ignore
        await auth_service.change_password(token_info.access_token, previous_password, proposed_password)

    return JSONResponse(
        content=jsonable_encoder({
            "success": True,
            "message": "Password successfully changed",
        }),
    )


@router.post("/forgot_password", response_model=ForgotPasswordResponse)
async def forgot_password(
    request_data: ForgotPasswordRequest,
    asession: AsyncSession = Depends(get_async_session),
) -> ForgotPasswordResponse:
    user: User | None = await user_repository.get_by_username_or_email(request_data.email, asession)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Mail address not found",
        )

    auth_service: AuthProtocol = CognitoAuthService() if user.auth_method == AuthMethod.COGNITO_EOTP else LocalAuthService(asession)

    try:
        result = await auth_service.forgot_password(user.username, request_data.email)
        return ForgotPasswordResponse(
            message=result["message"],
            delivery=result.get("delivery"),
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"Unexpected error in forgot_password: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error occurred",
        ) from exc


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


def get_auth_service_by_token(token: str, session: AsyncSession) -> AuthProtocol:
    issuer = get_token_source(token)
    if issuer == "cognito":
        return CognitoAuthService()
    return LocalAuthService(session)


async def get_me(username: str, asession: AsyncSession) -> Me:
    user: User | None = await user_repository.get_by_username_or_email(
        username, asession
    )
    assert user is not None
    assert user.id is not None
    return Me(
        username=user.username, id=user.id, nickname=user.nickname, email=user.email
    )


def set_auth_cookie(response: Response, token_data: dict, max_age: int) -> None:
    """Set authentication data in HttpOnly cookie"""
    encoded_data = encode_cookie_data(token_data)
    response.set_cookie(
        key="ad",
        value=encoded_data,
        max_age=max_age,
        httponly=True,
        secure=SECURE_HTTP_ONLY_COOKIE,
        samesite="lax",
        path="/",
    )


def delete_auth_cookie(response: Response) -> None:
    response.delete_cookie(
        key="ad",
        httponly=True,
        secure=SECURE_HTTP_ONLY_COOKIE,
        samesite="lax",
        path="/",
    )
