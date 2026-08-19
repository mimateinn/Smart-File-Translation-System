"""Official OAuth only: PKCE + state. Hosts must pass the same API allowlist."""

from __future__ import annotations

import base64
import hashlib
import secrets
from urllib.parse import urlencode, urlparse

from .hosts import HostNotAllowed, assert_public_https_url


def _b64url(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")


def make_pkce_pair() -> tuple[str, str]:
    verifier = _b64url(secrets.token_bytes(32))
    challenge = _b64url(hashlib.sha256(verifier.encode("ascii")).digest())
    return verifier, challenge


def make_state() -> str:
    return _b64url(secrets.token_bytes(24))


def official_authorize_url(
    authorize_url: str,
    client_id: str,
    redirect_uri: str,
    state: str,
    challenge: str,
    scope: str = "",
) -> str:
    """
    Build an authorize URL. The authorize host must already be allowlisted.
    Redirect must be this machine (localhost / 127.0.0.1) only.
    """
    if not (client_id or "").strip():
        raise HostNotAllowed("OAuth client id is missing.")
    checked = assert_public_https_url(authorize_url)
    redirect = urlparse(redirect_uri)
    if redirect.hostname not in {"127.0.0.1", "localhost"}:
        raise HostNotAllowed("OAuth redirect must be local.")
    q = {
        "response_type": "code",
        "client_id": client_id.strip(),
        "redirect_uri": redirect_uri,
        "state": state,
        "code_challenge": challenge,
        "code_challenge_method": "S256",
    }
    if scope:
        q["scope"] = scope
    sep = "&" if urlparse(checked).query else "?"
    return checked + sep + urlencode(q)


def official_token_url(token_url: str) -> str:
    return assert_public_https_url(token_url)
