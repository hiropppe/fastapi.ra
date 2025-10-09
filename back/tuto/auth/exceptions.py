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


"""
Password reset specific exceptions
"""
from typing import Optional


class PasswordResetException(Exception):
    """Base exception for password reset operations"""

    def __init__(self, message: str, error_code: str = None, details: dict = None):
        super().__init__(message)
        self.message = message
        self.error_code = error_code or self.__class__.__name__
        self.details = details or {}


class TemporaryPasswordGenerationError(PasswordResetException):
    """Raised when temporary password generation fails"""

    pass


class EmailTemplateError(PasswordResetException):
    """Raised when email template rendering fails"""

    def __init__(self, message: str, template_name: str = None, **kwargs):
        super().__init__(message, **kwargs)
        self.template_name = template_name


class EmailDeliveryError(PasswordResetException):
    """Raised when email delivery fails"""

    def __init__(
        self,
        message: str,
        recipient_email: str = None,
        ses_error_code: str = None,
        **kwargs,
    ):
        super().__init__(message, **kwargs)
        self.recipient_email = recipient_email
        self.ses_error_code = ses_error_code


class CognitoPasswordResetError(PasswordResetException):
    """Raised when Cognito password reset operations fail"""

    def __init__(
        self,
        message: str,
        username: str = None,
        cognito_error_code: str = None,
        **kwargs,
    ):
        super().__init__(message, **kwargs)
        self.username = username
        self.cognito_error_code = cognito_error_code


class UserNotFoundError(CognitoPasswordResetError):
    """Raised when user is not found in Cognito"""

    pass


class PasswordPolicyError(CognitoPasswordResetError):
    """Raised when password doesn't meet policy requirements"""

    pass


class RateLimitExceededError(PasswordResetException):
    """Raised when password reset rate limit is exceeded"""

    def __init__(
        self,
        message: str,
        username: str = None,
        retry_after_seconds: int = None,
        **kwargs,
    ):
        super().__init__(message, **kwargs)
        self.username = username
        self.retry_after_seconds = retry_after_seconds


class InvalidRequestError(PasswordResetException):
    """Raised when request parameters are invalid"""

    def __init__(self, message: str, field_name: str = None, **kwargs):
        super().__init__(message, **kwargs)
        self.field_name = field_name


class SystemConfigurationError(PasswordResetException):
    """Raised when system configuration is invalid or missing"""

    def __init__(self, message: str, config_key: str = None, **kwargs):
        super().__init__(message, **kwargs)
        self.config_key = config_key
