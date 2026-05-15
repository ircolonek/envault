"""CLI commands for vault diff."""

import argparse
import sys
from pathlib import Path

from envault.diff import diff_envs, summarise
from envault.vault import unlock
from envault.storage import VaultNotFoundError, VaultCorruptedError


def cmd_diff(args: argparse.Namespace) -> None:
    """Show differences between two vault files."""
    passphrase: str = args.passphrase

    try:
        old_env = unlock(passphrase, directory=str(Path(args.old).parent), filename=Path(args.old).name)
    except VaultNotFoundError:
        print(f"error: vault not found: {args.old}", file=sys.stderr)
        sys.exit(1)
    except VaultCorruptedError:
        print(f"error: vault corrupted or wrong passphrase: {args.old}", file=sys.stderr)
        sys.exit(1)

    try:
        new_env = unlock(passphrase, directory=str(Path(args.new).parent), filename=Path(args.new).name)
    except VaultNotFoundError:
        print(f"error: vault not found: {args.new}", file=sys.stderr)
        sys.exit(1)
    except VaultCorruptedError:
        print(f"error: vault corrupted or wrong passphrase: {args.new}", file=sys.stderr)
        sys.exit(1)

    entries = diff_envs(old_env, new_env, include_unchanged=args.all)

    if not entries:
        print("No differences found.")
        return

    for entry in entries:
        print(repr(entry))

    if args.summary:
        counts = summarise(entries)
        print(
            f"\nSummary: {counts['added']} added, "
            f"{counts['removed']} removed, "
            f"{counts['changed']} changed."
        )


def register_diff_commands(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser("diff", help="Diff two encrypted vault files")
    p.add_argument("old", help="Path to the old vault file")
    p.add_argument("new", help="Path to the new vault file")
    p.add_argument("-p", "--passphrase", required=True, help="Passphrase for both vaults")
    p.add_argument("--all", action="store_true", help="Include unchanged keys")
    p.add_argument("--summary", action="store_true", help="Print a summary line")
    p.set_defaults(func=cmd_diff)
