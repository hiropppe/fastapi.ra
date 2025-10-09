import logging
import sys
import time
from logging import INFO, StreamHandler, getLogger

import requests
from auth.exceptions import (
    AccessTokenExpirationError,
    AccessTokenRefreshError,
    InvalidAccessTokenError,
    NotAuthorizedError,
)
from botocore.exceptions import ClientError
from jose import JWTError, jwt

logger = getLogger(__name__)
formatter = logging.Formatter("%(levelname)s: %(asctime)s - %(message)s")
handler = StreamHandler(sys.stdout)
handler.setLevel(INFO)
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(INFO)


class CognitoTokenManager:
    """AWS Cognito token management class"""

    def __init__(self, cognito_idp_client, user_pool_id, client_id, region):
        self.cognito_idp_client = cognito_idp_client
        self.user_pool_id = user_pool_id
        self.client_id = client_id
        self.region = region
        self.jwks_url = f"https://cognito-idp.{region}.amazonaws.com/{user_pool_id}/.well-known/jwks.json"
        self._jwks_cache = None
        self._jwks_cache_time = 0

    def get_jwks(self):
        """Get JWKS keys (with caching functionality)"""
        current_time = time.time()
        # Cache for 1 hour
        if self._jwks_cache is None or current_time - self._jwks_cache_time > 3600:
            try:
                response = requests.get(self.jwks_url, timeout=10)
                response.raise_for_status()
                self._jwks_cache = response.json()
                self._jwks_cache_time = current_time
            except requests.RequestException as e:
                logger.error(f"Failed to retrieve JWKS: {e}")
                raise
        return self._jwks_cache

    def verify_token(self, access_token, verify_signature=True):
        """
        Verify Access Token

        :param access_token: Access Token to verify
        :param verify_signature: Whether to perform signature verification
        :return: Claims if token is valid, None if invalid
        """
        try:
            if verify_signature:
                # Perform signature verification using JWKS
                jwks = self.get_jwks()

                # Get token header and check kid
                unverified_header = jwt.get_unverified_header(access_token)
                kid = unverified_header.get("kid")

                # Find corresponding JWK
                jwk = None
                for key in jwks["keys"]:
                    if key["kid"] == kid:
                        jwk = key
                        break

                if not jwk:
                    raise JWTError("Corresponding JWK not found")

                # Verify and decode token
                claims = jwt.decode(
                    access_token,
                    jwk,
                    algorithms=["RS256"],
                    audience=self.client_id,
                    issuer=f"https://cognito-idp.{self.region}.amazonaws.com/{self.user_pool_id}",
                )
            else:
                # Decode without signature verification (for development/testing)
                claims = jwt.get_unverified_claims(access_token)

            # Check expiration time
            current_time = int(time.time())
            if claims.get("exp", 0) < current_time:
                logger.error("Access Token has expired")
                raise AccessTokenExpirationError("Access Token has expired")

            # Check if token_use is 'access'
            if claims.get("token_use") != "access":
                logger.error("This is not an Access Token")
                raise InvalidAccessTokenError("This is not an Access Token")

            logger.info(
                f"Access Token verification successful: user={claims.get('username')}"
            )
            return claims

        except JWTError as e:
            logger.error(f"Token verification error: {e}")
            raise InvalidAccessTokenError(f"Token verification error: {e}")
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            raise InvalidAccessTokenError(f"Unexpected error: {e}")

    def refresh_tokens(self, refresh_token, client_secret=None):
        """
        Update Access Token using Refresh Token

        :param refresh_token: Refresh token
        :param client_secret: Client secret (if required)
        :return: New token information
        """
        try:
            kwargs = {
                "ClientId": self.client_id,
                "AuthFlow": "REFRESH_TOKEN_AUTH",
                "AuthParameters": {"REFRESH_TOKEN": refresh_token},
            }

            # If client secret is required
            if client_secret:
                import base64
                import hashlib
                import hmac

                # For refresh token, use refresh token instead of username
                message = refresh_token + self.client_id
                secret_hash = base64.b64encode(
                    hmac.new(
                        client_secret.encode(),
                        message.encode(),
                        digestmod=hashlib.sha256,
                    ).digest()
                ).decode()
                kwargs["AuthParameters"]["SECRET_HASH"] = secret_hash

            response = self.cognito_idp_client.initiate_auth(**kwargs)

            auth_result = response.get("AuthenticationResult")
            if auth_result:
                logger.info("Token refresh successful")
                return {
                    "AccessToken": auth_result["AccessToken"],
                    "IdToken": auth_result.get("IdToken"),
                    "TokenType": auth_result["TokenType"],
                    "ExpiresIn": auth_result["ExpiresIn"],
                }
            else:
                logger.error("Could not retrieve authentication result")
                raise AccessTokenRefreshError(
                    "Could not retrieve authentication result"
                )

        except ClientError as err:
            error_code = err.response["Error"]["Code"]
            if error_code == "NotAuthorizedException":
                logger.error("Refresh Token is invalid or expired")
                raise AccessTokenRefreshError("Refresh Token is invalid or expired")
            else:
                logger.error(f"Token refresh error: {error_code}")
                raise AccessTokenRefreshError(f"Token refresh error: {error_code}")
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            raise AccessTokenRefreshError(f"Unexpected error: {e}")

    def global_sign_out(self, access_token):
        """
        Global sign out (sign out from all devices)

        :param access_token: Access token
        :return: True if sign out successful
        """
        try:
            self.cognito_idp_client.global_sign_out(AccessToken=access_token)
            logger.info("Global sign out successful")
            return True

        except ClientError as err:
            error_code = err.response["Error"]["Code"]
            if error_code == "NotAuthorizedException":
                logger.error("Access Token is invalid")
            else:
                logger.error(f"Sign out error: {error_code}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return False

    def revoke_token(self, refresh_token, client_secret=None):
        """
        Revoke (invalidate) Refresh Token

        :param refresh_token: Refresh token to revoke
        :param client_secret: Client secret (if required)
        :return: True if revocation successful
        """
        try:
            kwargs = {"ClientId": self.client_id, "Token": refresh_token}

            # If client secret is required
            if client_secret:
                import base64
                import hashlib
                import hmac

                message = refresh_token + self.client_id
                secret_hash = base64.b64encode(
                    hmac.new(
                        client_secret.encode(),
                        message.encode(),
                        digestmod=hashlib.sha256,
                    ).digest()
                ).decode()
                kwargs["ClientSecret"] = client_secret
                kwargs["SecretHash"] = secret_hash

            self.cognito_idp_client.revoke_token(**kwargs)
            logger.info("Token revocation successful")
            return True

        except ClientError as err:
            logger.error(f"Token revocation error: {err.response['Error']['Code']}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return False


class AuthenticationSession:
    """Authentication session management class"""

    def __init__(self, token_manager, auth_tokens):
        self.token_manager = token_manager
        self.access_token = auth_tokens.get("AccessToken")
        self.id_token = auth_tokens.get("IdToken")
        self.refresh_token = auth_tokens.get("RefreshToken")
        self.token_type = auth_tokens.get("TokenType", "Bearer")
        self.expires_in = auth_tokens.get("ExpiresIn", 3600)
        self.token_issued_time = auth_tokens.get("TokenIssuedTime", time.time())

    def validate_token(self):
        """Validate Access Token"""
        if not self.access_token:
            raise InvalidAccessTokenError("Access Token is empty")

        # Simple time-based check (consider expired 5 minutes early for safety)
        elapsed_time = time.time() - self.token_issued_time
        if elapsed_time >= (self.expires_in - 300):  # 5 minutes buffer
            raise AccessTokenExpirationError("Access Token is approaching expiration")

        # Actual token verification
        self.token_manager.verify_token(self.access_token)

    def is_valid_token(self) -> bool:
        """Check if Access Token has expired or not"""
        try:
            self.validate_token()
        except AccessTokenExpirationError as exc:
            return False
        else:
            return True

    def refresh(self, client_secret=None):
        """Refresh token"""
        logger.info("Refreshing Access Token")
        new_tokens = self.token_manager.refresh_tokens(
            self.refresh_token, client_secret
        )

        if new_tokens:
            self.access_token = new_tokens["AccessToken"]
            self.id_token = new_tokens.get("IdToken")
            self.expires_in = new_tokens["ExpiresIn"]
            self.token_issued_time = time.time()
            logger.info("Token refresh completed")
            return True
        else:
            logger.error("Token refresh failed")
            return False

    def refresh_if_needed(self, client_secret=None):
        """Refresh token if needed"""
        if not self.is_valid_token() and self.refresh_token:
            return self.refresh()
        return False

    def get_authorization_header(self):
        """Get value for Authorization header"""
        if self.access_token:
            return f"{self.token_type} {self.access_token}"
        return None

    def sign_out(self):
        """Execute sign out"""
        success = True

        # Global sign out
        if self.access_token:
            if not self.token_manager.global_sign_out(self.access_token):
                success = False

        # Revoke refresh token
        if self.refresh_token:
            if not self.token_manager.revoke_token(self.refresh_token):
                success = False

        # Clear local tokens
        self.access_token = None
        self.id_token = None
        self.refresh_token = None

        return success

    def change_password(self, previous_password: str, proposed_password: str):
        """Changes the password for the currently signed-in user"""
        try:
            kwargs = {
                "PreviousPassword": previous_password,
                "ProposedPassword": proposed_password,
                "AccessToken": self.access_token,
            }
            self.token_manager.cognito_idp_client.change_password(**kwargs)
            logger.info("Change password successful")
            return True
        except ClientError as err:
            logger.error(
                f"Password change failed: {err.response['Error']['Code']} - {err!s}"
            )
            raise NotAuthorizedError(
                f"Password change failed: {err.response['Error']['Message']}"
            ) from err
        except Exception as e:
            logger.error(f"Password change failed unexpectedly: {e}")
            raise NotAuthorizedError(
                f"Password change failed unexpectedly: {e!s}"
            ) from e


# Usage example
def demo_post_authentication_flow():
    """Demo of post-authentication flow"""
    import boto3

    # Configuration
    REGION = "us-east-1"  # Change to your region
    USER_POOL_ID = "us-east-1_XXXXXXXXX"  # Change to your User Pool ID
    CLIENT_ID = "your-client-id"  # Change to your Client ID

    cognito_client = boto3.client("cognito-idp", region_name=REGION)
    token_manager = CognitoTokenManager(cognito_client, USER_POOL_ID, CLIENT_ID, REGION)

    # Assume authenticated tokens are available
    auth_tokens = {
        "AccessToken": "your-access-token",
        "IdToken": "your-id-token",
        "RefreshToken": "your-refresh-token",
        "TokenType": "Bearer",
        "ExpiresIn": 3600,
    }

    # Create session
    session = AuthenticationSession(token_manager, auth_tokens)

    # 1. Token verification
    print("=== Token Verification ===")
    if session.is_valid_token():
        print("✓ Access Token is valid")

        # Example of API call requiring authentication
        auth_header = session.get_authorization_header()
        print(f"Authorization Header: {auth_header}")
    else:
        print("✗ Access Token is invalid")

    # 2. Token refresh
    print("\n=== Token Refresh ===")
    if session.is_valid_token():
        print("✓ Token is up to date")
    else:
        print("✗ Token refresh failed")

    # 3. Sign out
    print("\n=== Sign Out ===")
    if session.sign_out():
        print("✓ Sign out successful")
    else:
        print("✗ Some errors occurred during sign out")


if __name__ == "__main__":
    import logging

    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    demo_post_authentication_flow()
