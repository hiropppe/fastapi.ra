from enum import StrEnum


class AuthMethod(StrEnum):
    PASSWORD = "password"
    COGNITO_EOTP = "cognito_eotp"
