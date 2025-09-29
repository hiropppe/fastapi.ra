import logging
import sys
import time
from logging import INFO, StreamHandler, getLogger
from typing import Any

import requests

logger = getLogger(__name__)
formatter = logging.Formatter("%(levelname)s: %(asctime)s - %(message)s")
handler = StreamHandler(sys.stdout)
handler.setLevel(INFO)
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(INFO)


class CognitoTokenManager:
    """AWS Cognito token management class"""

    def __init__(
            self,
            cognito_idp_client: Any,
            user_pool_id: str,
            client_id: str,
            region: str
        ) -> None:
        self.cognito_idp_client: Any = cognito_idp_client
        self.user_pool_id: str = user_pool_id
        self.client_id: str = client_id
        self.region: str = region
        self.jwks_url: str = f"https://cognito-idp.{self.region}.amazonaws.com/{self.user_pool_id}/.well-known/jwks.json"
        self._jwks: dict | None = None
        self._jwks_cache: dict | None = None
        self._jwks_cache_time: float = 0

    def get_jwks(self) -> dict:
        """Get JWKS keys (JSON Web Key Set) with caching functionality"""
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
