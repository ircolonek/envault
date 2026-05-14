"""High-level sync commands: push a locked vault to remote, pull and verify it."""

from pathlib import Path

from envault.remote import pull_vault, push_vault
from envault.storage import VaultCorruptedError, VaultNotFoundError, get_vault_path, read_vault, write_vault


def sync_push(project: str, directory: str = ".") -> Path:
    """Read the local encrypted vault and push it to the remote backend.

    Returns the path of the vault file that was pushed.
    Raises VaultNotFoundError if the vault file does not exist.
    """
    vault_path = get_vault_path(directory)
    data = read_vault(vault_path)  # validates JSON structure
    raw_payload = vault_path.read_text(encoding="utf-8")
    push_vault(project, raw_payload)
    return vault_path


def sync_pull(project: str, directory: str = ".") -> Path:
    """Pull an encrypted vault from the remote backend and write it locally.

    Returns the path where the vault was written.
    Raises RemoteError on network or auth failures.
    Raises VaultCorruptedError if the downloaded payload is not valid JSON.
    """
    raw_payload = pull_vault(project)

    # Validate the payload is well-formed before writing to disk.
    import json
    try:
        parsed = json.loads(raw_payload)
    except json.JSONDecodeError as exc:
        raise VaultCorruptedError("Remote payload is not valid JSON.") from exc

    required_keys = {"version", "payload"}
    if not required_keys.issubset(parsed.keys()):
        raise VaultCorruptedError(
            f"Remote payload missing required keys: {required_keys - parsed.keys()}"
        )

    vault_path = get_vault_path(directory)
    vault_path.parent.mkdir(parents=True, exist_ok=True)
    vault_path.write_text(raw_payload, encoding="utf-8")
    return vault_path
