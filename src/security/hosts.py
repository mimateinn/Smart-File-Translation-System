"""HTTPS + host allowlist for official developer APIs only."""

from __future__ import annotations

import ipaddress
import os
import socket
from urllib.parse import urlparse

# Official developer API hosts (not consumer chat websites).
_OFFICIAL_HOSTS = frozenset(
    {
        "api.openai.com",
        "api.anthropic.com",
        "generativelanguage.googleapis.com",
        "api.groq.com",
        "api.deepseek.com",
        "api.x.ai",
        "api.openrouter.ai",
    }
)

# Consumer chat sites — never treat these as API endpoints.
_BLOCKED_WEBSITE_HOSTS = frozenset(
    {
        "chat.openai.com",
        "chatgpt.com",
        "www.chatgpt.com",
        "claude.ai",
        "www.claude.ai",
        "gemini.google.com",
        "aistudio.google.com",
        "grok.x.ai",
        "grok.com",
        "www.grok.com",
        "x.com",
        "twitter.com",
    }
)


class HostNotAllowed(ValueError):
    """Raised when a URL is not an allowlisted official API host."""


def official_api_hosts() -> set[str]:
    return set(_OFFICIAL_HOSTS)


def user_added_hosts() -> set[str]:
    raw = (os.getenv("ALLOWED_API_HOSTS") or "").strip()
    return {h.strip().lower().rstrip(".") for h in raw.split(",") if h.strip()}


def _is_azure_openai(host: str) -> bool:
    return host == "openai.azure.com" or host.endswith(".openai.azure.com")


def is_official_api_host(host: str) -> bool:
    host = (host or "").strip().lower().rstrip(".")
    if not host:
        return False
    if host in _BLOCKED_WEBSITE_HOSTS:
        return False
    if host in _OFFICIAL_HOSTS or _is_azure_openai(host):
        return True
    return host in user_added_hosts()


def _ip_blocked(ip_text: str) -> bool:
    try:
        addr = ipaddress.ip_address(ip_text)
    except ValueError:
        return True
    if addr.is_private or addr.is_loopback or addr.is_link_local:
        return True
    if addr.is_reserved or addr.is_multicast or addr.is_unspecified:
        return True
    if str(addr) == "169.254.169.254":
        return True
    return False


def _host_resolves_public(host: str) -> None:
    try:
        infos = socket.getaddrinfo(host, None)
    except socket.gaierror as e:
        raise HostNotAllowed(f"Could not resolve host: {host}") from e
    ips = {item[4][0] for item in infos if item[4]}
    if not ips:
        raise HostNotAllowed(f"Could not resolve host: {host}")
    for ip in ips:
        if _ip_blocked(ip):
            raise HostNotAllowed("That address is not allowed.")


def assert_public_https_url(url: str) -> str:
    """
    Require https, allowlisted host, and no private/link-local/metadata IPs.
    Returns the normalized URL string.
    """
    raw = (url or "").strip()
    if not raw:
        raise HostNotAllowed("Empty URL.")
    parsed = urlparse(raw)
    if parsed.scheme.lower() != "https":
        raise HostNotAllowed("Only HTTPS URLs are allowed.")
    host = (parsed.hostname or "").lower().rstrip(".")
    if not host:
        raise HostNotAllowed("URL has no host.")
    if host in _BLOCKED_WEBSITE_HOSTS:
        raise HostNotAllowed("Chat websites cannot be used as API endpoints.")
    try:
        ipaddress.ip_address(host)
    except ValueError:
        pass
    else:
        raise HostNotAllowed("Raw IP addresses are not allowed.")
    if not is_official_api_host(host):
        raise HostNotAllowed(
            "Host is not on the official API allowlist. "
            "Add it to ALLOWED_API_HOSTS in .env if you trust it."
        )
    _host_resolves_public(host)
    return raw
