"""Diff utilities for comparing vault contents across versions."""

from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass
class DiffEntry:
    key: str
    status: str  # 'added', 'removed', 'changed', 'unchanged'
    old_value: Optional[str] = None
    new_value: Optional[str] = None

    def __repr__(self) -> str:
        if self.status == "added":
            return f"+ {self.key}={self.new_value}"
        if self.status == "removed":
            return f"- {self.key}={self.old_value}"
        if self.status == "changed":
            return f"~ {self.key}: {self.old_value!r} -> {self.new_value!r}"
        return f"  {self.key}={self.new_value}"


def diff_envs(
    old: Dict[str, str],
    new: Dict[str, str],
    *,
    include_unchanged: bool = False,
) -> List[DiffEntry]:
    """Return a list of DiffEntry objects describing changes from old to new."""
    entries: List[DiffEntry] = []
    all_keys = sorted(set(old) | set(new))

    for key in all_keys:
        in_old = key in old
        in_new = key in new

        if in_old and in_new:
            if old[key] != new[key]:
                entries.append(
                    DiffEntry(key, "changed", old_value=old[key], new_value=new[key])
                )
            elif include_unchanged:
                entries.append(
                    DiffEntry(key, "unchanged", old_value=old[key], new_value=new[key])
                )
        elif in_new:
            entries.append(DiffEntry(key, "added", new_value=new[key]))
        else:
            entries.append(DiffEntry(key, "removed", old_value=old[key]))

    return entries


def summarise(entries: List[DiffEntry]) -> Dict[str, int]:
    """Return counts per status."""
    counts: Dict[str, int] = {"added": 0, "removed": 0, "changed": 0, "unchanged": 0}
    for e in entries:
        counts[e.status] += 1
    return counts
