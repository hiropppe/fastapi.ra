from tuto.model.user import User
from tuto.service.auth_protocol import AuthProtocol
from tuto.service.impl.cognito_auth_service import CognitoAuthService
from tuto.service.impl.local_auth_service import LocalAuthService

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
