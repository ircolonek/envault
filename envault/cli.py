"""Command-line interface for envault."""

import sys
import getpass
import argparse

from envault.vault import lock, unlock, is_locked
from envault.storage import VaultNotFoundError, VaultCorruptedError


def cmd_lock(args):
    """Encrypt a .env file into a vault."""
    passphrase = getpass.getpass("Passphrase: ")
    confirm = getpass.getpass("Confirm passphrase: ")
    if passphrase != confirm:
        print("Error: passphrases do not match.", file=sys.stderr)
        return 1

    try:
        with open(args.env_file, "r") as f:
            env_content = f.read()
    except FileNotFoundError:
        print(f"Error: '{args.env_file}' not found.", file=sys.stderr)
        return 1

    lock(env_content, passphrase, directory=args.dir)
    print(f"Vault created successfully.")
    return 0


def cmd_unlock(args):
    """Decrypt a vault and write the .env file."""
    passphrase = getpass.getpass("Passphrase: ")

    try:
        env_content = unlock(passphrase, directory=args.dir)
    except VaultNotFoundError:
        print("Error: No vault found. Run 'envault lock' first.", file=sys.stderr)
        return 1
    except VaultCorruptedError as e:
        print(f"Error: Vault is corrupted — {e}", file=sys.stderr)
        return 1
    except ValueError:
        print("Error: Incorrect passphrase or corrupted vault.", file=sys.stderr)
        return 1

    with open(args.env_file, "w") as f:
        f.write(env_content)
    print(f"'{args.env_file}' restored successfully.")
    return 0


def cmd_status(args):
    """Show whether a vault exists for the current directory."""
    if is_locked(directory=args.dir):
        print("Vault is present and locked.")
    else:
        print("No vault found.")
    return 0


def build_parser():
    parser = argparse.ArgumentParser(
        prog="envault",
        description="Secure environment variable manager.",
    )
    parser.add_argument("--dir", default=None, metavar="DIR",
                        help="Directory containing the vault (default: current directory).")

    sub = parser.add_subparsers(dest="command", required=True)

    p_lock = sub.add_parser("lock", help="Encrypt a .env file into a vault.")
    p_lock.add_argument("env_file", nargs="?", default=".env", help="Path to the .env file (default: .env).")
    p_lock.set_defaults(func=cmd_lock)

    p_unlock = sub.add_parser("unlock", help="Decrypt the vault into a .env file.")
    p_unlock.add_argument("env_file", nargs="?", default=".env", help="Output path for the .env file (default: .env).")
    p_unlock.set_defaults(func=cmd_unlock)

    p_status = sub.add_parser("status", help="Show vault status.")
    p_status.set_defaults(func=cmd_status)

    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()
    sys.exit(args.func(args))


if __name__ == "__main__":
    main()
