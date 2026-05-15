"""Export decrypted .env variables to shell-compatible formats."""

from __future__ import annotations

from pathlib import Path
from typing import Dict, Literal

from envault.vault import unlock

ExportFormat = Literal["dotenv", "shell", "json"]


class ExportError(Exception):
    """Raised when export fails."""


def export_env(
    passphrase: str,
    directory: Path | None = None,
    fmt: ExportFormat = "dotenv",
    keys: list[str] | None = None,
) -> str:
    """Decrypt the vault and return variables in the requested format.

    Args:
        passphrase: Passphrase used to decrypt the vault.
        directory:  Directory containing the vault file (defaults to cwd).
        fmt:        Output format – 'dotenv', 'shell', or 'json'.
        keys:       Optional allowlist of variable names to include.

    Returns:
        A string in the requested format.

    Raises:
        ExportError: If the vault cannot be read or decrypted.
    """
    try:
        env: Dict[str, str] = unlock(passphrase, directory=directory)
    except Exception as exc:
        raise ExportError(f"Failed to decrypt vault: {exc}") from exc

    if keys is not None:
        env = {k: v for k, v in env.items() if k in keys}

    if fmt == "dotenv":
        return _to_dotenv(env)
    if fmt == "shell":
        return _to_shell(env)
    if fmt == "json":
        return _to_json(env)
    raise ExportError(f"Unknown format: {fmt!r}")


def _to_dotenv(env: Dict[str, str]) -> str:
    lines = [f'{k}="{v}"' for k, v in sorted(env.items())]
    return "\n".join(lines)


def _to_shell(env: Dict[str, str]) -> str:
    lines = [f'export {k}="{v}"' for k, v in sorted(env.items())]
    return "\n".join(lines)


def _to_json(env: Dict[str, str]) -> str:
    import json
    return json.dumps(dict(sorted(env.items())), indent=2)
