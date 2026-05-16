"""CLI commands for importing .env files into envault vaults."""

from __future__ import annotations

import argparse
from pathlib import Path

from envault.import_env import import_env, ImportError as EnvImportError


def cmd_import(args: argparse.Namespace) -> None:
    """Handle the ``envault import`` sub-command."""
    source = Path(args.source)
    directory = Path(args.dir) if args.dir else None

    try:
        count = import_env(
            source,
            args.passphrase,
            directory=directory,
            overwrite=args.overwrite,
        )
    except EnvImportError as exc:
        print(f"Import failed: {exc}")
        raise SystemExit(1) from exc

    if count == 0:
        print("Nothing to import (file empty or all keys already present).")
    else:
        print(f"Imported {count} variable(s) from {source}.")


def register_import_commands(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    """Attach the *import* sub-command to *subparsers*."""
    p = subparsers.add_parser(
        "import",
        help="Import variables from a plain .env file into the vault.",
    )
    p.add_argument("source", help="Path to the .env file to import.")
    p.add_argument(
        "--passphrase",
        required=True,
        help="Passphrase used to encrypt / decrypt the vault.",
    )
    p.add_argument(
        "--dir",
        default=None,
        help="Directory containing the vault (default: current directory).",
    )
    p.add_argument(
        "--overwrite",
        action="store_true",
        default=False,
        help="Overwrite existing keys with values from the imported file.",
    )
    p.set_defaults(func=cmd_import)
