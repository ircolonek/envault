"""Backend storage abstraction for envault.

Handles reading and writing encrypted .env vault files to disk.
"""

import json
import os
from pathlib import Path
from typing import Optional

DEFAULT_VAULT_FILENAME = ".envault"


class VaultNotFoundError(FileNotFoundError):
    """Raised when a vault file does not exist."""


class VaultCorruptedError(ValueError):
    """Raised when a vault file cannot be parsed."""


def get_vault_path(directory: Optional[str] = None, filename: str = DEFAULT_VAULT_FILENAME) -> Path:
    """Return the resolved path to the vault file."""
    base = Path(directory) if directory else Path.cwd()
    return base / filename


def write_vault(ciphertext: str, path: Path) -> None:
    """Persist an encrypted vault to disk.

    Args:
        ciphertext: The encrypted payload string produced by crypto.encrypt.
        path: Destination file path.
    """
    payload = {"version": 1, "ciphertext": ciphertext}
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def read_vault(path: Path) -> str:
    """Load an encrypted vault from disk and return the ciphertext.

    Args:
        path: Path to the vault file.

    Returns:
        The raw ciphertext string.

    Raises:
        VaultNotFoundError: If the file does not exist.
        VaultCorruptedError: If the file cannot be parsed.
    """
    if not path.exists():
        raise VaultNotFoundError(f"Vault file not found: {path}")

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise VaultCorruptedError(f"Vault file is not valid JSON: {path}") from exc

    if "ciphertext" not in data:
        raise VaultCorruptedError(f"Vault file missing 'ciphertext' key: {path}")

    return data["ciphertext"]


def vault_exists(path: Path) -> bool:
    """Return True if a vault file exists at *path*."""
    return path.is_file()
