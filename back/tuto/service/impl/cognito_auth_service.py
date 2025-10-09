import logging
import os
import time

import boto3
from asyncpg import CaseNotFoundError
from fastapi import HTTPException, status

from tuto.auth.cognito_idp_action import CognitoIdentityProviderWrapper
from tuto.auth.cognito_token_manager import AuthenticationSession, CognitoTokenManager
from tuto.auth.exceptions import (
    CodeMismatchError,
    CognitoPasswordResetError,
    EmailDeliveryError,
    EmailTemplateError,
    InvalidAccessTokenError,
    NotAuthorizedError,
    SystemConfigurationError,
    TemporaryPasswordGenerationError,
    UserNotFoundError,
)
from tuto.service.auth_protocol import AuthProtocol, Challenge, Token, TokenData

logger = logging.getLogger(__name__)

COGNITO_USER_POOL_ID = os.environ["AWS_COGNITO_USER_POOL_ID"]
COGNITO_CLIENT_ID = os.environ["AWS_COGNITO_CLIENT_ID"]
REGION_NAME = os.environ.get("AWS_DEFAULT_REGION", "ap-northeast-1")

cognito_idp_client = boto3.client("cognito-idp", region_name=REGION_NAME)

cog_wrapper = CognitoIdentityProviderWrapper(
    cognito_idp_client,
    COGNITO_USER_POOL_ID,
    COGNITO_CLIENT_ID,
)
token_manager = CognitoTokenManager(
    cognito_idp_client,
    COGNITO_USER_POOL_ID,
    COGNITO_CLIENT_ID,
    REGION_NAME,
)


class CognitoAuthService(AuthProtocol):
    def __init__(self) -> None:
        super().__init__()
        self.cog_wrapper = cog_wrapper
        self.token_manager = token_manager

    async def signin(
        self,
        username: str,
        password: str,
        challenge_name: str = "",
    ) -> Token | Challenge:
        try:
            auth_session: AuthenticationSession = self.cog_wrapper.initiate_auth(
                username, password
            )
        except self.cog_wrapper.client.exceptions.UserNotFoundException:
            raise CaseNotFoundError("User not found")
        except self.cog_wrapper.client.exceptions.NotAuthorizedException:
            raise NotAuthorizedError("Incorrect username or password")
        except Exception as e:
            logger.error(f"Unexpected error during sign-in: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error",
            )

        if (
            auth_session.challenge_name == "NEW_PASSWORD_REQUIRED"
            or auth_session.challenge_name == "SMS_MFA"
            or auth_session.challenge_name == "SOFTWARE_TOKEN_MFA"
        ):
            return Challenge(
                challenge_name=auth_session.challenge_name,
                username=username,
                session=auth_session.session,
            )
        elif auth_session.challenge_name is None:
            tokens = self.token_manager.decode_tokens(
                auth_session.authentication_result
            )
            return Token(
                access_token=tokens["access_token"],
                id_token=tokens.get("id_token"),
                refresh_token=tokens.get("refresh_token"),
                token_type=auth_session.authentication_result.get(
                    "TokenType", "Bearer"
                ),
                expires_in=auth_session.authentication_result.get("ExpiresIn", 3600),
                token_issued_time=time.time(),
            )
        else:
            logger.error(f"Unsupported challenge: {auth_session.challenge_name}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported challenge: {auth_session.challenge_name}",
            )

    async def respond_to_new_password_challenge(
        self,
        username: str,
        session: str,
        new_password: str,
    ) -> Token | Challenge:
        # Trim whitespace from inputs
        username = username.strip()
        new_password = new_password.strip()

        response = respond_to_require_new_password(username, session, new_password)

        if "AuthenticationResult" in response:
            auth_tokens: dict = response["AuthenticationResult"]
            return Token(
                access_token=auth_tokens["AccessToken"],
                id_token=auth_tokens["IdToken"],
                refresh_token=auth_tokens["RefreshToken"],
                token_type=auth_tokens.get("TokenType", "Bearer"),
                expires_in=auth_tokens.get("ExpiresIn", 3600),
                token_issued_time=time.time(),
            )

        next_challenge_name: str = response["ChallengeName"]
        if next_challenge_name == "EMAIL_OTP":
            return Challenge(
                challenge_name=next_challenge_name,
                username=username,
                session=response["Session"],
            )

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Unexpected challenge {next_challenge_name}",
            headers={"WWW-Authenticate": "Bearer"},
        )

    async def respond_to_email_otp_challenge(
        self,
        username: str,
        session: str,
        email_otp_code: str,
    ) -> Token:
        # Trim whitespace from inputs
        username = username.strip()
        email_otp_code = email_otp_code.strip()

        auth_tokens: dict = verify_mfa_code(username, session, email_otp_code)
        return Token(
            access_token=auth_tokens["AccessToken"],
            id_token=auth_tokens["IdToken"],
            refresh_token=auth_tokens["RefreshToken"],
            token_type=auth_tokens.get("TokenType", "Bearer"),
            expires_in=auth_tokens.get("ExpiresIn", 3600),
            token_issued_time=time.time(),
        )

    async def refresh_token(
        self,
        access_token: str,
        refresh_token: str,
    ) -> Token:
        auth_tokens = {
            "AccessToken": access_token,
            "RefreshToken": refresh_token,
        }

        session = AuthenticationSession(token_manager, auth_tokens)
        session.refresh()

        return Token(
            access_token=session.access_token,
            id_token=session.access_token,
            refresh_token=session.refresh_token,
            token_type=session.token_type,
            expires_in=session.expires_in,
            token_issued_time=session.token_issued_time,
        )

    async def discard_token(
        self,
        access_token: str,
        refresh_token: str,
    ) -> bool:
        auth_tokens = {
            "AccessToken": access_token,
            "RefreshToken": refresh_token,
        }

        session = AuthenticationSession(token_manager, auth_tokens)
        return session.sign_out()

    async def get_token_info(
        self,
        access_token: str,
        expires_in: int = 3600,
        token_issued_time: float = 0,
    ) -> TokenData:
        auth_tokens = {
            "AccessToken": access_token,
            "ExpiresIn": expires_in,
            "TokenIssuedTime": token_issued_time if token_issued_time else time.time(),
        }

        session = AuthenticationSession(token_manager, auth_tokens)
        # Run lightweight token validation
        session.validate_token()
        # Also perform detailed verification
        claims = token_manager.verify_token(session.access_token, verify_signature=True)
        username = claims.get("username")
        if username is None:
            msg = "username is None"
            raise InvalidAccessTokenError(msg)
        return TokenData(username=username)

    async def change_password(
        self,
        access_token: str,
        old_password: str,
        new_password: str,
    ) -> None:
        # Trim whitespace from passwords
        old_password = old_password.strip()
        new_password = new_password.strip()

        auth_tokens = {
            "AccessToken": access_token,
        }
        session = AuthenticationSession(token_manager, auth_tokens)
        session.change_password(old_password, new_password)

    async def forgot_password(self, username: str, email: str = None) -> dict:
        """
        Initiates the forgot password process for a user using admin-set-user-password.
        This method sets a temporary password that forces the user to change it on next login.

        :param username: The username of the user who forgot their password.
        :param email: The email address of the user (required for security verification).
        :return: Information about the password reset process.
        """
        try:
            from auth.utils.email_sender import send_temporary_password_email
            from auth.utils.password_generator import generate_temporary_password

            # Generate secure temporary password
            try:
                temporary_password = generate_temporary_password()
            except TemporaryPasswordGenerationError as e:
                logger.error(f"Failed to generate temporary password: {e}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="一時パスワードの生成に失敗しました",
                ) from e

            # Set temporary password for the user (permanent=False forces password change)
            try:
                cog_wrapper.admin_set_user_password(
                    username, temporary_password, permanent=False
                )
            except cognito_idp_client.exceptions.UserNotFoundException as e:
                logger.warning(f"User not found during password set: {username}")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="ユーザーが見つかりません",
                ) from e
            except Exception as e:
                logger.error(f"Failed to set temporary password for {username}: {e}")
                raise CognitoPasswordResetError(
                    f"Failed to set temporary password: {e}",
                    username=username,
                    error_code="PASSWORD_SET_FAILED",
                )

            # Get user's email address for sending temporary password
            try:
                user_info = cognito_idp_client.admin_get_user(
                    UserPoolId=cog_wrapper.user_pool_id,
                    Username=username,
                )

                user_email = None
                for attr in user_info.get("UserAttributes", []):
                    if attr["Name"] == "email":
                        user_email = attr["Value"]
                        break

                if not user_email:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="ユーザーのメールアドレスが見つかりません",
                    )

                # Verify that the provided email matches the user's email
                if email and user_email != email:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="ユーザー名またはメールアドレスが一致しません",
                    )

                # Send temporary password via email
                try:
                    message_id = send_temporary_password_email(
                        user_email, username, temporary_password
                    )
                    masked_email = (
                        user_email[:2] + "***@***" + user_email[user_email.rfind(".") :]
                        if user_email
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
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail="一時パスワードのメール送信に失敗しました",
                    ) from e

            except cognito_idp_client.exceptions.UserNotFoundException:
                # This should be caught by the outer handler, but adding here for safety
                raise UserNotFoundError(
                    f"User {username} not found",
                    username=username,
                    error_code="USER_NOT_FOUND",
                )
            except HTTPException:
                # Re-raise HTTP exceptions as-is
                raise
            except Exception as e:
                logger.error(f"Failed to get user info for {username}: {e}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="パスワードリセット処理に失敗しました",
                ) from e

        except HTTPException:
            # Re-raise HTTP exceptions as-is
            raise
        except cognito_idp_client.exceptions.UserNotFoundException as exc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="ユーザーが見つかりません",
            ) from exc
        except cognito_idp_client.exceptions.LimitExceededException as exc:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="リクエスト回数が制限を超えています。しばらく時間をおいてから再度お試しください。",
            ) from exc
        except cognito_idp_client.exceptions.InvalidParameterException as exc:
            logger.error(f"Invalid parameter for password reset: {exc}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="リクエストパラメータが無効です",
            ) from exc
        except (CognitoPasswordResetError, TemporaryPasswordGenerationError) as exc:
            logger.error(f"Password reset error: {exc}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="パスワードリセット処理に失敗しました",
            ) from exc

    async def create_cognito_user(
        self, username: str, email: str, temporary_password: str
    ) -> dict:
        """
        Creates a new user in the Cognito User Pool.

        :param username: The username for the new user.
        :param email: The email address for the new user.
        :param temporary_password: The temporary password for the new user.
        :return: Information about the created user.
        """
        try:
            response = cog_wrapper.admin_create_user(
                user_name=username,
                email=email,
                temporary_password=temporary_password,
                send_invitation=False,  # Don't send invitation message
            )

            return {
                "username": username,
                "email": email,
                "user_status": response.get("User", {}).get(
                    "UserStatus", "FORCE_CHANGE_PASSWORD"
                ),
                "created": True,
            }

        except cognito_idp_client.exceptions.UsernameExistsException as e:
            logger.warning(f"User already exists in Cognito: {username}")
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="ユーザー名は既に使用されています",
            ) from e
        except cognito_idp_client.exceptions.InvalidParameterException as e:
            logger.error(f"Invalid parameter for user creation: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="ユーザー作成パラメータが無効です",
            ) from e
        except Exception as e:
            logger.error(f"Failed to create Cognito user {username}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Cognitoユーザー作成に失敗しました",
            ) from e

    async def update_cognito_user(
        self,
        username: str,
        email: str = None,
        password: str = None,
        password_is_temporary: bool = True,
    ) -> dict:
        """
        Updates a user in the Cognito User Pool.

        :param username: The username of the user to update.
        :param email: The new email address for the user (optional).
        :param password: The new password for the user (optional).
        :param password_is_temporary: Whether the password is temporary (used when password is provided).
        :return: Information about the updated user.
        """
        try:
            updated_attributes = []

            # Update email if provided
            if email:
                cog_wrapper.admin_update_user_attributes(
                    user_name=username,
                    user_attributes={
                        "email": email,
                        "email_verified": "true",
                    },
                )
                updated_attributes.append("email")

            # Update password if provided
            if password:
                # Permanent = not password_is_temporary
                permanent = not password_is_temporary
                cog_wrapper.admin_set_user_password(
                    user_name=username,
                    password=password,
                    permanent=permanent,
                )
                updated_attributes.append("password")

            return {
                "username": username,
                "updated_attributes": updated_attributes,
                "updated": True,
            }

        except cognito_idp_client.exceptions.UserNotFoundException as e:
            logger.warning(f"User not found in Cognito: {username}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Cognitoユーザーが見つかりません",
            ) from e
        except cognito_idp_client.exceptions.InvalidParameterException as e:
            logger.error(f"Invalid parameter for user update: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="ユーザー更新パラメータが無効です",
            ) from e
        except Exception as e:
            logger.error(f"Failed to update Cognito user {username}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Cognitoユーザー更新に失敗しました",
            ) from e

    async def delete_cognito_user(self, username: str) -> dict:
        """
        Deletes a user from the Cognito User Pool.

        :param username: The username of the user to delete.
        :return: Information about the deleted user.
        """
        try:
            cog_wrapper.admin_delete_user(user_name=username)

            return {
                "username": username,
                "deleted": True,
            }

        except cognito_idp_client.exceptions.UserNotFoundException as e:
            logger.warning(f"User not found in Cognito: {username}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Cognitoユーザーが見つかりません",
            ) from e
        except Exception as e:
            logger.error(f"Failed to delete Cognito user {username}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Cognitoユーザー削除に失敗しました",
            ) from e


def start_sign_in(username: str, password: str) -> dict:
    try:
        response = cog_wrapper.start_sign_in(username, password)
    except cognito_idp_client.exceptions.NotAuthorizedException as exc:
        raise NotAuthorizedError(exc.response["Error"]["Message"]) from exc
    else:
        return response


def verify_mfa_code(username: str, session: str, email_otp_code: str) -> dict:
    try:
        response: dict = cog_wrapper.respond_to_email_otp_challenge(
            username,
            session,
            email_otp_code,
        )
    except cognito_idp_client.exceptions.CodeMismatchException as exc:
        raise CodeMismatchError(exc.response["Error"]["Message"]) from exc
    except cognito_idp_client.exceptions.NotAuthorizedException as exc:
        raise NotAuthorizedError(exc.response["Error"]["Message"]) from exc
    return response


def respond_to_require_new_password(username: str, session: str, new_password: str):
    try:
        response = cog_wrapper.respond_to_new_password_challenge(
            username,
            session,
            new_password,
        )
    except cognito_idp_client.exceptions.NotAuthorizedException as exc:
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"{exc.response['Error']['Code']}: {exc.response['Error']['Message']}",
            headers={"WWW-Authenticate": "Bearer"},
        )
        raise credentials_exception
    else:
        return response
