from tuto.core.user.models import User
from .protocol import AuthProtocol
from .cognito_protocol import CognitoAuthService
from .local_protocol import LocalAuthService

from sqlmodel import select

from sqlalchemy.ext.asyncio import AsyncSession


async def get_auth_service(
    username: str,
    asession: AsyncSession,
) -> AuthProtocol:
    user: User | None = await asession.scalar(
        select(User).where(User.username == username)
    )
    if user is None:
        raise ValueError(f"User with username {username} not found")
    if user.auth_method == "cognito_eotp":
        return CognitoAuthService()
    return LocalAuthService(asession)
