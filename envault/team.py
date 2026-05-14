"""Team member management for envault.

Handles adding/removing team members and managing their access tokens
for the shared backend.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Optional

TEAM_FILE = ".envault-team.json"


class TeamError(Exception):
    """Raised when a team operation fails."""


def _get_team_path(directory: Optional[str] = None) -> Path:
    """Return the path to the team config file."""
    base = Path(directory) if directory else Path.cwd()
    return base / TEAM_FILE


def _load_team(directory: Optional[str] = None) -> dict:
    """Load the team config from disk, returning an empty structure if missing."""
    path = _get_team_path(directory)
    if not path.exists():
        return {"members": []}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        raise TeamError(f"Could not read team file: {exc}") from exc


def _save_team(data: dict, directory: Optional[str] = None) -> None:
    """Persist the team config to disk."""
    path = _get_team_path(directory)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def add_member(email: str, token: str, directory: Optional[str] = None) -> None:
    """Add a team member with the given email and access token.

    Raises TeamError if the member already exists.
    """
    data = _load_team(directory)
    for member in data["members"]:
        if member["email"] == email:
            raise TeamError(f"Member '{email}' already exists.")
    data["members"].append({"email": email, "token": token})
    _save_team(data, directory)


def remove_member(email: str, directory: Optional[str] = None) -> None:
    """Remove a team member by email.

    Raises TeamError if the member is not found.
    """
    data = _load_team(directory)
    original_count = len(data["members"])
    data["members"] = [m for m in data["members"] if m["email"] != email]
    if len(data["members"]) == original_count:
        raise TeamError(f"Member '{email}' not found.")
    _save_team(data, directory)


def list_members(directory: Optional[str] = None) -> list[dict]:
    """Return a list of all team members (email + token)."""
    data = _load_team(directory)
    return list(data["members"])


def get_token(email: str, directory: Optional[str] = None) -> str:
    """Return the access token for a given email.

    Raises TeamError if the member is not found.
    """
    data = _load_team(directory)
    for member in data["members"]:
        if member["email"] == email:
            return member["token"]
    raise TeamError(f"Member '{email}' not found.")
