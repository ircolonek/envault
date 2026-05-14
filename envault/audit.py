"""Audit log for vault operations — records who did what and when."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Any

AUDIT_FILENAME = ".envault_audit.json"


def _get_audit_path(directory: str | None = None) -> Path:
    base = Path(directory) if directory else Path.cwd()
    return base / AUDIT_FILENAME


def _load_entries(audit_path: Path) -> List[Dict[str, Any]]:
    if not audit_path.exists():
        return []
    try:
        with audit_path.open("r", encoding="utf-8") as fh:
            data = json.load(fh)
        if isinstance(data, list):
            return data
    except (json.JSONDecodeError, OSError):
        pass
    return []


def record(action: str, actor: str | None = None, directory: str | None = None, **extra: Any) -> None:
    """Append a single audit entry."""
    audit_path = _get_audit_path(directory)
    entries = _load_entries(audit_path)

    entry: Dict[str, Any] = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "action": action,
        "actor": actor or os.environ.get("USER", "unknown"),
    }
    entry.update(extra)
    entries.append(entry)

    audit_path.parent.mkdir(parents=True, exist_ok=True)
    with audit_path.open("w", encoding="utf-8") as fh:
        json.dump(entries, fh, indent=2)


def get_log(directory: str | None = None) -> List[Dict[str, Any]]:
    """Return all audit entries for the given directory."""
    return _load_entries(_get_audit_path(directory))


def clear_log(directory: str | None = None) -> None:
    """Remove the audit log file entirely."""
    audit_path = _get_audit_path(directory)
    if audit_path.exists():
        audit_path.unlink()
