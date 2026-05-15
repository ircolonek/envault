"""Main CLI entry point for envault."""

import argparse
import sys
from pathlib import Path

from envault.vault import lock, unlock, is_locked
from envault.storage import VaultNotFoundError, VaultCorruptedError
from envault.cli_audit import register_audit_commands
from envault.cli_team import register_team_commands
from envault.cli_diff import register_diff_commands


def cmd_lock(args: argparse.Namespace) -> None:
    env_path = Path(args.env_file)
    if not env_path.exists():
        print(f"error: {args.env_file} not found", file=sys.stderr)
        sys.exit(1)
    env = {}
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, _, v = line.partition("=")
        env[k.strip()] = v.strip()
    lock(env, args.passphrase, directory=args.dir, filename=args.vault_file)
    print(f"Vault locked -> {Path(args.dir) / args.vault_file}")


def cmd_unlock(args: argparse.Namespace) -> None:
    try:
        env = unlock(args.passphrase, directory=args.dir, filename=args.vault_file)
    except VaultNotFoundError:
        print("error: vault not found", file=sys.stderr)
        sys.exit(1)
    except VaultCorruptedError:
        print("error: wrong passphrase or corrupted vault", file=sys.stderr)
        sys.exit(1)
    out = Path(args.dir) / args.env_file
    lines = [f"{k}={v}" for k, v in sorted(env.items())]
    out.write_text("\n".join(lines) + "\n")
    print(f"Vault unlocked -> {out}")


def cmd_status(args: argparse.Namespace) -> None:
    locked = is_locked(directory=args.dir, filename=args.vault_file)
    vault_path = Path(args.dir) / args.vault_file
    if not vault_path.exists():
        print("No vault found.")
    elif locked:
        print(f"Vault is locked: {vault_path}")
    else:
        print(f"Vault is unlocked: {vault_path}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="envault",
        description="Secure environment variable manager",
    )
    parser.add_argument(
        "--dir", default=".", help="Working directory (default: current directory)"
    )
    parser.add_argument(
        "--vault-file", default=".envault", dest="vault_file",
        help="Vault filename (default: .envault)"
    )
    sub = parser.add_subparsers(dest="command")

    p_lock = sub.add_parser("lock", help="Encrypt a .env file into the vault")
    p_lock.add_argument("--env-file", default=".env", dest="env_file")
    p_lock.add_argument("-p", "--passphrase", required=True)
    p_lock.set_defaults(func=cmd_lock)

    p_unlock = sub.add_parser("unlock", help="Decrypt the vault into a .env file")
    p_unlock.add_argument("--env-file", default=".env", dest="env_file")
    p_unlock.add_argument("-p", "--passphrase", required=True)
    p_unlock.set_defaults(func=cmd_unlock)

    p_status = sub.add_parser("status", help="Show vault status")
    p_status.set_defaults(func=cmd_status)

    register_audit_commands(sub)
    register_team_commands(sub)
    register_diff_commands(sub)

    return parser


def main(argv=None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not hasattr(args, "func"):
        parser.print_help()
        sys.exit(0)
    args.func(args)


if __name__ == "__main__":
    main()
