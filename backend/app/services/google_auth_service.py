"""
Google OAuth authentication service.

Verifies Google ID tokens and extracts user information.
Supports multiple client IDs (Web, iOS, Android).
"""
from typing import Optional, List
from dataclasses import dataclass

from google.oauth2 import id_token
from google.auth.transport import requests

from app.core.config import settings


@dataclass
class GoogleUserInfo:
    """User information extracted from Google ID token."""
    google_id: str
    email: str
    email_verified: bool
    first_name: str
    last_name: str
    avatar_url: Optional[str] = None


class GoogleAuthError(Exception):
    """Custom exception for Google auth errors."""
    pass


def get_allowed_client_ids() -> List[str]:
    """
    Get list of all configured Google Client IDs.

    Returns:
        List of valid client IDs (Web, iOS, Android, Firebase, etc.)
    """
    client_ids = []
    if settings.GOOGLE_CLIENT_ID:
        client_ids.append(settings.GOOGLE_CLIENT_ID)
    if settings.GOOGLE_CLIENT_ID_IOS:
        client_ids.append(settings.GOOGLE_CLIENT_ID_IOS)
    if settings.GOOGLE_CLIENT_ID_ANDROID:
        client_ids.append(settings.GOOGLE_CLIENT_ID_ANDROID)
    # Parse extra client IDs (comma-separated)
    if settings.GOOGLE_CLIENT_IDS_EXTRA:
        extra_ids = [cid.strip() for cid in settings.GOOGLE_CLIENT_IDS_EXTRA.split(",") if cid.strip()]
        client_ids.extend(extra_ids)
    return client_ids


class GoogleAuthService:
    """
    Service for Google OAuth authentication.

    Uses Google Identity Services to verify ID tokens issued by Google Sign-In.
    Supports multiple client IDs for web and mobile apps.
    """

    def __init__(self, client_id: Optional[str] = None):
        """
        Initialize Google Auth Service.

        Args:
            client_id: Specific Google OAuth Client ID to use, or None to accept any configured ID.
        """
        self.allowed_client_ids = get_allowed_client_ids()
        if not self.allowed_client_ids:
            raise GoogleAuthError("No GOOGLE_CLIENT_ID configured")

        # If specific client_id provided, use it; otherwise use first available
        self.primary_client_id = client_id if client_id in self.allowed_client_ids else self.allowed_client_ids[0]

    async def verify_token(self, token: str) -> GoogleUserInfo:
        """
        Verify Google ID token and extract user information.

        Tries to verify against all configured client IDs (Web, iOS, Android).

        Args:
            token: The ID token from Google Sign-In

        Returns:
            GoogleUserInfo object with user data

        Raises:
            GoogleAuthError: If token verification fails
        """
        last_error = None

        # Try each allowed client ID
        for client_id in self.allowed_client_ids:
            try:
                idinfo = id_token.verify_oauth2_token(
                    token,
                    requests.Request(),
                    client_id
                )

                # Verify issuer
                if idinfo['iss'] not in ['accounts.google.com', 'https://accounts.google.com']:
                    raise GoogleAuthError("Invalid token issuer")

                # Token verified successfully
                return GoogleUserInfo(
                    google_id=idinfo['sub'],
                    email=idinfo['email'],
                    email_verified=idinfo.get('email_verified', False),
                    first_name=idinfo.get('given_name', ''),
                    last_name=idinfo.get('family_name', ''),
                    avatar_url=idinfo.get('picture')
                )

            except ValueError as e:
                # Token doesn't match this client_id, try next
                last_error = e
                continue
            except Exception as e:
                last_error = e
                continue

        # None of the client IDs worked
        raise GoogleAuthError(f"Invalid token: {str(last_error)}")

    def verify_token_sync(self, token: str) -> GoogleUserInfo:
        """
        Synchronous version of verify_token.

        Tries to verify against all configured client IDs (Web, iOS, Android).

        Args:
            token: The ID token from Google Sign-In

        Returns:
            GoogleUserInfo object with user data
        """
        last_error = None

        for client_id in self.allowed_client_ids:
            try:
                idinfo = id_token.verify_oauth2_token(
                    token,
                    requests.Request(),
                    client_id
                )

                if idinfo['iss'] not in ['accounts.google.com', 'https://accounts.google.com']:
                    raise GoogleAuthError("Invalid token issuer")

                return GoogleUserInfo(
                    google_id=idinfo['sub'],
                    email=idinfo['email'],
                    email_verified=idinfo.get('email_verified', False),
                    first_name=idinfo.get('given_name', ''),
                    last_name=idinfo.get('family_name', ''),
                    avatar_url=idinfo.get('picture')
                )

            except ValueError as e:
                last_error = e
                continue
            except Exception as e:
                last_error = e
                continue

        raise GoogleAuthError(f"Invalid token: {str(last_error)}")
