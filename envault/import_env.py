"""Import variables from an existing .env file into an envault vault."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Dict, Optional

from envault.vault import lock, unlock, is_locked
from envault.storage import get_vault_path, VaultNotFoundError


class ImportError(Exception):  # noqa: A001
    """Raised when an import operation fails."""


def parse_dotenv(source: Path) -> Dict[str, str]:
    """Parse a .env file and return a dict of key/value pairs.

    Skips blank lines and comments.  Strips optional surrounding quotes
    from values.
    """
    if not source.exists():
        raise ImportError(f".env file not found: {source}")

    env: Dict[str, str] = {}
    for raw in source.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip()
        # Strip matching surrounding quotes
        if len(value) >= 2 and value[0] in ('"', "'") and value[-1] == value[0]:
            value = value[1:-1]
        if key:
            env[key] = value
    return env


def import_env(
    source: Path,
    passphrase: str,
    *,
    directory: Optional[Path] = None,
    overwrite: bool = False,
) -> int:
    """Import variables from *source* .env file into the vault.

    If the vault already exists the incoming variables are merged; existing
    keys are only overwritten when *overwrite* is True.

    Returns the number of variables actually written (new + updated).
    """
    incoming = parse_dotenv(source)
    if not incoming:
        return 0

    vault_path = get_vault_path(directory)
    existing: Dict[str, str] = {}

    if vault_path.exists():
        try:
            existing = unlock(passphrase, directory=directory)
        except Exception as exc:  # pragma: no cover
            raise ImportError(f"Could not unlock existing vault: {exc}") from exc

    if overwrite:
        merged = {**existing, **incoming}
    else:
        merged = {**incoming, **existing}  # existing wins on conflict

    written = sum(1 for k, v in incoming.items() if merged.get(k) == v and (overwrite or k not in existing))
    lock(merged, passphrase, directory=directory)
    return written
