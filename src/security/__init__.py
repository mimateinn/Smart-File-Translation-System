"""Local-only secrets and official-API host checks. No website-login paths."""

from .hosts import (
    HostNotAllowed,
    assert_public_https_url,
    is_official_api_host,
    official_api_hosts,
)
from .secrets import load_secret, mask_secret, redact_secrets, save_secret_to_env

__all__ = [
    "HostNotAllowed",
    "assert_public_https_url",
    "is_official_api_host",
    "official_api_hosts",
    "load_secret",
    "mask_secret",
    "redact_secrets",
    "save_secret_to_env",
]
