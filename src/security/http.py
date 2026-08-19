"""httpx client that re-checks HTTPS + allowlist on every request and redirect."""

from __future__ import annotations

import httpx

from .hosts import HostNotAllowed, assert_public_https_url


class _AllowlistTransport(httpx.HTTPTransport):
    def handle_request(self, request: httpx.Request) -> httpx.Response:
        assert_public_https_url(str(request.url))
        return super().handle_request(request)


def make_secure_client(timeout: float = 60.0) -> httpx.Client:
    """Shared client for official provider SDKs. Follows redirects only if still allowlisted."""
    return httpx.Client(
        transport=_AllowlistTransport(),
        follow_redirects=True,
        timeout=timeout,
        trust_env=False,
    )


def secure_request(method: str, url: str, **kwargs) -> httpx.Response:
    assert_public_https_url(url)
    with make_secure_client() as client:
        try:
            resp = client.request(method, url, **kwargs)
        except HostNotAllowed:
            raise
        assert_public_https_url(str(resp.url))
        return resp
