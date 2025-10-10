from tuto.service.auth_protocol import AuthProtocol
from tuto.service.impl.cognito_auth_service import CognitoAuthService
from tuto.service.impl.local_auth_service import LocalAuthService

from fastapi import Depends
from sqlmodel import Session

from tuto.datasource.database import get_session


def get_auth_service(
    username: str,
    session: Session = Depends(get_session),
) -> AuthProtocol:
    if username.endswith("@example.com"):
        return LocalAuthService(session)
    else:
        return CognitoAuthService()
