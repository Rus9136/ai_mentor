"""
Google OAuth authentication service.

Verifies Google ID tokens and extracts user information.
"""
from typing import Optional
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


class GoogleAuthService:
    """
    Service for Google OAuth authentication.

    Uses Google Identity Services to verify ID tokens issued by Google Sign-In.
    """

    def __init__(self, client_id: Optional[str] = None):
        """
        Initialize Google Auth Service.

        Args:
            client_id: Google OAuth Client ID. Uses settings.GOOGLE_CLIENT_ID if not provided.
        """
        self.client_id = client_id or settings.GOOGLE_CLIENT_ID
        if not self.client_id:
            raise GoogleAuthError("GOOGLE_CLIENT_ID is not configured")

    async def verify_token(self, token: str) -> GoogleUserInfo:
        """
        Verify Google ID token and extract user information.

        Args:
            token: The ID token from Google Sign-In

        Returns:
            GoogleUserInfo object with user data

        Raises:
            GoogleAuthError: If token verification fails
        """
        try:
            # Verify the token with Google
            idinfo = id_token.verify_oauth2_token(
                token,
                requests.Request(),
                self.client_id
            )

            # Verify issuer
            if idinfo['iss'] not in ['accounts.google.com', 'https://accounts.google.com']:
                raise GoogleAuthError("Invalid token issuer")

            # Verify audience (client_id)
            if idinfo.get('aud') != self.client_id:
                # Also check mobile client ID if configured
                if settings.GOOGLE_CLIENT_ID_MOBILE:
                    if idinfo.get('aud') != settings.GOOGLE_CLIENT_ID_MOBILE:
                        raise GoogleAuthError("Token was not issued for this application")
                else:
                    raise GoogleAuthError("Token was not issued for this application")

            # Extract user info
            return GoogleUserInfo(
                google_id=idinfo['sub'],
                email=idinfo['email'],
                email_verified=idinfo.get('email_verified', False),
                first_name=idinfo.get('given_name', ''),
                last_name=idinfo.get('family_name', ''),
                avatar_url=idinfo.get('picture')
            )

        except ValueError as e:
            # Invalid token format or signature
            raise GoogleAuthError(f"Invalid token: {str(e)}")
        except Exception as e:
            raise GoogleAuthError(f"Token verification failed: {str(e)}")

    def verify_token_sync(self, token: str) -> GoogleUserInfo:
        """
        Synchronous version of verify_token.

        Note: The google-auth library is synchronous, so this is actually
        the same as the async version but without await.

        Args:
            token: The ID token from Google Sign-In

        Returns:
            GoogleUserInfo object with user data
        """
        try:
            idinfo = id_token.verify_oauth2_token(
                token,
                requests.Request(),
                self.client_id
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
            raise GoogleAuthError(f"Invalid token: {str(e)}")
        except Exception as e:
            raise GoogleAuthError(f"Token verification failed: {str(e)}")
