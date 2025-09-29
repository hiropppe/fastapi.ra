class AccessTokenExpirationError(Exception):
    pass


class InvalidAccessTokenError(Exception):
    pass


class AccessTokenRefreshError(Exception):
    pass


class ChangePasswordError(Exception):
    pass


class NotAuthorizedError(Exception):
    pass


class CodeMismatchError(Exception):
    pass


class AccessDeniedError(Exception):
    pass
