import base64
import hmac
import os
from hashlib import sha256
from datetime import datetime


class TokenUtil:
    """
    Utility for generating and verifying URL-safe access tokens with embedded expiry
    secured by HMAC-SHA256 signature.

    Token format: <random>.<exp_epoch_sec>.<sig_b64url>
    - random: arbitrary URL-safe string component
    - exp_epoch_sec: integer epoch seconds (UTC)
    - sig_b64url: base64url(HMAC_SHA256(secret, random + "." + exp)) without padding
    """

    @staticmethod
    def _secret_key() -> bytes:
        key = os.getenv("ACCESS_TOKEN_SECRET", "change-me")
        return key.encode("utf-8")

    @staticmethod
    def _refresh_secret_key() -> bytes:
        key = os.getenv("REFRESH_TOKEN_SECRET", "change-me-refresh")
        return key.encode("utf-8")

    @staticmethod
    def _b64url_no_pad(data: bytes) -> str:
        return base64.urlsafe_b64encode(data).decode("ascii").rstrip("=")

    @staticmethod
    def _sign(payload: str) -> str:
        mac = hmac.new(TokenUtil._secret_key(), payload.encode("utf-8"), sha256)
        return TokenUtil._b64url_no_pad(mac.digest())

    @staticmethod
    def _sign_refresh(payload: str) -> str:
        mac = hmac.new(TokenUtil._refresh_secret_key(), payload.encode("utf-8"), sha256)
        return TokenUtil._b64url_no_pad(mac.digest())

    @staticmethod
    def generate_access_token(random_part: str, expires_at: datetime, company_id: int) -> str:
        """
        Create a signed, URL-safe token with embedded expiry.

        Args:
            random_part: URL-safe random string component (e.g., secrets.token_urlsafe(..))
            expires_at: timezone-aware datetime in UTC when token expires
            company_id: optional company identifier to embed in the token payload

        Returns:
            str: token string
        """
        exp = int(expires_at.timestamp())
        payload = f"{random_part}.{company_id}.{exp}"
        sig = TokenUtil._sign(payload)
        return f"{payload}.{sig}"

    @staticmethod
    def generate_refresh_token(random_part: str, expires_at: datetime, company_id: int) -> str:
        """
        Create a signed, URL-safe refresh token with embedded expiry.

        Token format mirrors access token but uses a distinct secret.
        """
        exp = int(expires_at.timestamp())
        payload = f"{random_part}.{company_id}.{exp}"
        sig = TokenUtil._sign_refresh(payload)
        return f"{payload}.{sig}"

    @staticmethod
    def verify_access_token(token: str) -> tuple[bool, int | None]:
        """
        Verify token signature and return embedded expiry epoch seconds.

        Returns:
            (is_valid, exp_epoch_seconds)
        """
        try:
            parts = token.split(".")
            if len(parts) == 3:
                random_part, exp_str, sig = parts
                payload = f"{random_part}.{exp_str}"
            elif len(parts) == 4:
                random_part, company_id_str, exp_str, sig = parts
                payload = f"{random_part}.{company_id_str}.{exp_str}"
            else:
                return False, None
            # Basic format checks
            if not exp_str.isdigit():
                return False, None
            expected_sig = TokenUtil._sign(payload)
            if not hmac.compare_digest(sig, expected_sig):
                return False, None
            return True, int(exp_str)
        except Exception:
            return False, None

    @staticmethod
    def verify_refresh_token(token: str) -> tuple[bool, int | None]:
        """
        Verify refresh token signature and return embedded expiry epoch seconds.

        Returns:
            (is_valid, exp_epoch_seconds)
        """
        try:
            parts = token.split(".")
            if len(parts) != 4:
                return False, None
            random_part, company_id_str, exp_str, sig = parts
            if not exp_str.isdigit() or not company_id_str.isdigit():
                return False, None
            payload = f"{random_part}.{company_id_str}.{exp_str}"
            expected_sig = TokenUtil._sign_refresh(payload)
            if not hmac.compare_digest(sig, expected_sig):
                return False, None
            return True, int(exp_str)
        except Exception:
            return False, None

    @staticmethod
    def extract_company_id(token: str) -> int:
        """
        Extract embedded company_id from a token if present.
        Returns None for legacy 3-part tokens without company_id.
        """
        try:
            parts = token.split(".")
            if len(parts) == 4:
                _, company_id_str, _, _ = parts
                if company_id_str.isdigit():
                    return int(company_id_str)
            raise None
        except Exception:
            return None
