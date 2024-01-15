"""
Entry point for the CLI. It parses the arguments and calls the corresponding function.
"""
from argparse import ArgumentParser
from typing import Any, Optional

from pyneo4j_ogm.migrations.actions import create, down, init, status, up


def parse_int_arg(arg: Any) -> Optional[int]:
    try:
        return int(arg)
    except ValueError:
        return None


def cli() -> None:
    """
    Function that parses the CLI arguments and calls the corresponding function.
    """
    parser = ArgumentParser(prog="pyneo4j_ogm", description="Migration CLI pyneo4j-ogm models")
    subparsers = parser.add_subparsers(dest="command", title="Commands", metavar="")

    init_parser = subparsers.add_parser("init", help="Initialize migrations for this project")
    init_parser.add_argument(
        "-p",
        "--path",
        help="Path to the directory where the migrations will be stored",
        default="migrations",
        required=False,
    )
    init_parser.add_argument("-o", "--overwrite", help="Overwrite existing directory", type=bool, default=False)
    init_parser.set_defaults(func=init)

    create_parser = subparsers.add_parser("create", help="Creates a new migration file")
    create_parser.add_argument("-n", "--name", help="Name of the migration")
    create_parser.set_defaults(func=create)

    up_parser = subparsers.add_parser("up", help="Applies the defined number of migrations")
    up_parser.add_argument("-c", "--config", help="Path to a config file", default="migration.json", required=False)
    up_parser.add_argument(
        "-n",
        "--number",
        help="Number of migrations to apply. Omit to apply all pending migrations",
        type=parse_int_arg,
        default=None,
        required=False,
    )
    up_parser.set_defaults(func=up)

    down_parser = subparsers.add_parser("down", help="Rollbacks the defined number of migrations")
    down_parser.add_argument("-c", "--config", help="Path to a config file", default="migration.json", required=False)
    down_parser.add_argument(
        "-n", "--number", help="Number of migrations to rollback", type=int, default=1, required=False
    )
    down_parser.set_defaults(func=down)

    status_parser = subparsers.add_parser("status", help="Shows the status of all migrations")
    status_parser.add_argument("-c", "--config", help="Path to a config file", default="migration.json", required=False)
    status_parser.add_argument(
        "-f",
        "--format",
        help="Output format",
        choices=["raw", "prettify", "file:json"],
        default="prettify",
        required=False,
    )
    status_parser.set_defaults(func=status)

    args = parser.parse_args()

    if args.command:
        args.func(args)
    else:
        parser.print_help()
