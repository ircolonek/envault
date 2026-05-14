"""CLI sub-commands for interacting with the audit log."""

from __future__ import annotations

import argparse
import json
import sys
from typing import List

from envault.audit import get_log, clear_log


def cmd_audit_log(args: argparse.Namespace) -> None:
    """Print audit log entries, optionally filtering by action."""
    entries = get_log(directory=args.dir)
    if not entries:
        print("No audit entries found.")
        return

    if args.action:
        entries = [e for e in entries if e.get("action") == args.action]

    if args.json:
        print(json.dumps(entries, indent=2))
        return

    for entry in entries:
        ts = entry.get("timestamp", "?")
        actor = entry.get("actor", "?")
        action = entry.get("action", "?")
        extras = {k: v for k, v in entry.items() if k not in ("timestamp", "actor", "action")}
        extra_str = "  " + "  ".join(f"{k}={v}" for k, v in extras.items()) if extras else ""
        print(f"[{ts}] {actor}: {action}{extra_str}")


def cmd_audit_clear(args: argparse.Namespace) -> None:
    """Clear the audit log."""
    clear_log(directory=args.dir)
    print("Audit log cleared.")


def register_audit_commands(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    """Attach audit sub-commands to an existing subparser group."""
    audit_parser = subparsers.add_parser("audit", help="Manage the audit log")
    audit_sub = audit_parser.add_subparsers(dest="audit_cmd", required=True)

    # envault audit log
    log_parser = audit_sub.add_parser("log", help="Display audit log entries")
    log_parser.add_argument("--dir", default=None, help="Vault directory")
    log_parser.add_argument("--action", default=None, help="Filter by action type")
    log_parser.add_argument("--json", action="store_true", help="Output as JSON")
    log_parser.set_defaults(func=cmd_audit_log)

    # envault audit clear
    clear_parser = audit_sub.add_parser("clear", help="Clear the audit log")
    clear_parser.add_argument("--dir", default=None, help="Vault directory")
    clear_parser.set_defaults(func=cmd_audit_clear)
