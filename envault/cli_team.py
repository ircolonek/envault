"""CLI commands for team member management."""

from __future__ import annotations

import argparse
import sys

from envault.team import TeamError, add_member, get_token, list_members, remove_member


def cmd_team_add(args: argparse.Namespace) -> None:
    """Add a team member."""
    try:
        add_member(args.email, args.token, args.directory)
        print(f"Added member: {args.email}")
    except TeamError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)


def cmd_team_remove(args: argparse.Namespace) -> None:
    """Remove a team member."""
    try:
        remove_member(args.email, args.directory)
        print(f"Removed member: {args.email}")
    except TeamError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)


def cmd_team_list(args: argparse.Namespace) -> None:
    """List all team members."""
    members = list_members(args.directory)
    if not members:
        print("No team members configured.")
        return
    for member in members:
        token_preview = member["token"][:6] + "..." if len(member["token"]) > 6 else "***"
        print(f"  {member['email']}  (token: {token_preview})")


def cmd_team_token(args: argparse.Namespace) -> None:
    """Print the token for a specific team member."""
    try:
        token = get_token(args.email, args.directory)
        print(token)
    except TeamError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)


def register_team_commands(subparsers: argparse._SubParsersAction) -> None:
    """Register all team-related subcommands onto the given subparser."""
    team_parser = subparsers.add_parser("team", help="Manage team members")
    team_sub = team_parser.add_subparsers(dest="team_command", required=True)

    # team add
    p_add = team_sub.add_parser("add", help="Add a team member")
    p_add.add_argument("email", help="Member email address")
    p_add.add_argument("token", help="Member access token")
    p_add.add_argument("--directory", default=None, help="Vault directory")
    p_add.set_defaults(func=cmd_team_add)

    # team remove
    p_remove = team_sub.add_parser("remove", help="Remove a team member")
    p_remove.add_argument("email", help="Member email address")
    p_remove.add_argument("--directory", default=None, help="Vault directory")
    p_remove.set_defaults(func=cmd_team_remove)

    # team list
    p_list = team_sub.add_parser("list", help="List team members")
    p_list.add_argument("--directory", default=None, help="Vault directory")
    p_list.set_defaults(func=cmd_team_list)

    # team token
    p_token = team_sub.add_parser("token", help="Show token for a member")
    p_token.add_argument("email", help="Member email address")
    p_token.add_argument("--directory", default=None, help="Vault directory")
    p_token.set_defaults(func=cmd_team_token)
