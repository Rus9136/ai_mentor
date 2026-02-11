"""
Apple Sign In authentication service.

Verifies Apple identity tokens and extracts user information.
Supports iOS app and web client IDs.
"""
from typing import Optional, List
from dataclasses import dataclass
import time

import httpx
from jose import jwt, jwk
from jose.exceptions import JWTError, JWKError

from app.core.config import settings


@dataclass
class AppleUserInfo:
    """User information extracted from Apple identity token."""
    apple_id: str  # 'sub' claim - unique Apple user ID
    email: Optional[str]  # May be hidden/private relay
    email_verified: bool
    first_name: Optional[str] = None
    last_name: Optional[str] = None


class AppleAuthError(Exception):
    """Custom exception for Apple auth errors."""
    pass


# Cache for Apple public keys (JWK)
_apple_keys_cache: dict = {"keys": None, "fetched_at": 0}
KEYS_CACHE_TTL = 3600  # 1 hour


async def get_apple_public_keys() -> List[dict]:
    """
    Fetch Apple's public keys for JWT verification.

    Keys are cached for 1 hour to reduce API calls.
    URL: https://appleid.apple.com/auth/keys

    Returns:
        List of JWK key dictionaries
    """
    current_time = time.time()

    if (
        _apple_keys_cache["keys"] is not None
        and current_time - _apple_keys_cache["fetched_at"] < KEYS_CACHE_TTL
    ):
        return _apple_keys_cache["keys"]

    async with httpx.AsyncClient() as client:
        response = await client.get(
            "https://appleid.apple.com/auth/keys",
            timeout=10.0
        )
        response.raise_for_status()
        data = response.json()

    _apple_keys_cache["keys"] = data["keys"]
    _apple_keys_cache["fetched_at"] = current_time

    return data["keys"]


def get_allowed_apple_client_ids() -> List[str]:
    """
    Get list of all configured Apple Client IDs.

    Returns:
        List of valid client IDs (Bundle ID, Web Service ID)
    """
    client_ids = []
    if settings.APPLE_CLIENT_ID:
        client_ids.append(settings.APPLE_CLIENT_ID)
    if settings.APPLE_CLIENT_ID_WEB:
        client_ids.append(settings.APPLE_CLIENT_ID_WEB)
    return client_ids


class AppleAuthService:
    """
    Service for Apple Sign In authentication.

    Verifies Apple identity tokens using Apple's public keys.
    Supports both iOS app and web client IDs.
    """

    def __init__(self, client_id: Optional[str] = None):
        """
        Initialize Apple Auth Service.

        Args:
            client_id: Specific Apple Client ID to use, or None to accept any configured ID.
        """
        self.allowed_client_ids = get_allowed_apple_client_ids()
        if not self.allowed_client_ids:
            raise AppleAuthError("No APPLE_CLIENT_ID configured")

        self.primary_client_id = (
            client_id
            if client_id in self.allowed_client_ids
            else self.allowed_client_ids[0]
        )

    async def verify_token(
        self,
        identity_token: str,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
    ) -> AppleUserInfo:
        """
        Verify Apple identity token and extract user information.

        Args:
            identity_token: The identity_token from Apple Sign In
            first_name: Optional first name (Apple provides only on first sign-in)
            last_name: Optional last name (Apple provides only on first sign-in)

        Returns:
            AppleUserInfo object with user data

        Raises:
            AppleAuthError: If token verification fails
        """
        try:
            # Get Apple's public keys
            apple_keys = await get_apple_public_keys()

            # Decode header to get key ID
            unverified_header = jwt.get_unverified_header(identity_token)
            kid = unverified_header.get("kid")

            if not kid:
                raise AppleAuthError("Token missing 'kid' in header")

            # Find matching key
            matching_key = None
            for key_dict in apple_keys:
                if key_dict.get("kid") == kid:
                    matching_key = key_dict
                    break

            if not matching_key:
                raise AppleAuthError("No matching public key found")

            # Convert JWK to public key
            public_key = jwk.construct(matching_key)

            # Try each allowed client ID
            last_error = None
            for client_id in self.allowed_client_ids:
                try:
                    payload = jwt.decode(
                        identity_token,
                        public_key,
                        algorithms=["RS256"],
                        audience=client_id,
                        issuer="https://appleid.apple.com",
                    )

                    # Token verified successfully
                    return AppleUserInfo(
                        apple_id=payload["sub"],
                        email=payload.get("email"),
                        email_verified=payload.get("email_verified", False),
                        first_name=first_name,
                        last_name=last_name,
                    )

                except JWTError as e:
                    last_error = e
                    continue

            raise AppleAuthError(f"Token verification failed: {last_error}")

        except httpx.HTTPError as e:
            raise AppleAuthError(f"Failed to fetch Apple public keys: {e}")
        except JWKError as e:
            raise AppleAuthError(f"Invalid public key format: {e}")
        except AppleAuthError:
            raise
        except Exception as e:
            raise AppleAuthError(f"Token verification failed: {e}")
