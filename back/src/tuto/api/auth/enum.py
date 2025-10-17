from enum import Enum


class AuthMethod(str, Enum):
    PASSWORD = "password"
    COGNITO_EOTP = "cognito_eotp"