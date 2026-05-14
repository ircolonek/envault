"""Remote backend sync for envault — push/pull encrypted vaults to/from a shared backend."""

import json
import os
import urllib.error
import urllib.request
from typing import Optional

ENVAULT_API_URL_ENV = "ENVAULT_API_URL"
ENVAULT_API_TOKEN_ENV = "ENVAULT_API_TOKEN"
DEFAULT_TIMEOUT = 10


class RemoteError(Exception):
    """Raised when a remote operation fails."""


class RemoteAuthError(RemoteError):
    """Raised when the remote rejects our credentials."""


def _get_base_url() -> str:
    url = os.environ.get(ENVAULT_API_URL_ENV, "").rstrip("/")
    if not url:
        raise RemoteError(
            f"Remote API URL not set. Export {ENVAULT_API_URL_ENV}."
        )
    return url


def _get_token() -> str:
    token = os.environ.get(ENVAULT_API_TOKEN_ENV, "")
    if not token:
        raise RemoteError(
            f"API token not set. Export {ENVAULT_API_TOKEN_ENV}."
        )
    return token


def _request(method: str, path: str, body: Optional[dict] = None) -> dict:
    url = f"{_get_base_url()}{path}"
    token = _get_token()
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(
        url,
        data=data,
        method=method,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=DEFAULT_TIMEOUT) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as exc:
        if exc.code == 401:
            raise RemoteAuthError("Invalid or expired API token.") from exc
        raise RemoteError(f"HTTP {exc.code}: {exc.reason}") from exc
    except urllib.error.URLError as exc:
        raise RemoteError(f"Connection error: {exc.reason}") from exc


def push_vault(project: str, encrypted_payload: str) -> None:
    """Upload an encrypted vault payload to the remote backend."""
    _request("PUT", f"/vaults/{project}", {"payload": encrypted_payload})


def pull_vault(project: str) -> str:
    """Download an encrypted vault payload from the remote backend."""
    result = _request("GET", f"/vaults/{project}")
    try:
        return result["payload"]
    except KeyError as exc:
        raise RemoteError("Malformed response from remote: missing 'payload'.") from exc
