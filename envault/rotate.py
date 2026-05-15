"""Key rotation: re-encrypt vault contents with a new passphrase."""

from pathlib import Path
from typing import Optional

from envault.storage import read_vault, write_vault, VaultNotFoundError
from envault.vault import lock, unlock
from envault.audit import record


class RotationError(Exception):
    """Raised when key rotation fails."""


def rotate(
    old_passphrase: str,
    new_passphrase: str,
    directory: Optional[Path] = None,
    env_file: Optional[Path] = None,
) -> int:
    """Re-encrypt the vault with a new passphrase.

    1. Unlock (decrypt) the existing vault using *old_passphrase*.
    2. Re-lock (encrypt) the plaintext with *new_passphrase*.
    3. Overwrite the vault file in place.

    Returns the number of environment variables that were rotated.

    Raises
    ------
    RotationError
        If the vault cannot be found, decryption fails, or any other
        rotation-specific problem occurs.
    """
    directory = directory or Path.cwd()

    # --- decrypt with old passphrase ---
    try:
        env_vars = unlock(
            passphrase=old_passphrase,
            directory=directory,
            env_file=env_file,
        )
    except VaultNotFoundError as exc:
        raise RotationError(str(exc)) from exc
    except Exception as exc:
        raise RotationError(f"Failed to decrypt vault: {exc}") from exc

    # --- re-encrypt with new passphrase ---
    try:
        lock(
            env_vars=env_vars,
            passphrase=new_passphrase,
            directory=directory,
            env_file=env_file,
        )
    except Exception as exc:
        raise RotationError(f"Failed to re-encrypt vault: {exc}") from exc

    count = len(env_vars)
    record(action="rotate", detail=f"rotated {count} variable(s)", directory=directory)
    return count
