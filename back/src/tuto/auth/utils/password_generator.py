import logging
import secrets
import string

from tuto.auth.exceptions import TemporaryPasswordGenerationError

logger = logging.getLogger(__name__)


def generate_temporary_password(length: int = 12) -> str:
    """
    Generate a secure temporary password that meets Cognito password policy requirements.

    Requirements:
    - At least 8 characters long
    - Contains at least one uppercase letter
    - Contains at least one lowercase letter
    - Contains at least one digit
    - Contains at least one special character

    :param length: Length of the password (minimum 8)
    :return: Generated temporary password
    :raises TemporaryPasswordGenerationError: If password generation fails
    """
    try:
        # Validate input
        if not isinstance(length, int):
            raise TemporaryPasswordGenerationError(
                f"Password length must be an integer, got {type(length).__name__}",
                error_code="INVALID_LENGTH_TYPE",
            )

        if length < 8:
            logger.warning(f"Password length {length} is less than minimum 8, using 8")
            length = 8

        if length > 256:
            raise TemporaryPasswordGenerationError(
                f"Password length {length} exceeds maximum allowed length of 256",
                error_code="LENGTH_TOO_LONG",
            )

        # Define character sets
        uppercase = string.ascii_uppercase
        lowercase = string.ascii_lowercase
        digits = string.digits
        special_chars = "!@#$%^&*()_+-=[]{}|;':\",./<>?"

        # Ensure at least one character from each required set
        password = [
            secrets.choice(uppercase),
            secrets.choice(lowercase),
            secrets.choice(digits),
            secrets.choice(special_chars),
        ]

        # Fill the rest with random characters from all sets
        all_chars = uppercase + lowercase + digits + special_chars
        for _ in range(length - 4):
            password.append(secrets.choice(all_chars))

        # Shuffle the password to randomize the order
        secrets.SystemRandom().shuffle(password)

        generated_password = "".join(password)

        # Validate generated password meets requirements
        if not _validate_password_policy(generated_password):
            raise TemporaryPasswordGenerationError(
                "Generated password does not meet policy requirements",
                error_code="POLICY_VALIDATION_FAILED",
            )

        logger.debug(
            f"Generated temporary password of length {len(generated_password)}"
        )
        return generated_password

    except TemporaryPasswordGenerationError:
        # Re-raise custom exceptions as-is
        raise
    except Exception as e:
        logger.error(f"Unexpected error generating temporary password: {e}")
        raise TemporaryPasswordGenerationError(
            f"Unexpected error during password generation: {e}",
            error_code="GENERATION_ERROR",
        )


def _validate_password_policy(password: str) -> bool:
    """
    Validate that password meets the required policy.

    :param password: Password to validate
    :return: True if password meets policy requirements
    """
    if len(password) < 8:
        return False

    has_upper = any(c.isupper() for c in password)
    has_lower = any(c.islower() for c in password)
    has_digit = any(c.isdigit() for c in password)
    has_special = any(c in "!@#$%^&*()_+-=[]{}|;':\",./<>?" for c in password)

    return has_upper and has_lower and has_digit and has_special
