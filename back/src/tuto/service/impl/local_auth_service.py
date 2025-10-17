import logging
import time
from datetime import datetime, timedelta

import jwt
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from tuto.auth.auth_helper import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    ALGORITHM,
    SECRET_KEY,
    create_access_token,
    hash_password,
    verify_password,
)
from tuto.auth.exceptions import (
    AccessTokenRefreshError,
    EmailDeliveryError,
    EmailTemplateError,
    InvalidAccessTokenError,
    NotAuthorizedError,
    SystemConfigurationError,
    TemporaryPasswordGenerationError,
)
from tuto.auth.utils.email_sender import send_temporary_password_email
from tuto.auth.utils.password_generator import generate_temporary_password
from tuto.model.user import User
from tuto.repository.impl import user_repository
from tuto.service.auth_protocol import AuthProtocol, Challenge, Token, TokenData


logging.getLogger("passlib").setLevel(logging.ERROR)
logger = logging.getLogger(__name__)


class LocalAuthService(AuthProtocol):
    def __init__(self, asession: AsyncSession) -> None:
        super().__init__()
        self.asession: AsyncSession = asession

    async def signin(
        self,
        username: str,
        password: str,
        challenge_name: str = "",
    ) -> Token | Challenge:
        # Trim whitespace from inputs
        username = username.strip()
        password = password.strip()

        # Find user by username or email
        user: User | None = await user_repository.get_by_username_or_email(
            username, self.asession
        )
        if not user:
            msg = "Incorrect username or password"
            raise NotAuthorizedError(msg)

        # Verify password
        assert user.hashed_password is not None
        if not verify_password(password, user.hashed_password):
            msg = "Incorrect username or password"
            raise NotAuthorizedError(msg)

        # Check if password has expired
        if user.password_expires_at and datetime.utcnow() > user.password_expires_at:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Your temporary password has expired. Please try again to reset your password.",
            )

        # If user has temporary password, return NEW_PASSWORD_REQUIRED challenge
        if user.password_is_temporary:
            # Store session data for later use in respond_to_new_password_challenge
            session_data = {
                "username": username,
                "user_id": user.id,
                "challenge_type": "NEW_PASSWORD_REQUIRED",
            }
            # Create a simple session token for this challenge
            session_token = jwt.encode(session_data, SECRET_KEY, algorithm=ALGORITHM)

            return Challenge(
                challenge_name="NEW_PASSWORD_REQUIRED",
                username=username,
                session=session_token,
            )

        # Create access token for successful authentication
        access_token_expires: timedelta = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token: str = create_access_token(
            data={"sub": username}, expires_delta=access_token_expires
        )

        return Token(
            access_token=access_token,
            id_token=None,
            refresh_token=None,
            token_type="Bearer",
            expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            token_issued_time=time.time(),
        )

    async def respond_to_new_password_challenge(
        self,
        username: str,
        session: str,
        new_password: str,
    ) -> Token | Challenge:
        """
        Respond to NEW_PASSWORD_REQUIRED challenge for local users.
        Sets the new password and clears temporary password flags.

        :param username: The username
        :param session: Session token from the challenge
        :param new_password: The new password to set
        :return: Access token upon successful password change
        """
        try:
            # Trim whitespace from inputs
            username = username.strip()
            new_password = new_password.strip()
            # Decode session token to get user info
            try:
                session_data = jwt.decode(session, SECRET_KEY, algorithms=[ALGORITHM])
            except jwt.JWTError as e:
                logger.error(f"Invalid session token: {e}")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid session token",
                )

            # Validate session data
            if (
                session_data.get("username") != username
                or session_data.get("challenge_type") != "NEW_PASSWORD_REQUIRED"
            ):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid session data",
                )

            # Find user
            user: User | None = await user_repository.read_by_username_or_email(
                username, self.session
            )
            if not user or user.id != session_data.get("user_id"):
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found",
                )

            # Check if password has expired
            if (
                user.password_expires_at
                and datetime.utcnow() > user.password_expires_at
            ):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Your temporary password has expired. Please try again to reset your password.",
                )

            # Update password and clear temporary flags
            user.password = hash_password(new_password)
            user.password_is_temporary = False
            user.password_expires_at = None

            self.asession.add(user)
            await self.asession.commit()

            # Create access token for successful authentication
            access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
            access_token = create_access_token(
                data={"sub": user.username},
                expires_delta=access_token_expires,
            )

            return Token(
                access_token=access_token,
                id_token=None,
                refresh_token=None,
                token_type="Bearer",
                expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
                token_issued_time=time.time(),
            )

        except HTTPException:
            # Re-raise HTTP exceptions as-is
            raise
        except Exception as exc:
            logger.error(
                f"Unexpected error in respond_to_new_password_challenge: {exc}"
            )
            self.session.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to respond to new password challenge",
            ) from exc

    async def respond_to_email_otp_challenge(
        self,
        username: str,
        session: str,
        email_otp_code: str,
    ) -> Token:
        raise NotImplementedError

    async def refresh_token(
        self,
        access_token: str,
        refresh_token: str,
    ) -> Token:
        raise AccessTokenRefreshError("Token refresh is not supported for local users")

    async def discard_token(
        self,
        access_token: str,
        refresh_token: str,
    ) -> bool:
        return True

    async def get_token_info(
        self,
        access_token: str,
        expires_in: int = 3600,
        token_issued_time: float = 0,
    ) -> TokenData:
        try:
            payload = jwt.decode(access_token, SECRET_KEY, algorithms=[ALGORITHM])
        except Exception as e:
            msg = f"Token verification error: {e}"
            raise InvalidAccessTokenError(msg) from e
        username: str = payload.get("sub")
        if username is None:
            msg = "username is None"
            raise InvalidAccessTokenError(msg)
        return TokenData(username=username)

    async def change_password(
        self,
        access_token: str,
        old_password: str,
        new_password: str,
    ):
        raise NotImplementedError

    async def forget_password(
        self,
        username: str,
        email: str = "",
    ) -> dict:
        """
        Initiates the forgot password process for a local user.
        Sets a temporary password that forces the user to change it on next login.

        :param username: The username of the user who forgot their password.
        :param email: The email address of the user (required for security verification).
        :return: Information about the password reset process.
        """
        try:
            # Find user by username or email
            user: User | None = await user_repository.read_by_username_or_email(
                username, self.session
            )
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found",
                )

            # Verify that the provided email matches the user's email
            if email and user.email != email:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Email address does not match our records",
                )

            # Generate secure temporary password
            try:
                temporary_password = generate_temporary_password()
            except TemporaryPasswordGenerationError as e:
                logger.error(f"Failed to generate temporary password: {e}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to generate temporary password",
                ) from e

            # Set temporary password and expiration (24 hours from now)
            password_expiry = datetime.utcnow() + timedelta(hours=24)

            user.password = hash_password(temporary_password)
            user.password_is_temporary = True
            user.password_expires_at = password_expiry

            self.session.add(user)
            self.session.commit()

            # Send temporary password via email
            try:
                message_id = send_temporary_password_email(
                    user.email, username, temporary_password
                )
                masked_email = (
                    user.email[:2]
                    + "***@***"
                    + user.email[user.email.rfind(".") :]
                    if user.email
                    else "***@***.***"
                )

                return {
                    "message": "Temporary password set and sent via email",
                    "delivery": {
                        "Destination": masked_email,
                        "DeliveryMedium": "EMAIL",
                        "AttributeName": "email",
                        "MessageId": message_id,
                    },
                }

            except (
                EmailTemplateError,
                EmailDeliveryError,
                SystemConfigurationError,
            ) as e:
                logger.error(f"Failed to send temporary password email: {e}")
                # Rollback database changes if email fails
                self.session.rollback()
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to send temporary password email",
                ) from e

        except HTTPException:
            # Re-raise HTTP exceptions as-is
            raise
        except Exception as exc:
            logger.error(f"Unexpected error in forgot_password: {exc}")
            self.session.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to process forgot password request",
            ) from exc
