"""High-level Vault API for envault.

Provides a simple interface to lock (encrypt) and unlock (decrypt) a
collection of environment variables stored in a vault file.
"""

from pathlib import Path
from typing import Dict, Optional

from envault.crypto import decrypt, encrypt
from envault.storage import (
    VaultNotFoundError,
    get_vault_path,
    read_vault,
    vault_exists,
    write_vault,
)

_ENV_SEPARATOR = "\n"
_KV_SEPARATOR = "="


def _serialize(env_vars: Dict[str, str]) -> str:
    """Serialize a dict of env vars to a newline-delimited KEY=VALUE string."""
    return _ENV_SEPARATOR.join(
        f"{k}{_KV_SEPARATOR}{v}" for k, v in sorted(env_vars.items())
    )


def _deserialize(plaintext: str) -> Dict[str, str]:
    """Deserialize a KEY=VALUE plaintext string back to a dict."""
    result: Dict[str, str] = {}
    for line in plaintext.splitlines():
        line = line.strip()
        if not line:
            continue
        key, _, value = line.partition(_KV_SEPARATOR)
        result[key] = value
    return result


def lock(
    env_vars: Dict[str, str],
    passphrase: str,
    directory: Optional[str] = None,
) -> Path:
    """Encrypt *env_vars* and write them to a vault file.

    Returns the path of the written vault file.
    """
    plaintext = _serialize(env_vars)
    ciphertext = encrypt(plaintext, passphrase)
    path = get_vault_path(directory)
    write_vault(ciphertext, path)
    return path


def unlock(
    passphrase: str,
    directory: Optional[str] = None,
) -> Dict[str, str]:
    """Read and decrypt the vault file, returning the env vars dict.

    Raises:
        VaultNotFoundError: If no vault file is found.
        cryptography.fernet.InvalidToken: If the passphrase is wrong.
    """
    path = get_vault_path(directory)
    ciphertext = read_vault(path)
    plaintext = decrypt(ciphertext, passphrase)
    return _deserialize(plaintext)


def is_locked(directory: Optional[str] = None) -> bool:
    """Return True if a vault file exists in *directory* (or cwd)."""
    return vault_exists(get_vault_path(directory))
