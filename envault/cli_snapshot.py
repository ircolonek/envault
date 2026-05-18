"""CLI commands for snapshot management."""

from __future__ import annotations

import argparse
from datetime import datetime

from .snapshot import SnapshotError, delete_snapshot, list_snapshots, restore_snapshot, save_snapshot


def cmd_snapshot_save(args: argparse.Namespace) -> None:
    try:
        count = save_snapshot(
            args.name,
            args.passphrase,
            directory=args.dir,
            vault_file=args.file,
        )
        print(f"Snapshot '{args.name}' saved ({count} variable(s)).")
    except Exception as exc:
        print(f"Error: {exc}")
        raise SystemExit(1)


def cmd_snapshot_restore(args: argparse.Namespace) -> None:
    try:
        count = restore_snapshot(
            args.name,
            args.passphrase,
            directory=args.dir,
            vault_file=args.file,
        )
        print(f"Snapshot '{args.name}' restored ({count} variable(s)).")
    except SnapshotError as exc:
        print(f"Error: {exc}")
        raise SystemExit(1)


def cmd_snapshot_list(args: argparse.Namespace) -> None:
    entries = list_snapshots(directory=args.dir)
    if not entries:
        print("No snapshots found.")
        return
    for entry in entries:
        ts = datetime.fromtimestamp(entry["created_at"]).strftime("%Y-%m-%d %H:%M:%S")
        print(f"  {entry['name']:<30} {ts}")


def cmd_snapshot_delete(args: argparse.Namespace) -> None:
    try:
        delete_snapshot(args.name, directory=args.dir)
        print(f"Snapshot '{args.name}' deleted.")
    except SnapshotError as exc:
        print(f"Error: {exc}")
        raise SystemExit(1)


def register_snapshot_commands(subparsers: argparse._SubParsersAction) -> None:
    snap = subparsers.add_parser("snapshot", help="Manage vault snapshots")
    snap_sub = snap.add_subparsers(dest="snapshot_cmd", required=True)

    p_save = snap_sub.add_parser("save", help="Save a snapshot of the current vault")
    p_save.add_argument("name", help="Snapshot name")
    p_save.add_argument("--passphrase", required=True)
    p_save.add_argument("--dir", default=".")
    p_save.add_argument("--file", default=".env.vault")
    p_save.set_defaults(func=cmd_snapshot_save)

    p_restore = snap_sub.add_parser("restore", help="Restore a snapshot into the vault")
    p_restore.add_argument("name", help="Snapshot name")
    p_restore.add_argument("--passphrase", required=True)
    p_restore.add_argument("--dir", default=".")
    p_restore.add_argument("--file", default=".env.vault")
    p_restore.set_defaults(func=cmd_snapshot_restore)

    p_list = snap_sub.add_parser("list", help="List saved snapshots")
    p_list.add_argument("--dir", default=".")
    p_list.set_defaults(func=cmd_snapshot_list)

    p_del = snap_sub.add_parser("delete", help="Delete a snapshot")
    p_del.add_argument("name", help="Snapshot name")
    p_del.add_argument("--dir", default=".")
    p_del.set_defaults(func=cmd_snapshot_delete)
