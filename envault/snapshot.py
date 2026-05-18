"""Snapshot management: save and restore named snapshots of vault contents."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Dict, List, Optional

from .vault import lock, unlock


class SnapshotError(Exception):
    """Raised when a snapshot operation fails."""


def _get_snapshot_dir(directory: str = ".") -> Path:
    return Path(directory) / ".envault" / "snapshots"


def _snapshot_path(name: str, directory: str = ".") -> Path:
    return _get_snapshot_dir(directory) / f"{name}.json"


def save_snapshot(
    name: str,
    passphrase: str,
    directory: str = ".",
    vault_file: str = ".env.vault",
) -> int:
    """Decrypt the current vault and save its contents as a named snapshot.
    Returns the number of variables saved."""
    env = unlock(passphrase, directory=directory, vault_file=vault_file)
    snapshot_dir = _get_snapshot_dir(directory)
    snapshot_dir.mkdir(parents=True, exist_ok=True)
    data = {
        "name": name,
        "created_at": time.time(),
        "variables": env,
    }
    _snapshot_path(name, directory).write_text(json.dumps(data, indent=2))
    return len(env)


def restore_snapshot(
    name: str,
    passphrase: str,
    directory: str = ".",
    vault_file: str = ".env.vault",
) -> int:
    """Re-encrypt a saved snapshot back into the vault.
    Returns the number of variables restored."""
    path = _snapshot_path(name, directory)
    if not path.exists():
        raise SnapshotError(f"Snapshot '{name}' not found.")
    data = json.loads(path.read_text())
    env: Dict[str, str] = data["variables"]
    lock(env, passphrase, directory=directory, vault_file=vault_file)
    return len(env)


def list_snapshots(directory: str = ".") -> List[dict]:
    """Return metadata for all saved snapshots, sorted by creation time."""
    snapshot_dir = _get_snapshot_dir(directory)
    if not snapshot_dir.exists():
        return []
    entries = []
    for p in snapshot_dir.glob("*.json"):
        try:
            data = json.loads(p.read_text())
            entries.append({"name": data["name"], "created_at": data["created_at"]})
        except (json.JSONDecodeError, KeyError):
            continue
    return sorted(entries, key=lambda e: e["created_at"])


def delete_snapshot(name: str, directory: str = ".") -> None:
    """Delete a named snapshot."""
    path = _snapshot_path(name, directory)
    if not path.exists():
        raise SnapshotError(f"Snapshot '{name}' not found.")
    path.unlink()
