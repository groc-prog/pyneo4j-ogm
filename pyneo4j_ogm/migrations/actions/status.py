"""
Shows which migrations have been run or are pending.
"""
from argparse import Namespace
from typing import List, Optional, TypedDict, cast

from tabulate import tabulate

from pyneo4j_ogm.logger import logger
from pyneo4j_ogm.migrations.client import MigrationClient
from pyneo4j_ogm.migrations.models import StatusActionFormat
from pyneo4j_ogm.migrations.utils.config import get_migration_config
from pyneo4j_ogm.migrations.utils.migration import get_migration_files

MAX_FILENAME_LENGTH = 80
MAX_APPLIED_AT_LENGTH = 27


class MigrationState(TypedDict):
    name: str
    applied_at: Optional[str]


def prettify_status(migrations: List[MigrationState]) -> None:
    """
    Visualize the status of all migrations in a pretty format.

    Args:
        migrations(List[MigrationState]): List of migrations and their state
    """
    table: List[List[str]] = []

    for migration in migrations:
        applied_at: str = migration["applied_at"] if migration["applied_at"] is not None else "PENDING"
        table.append([migration["name"], applied_at])

    print(tabulate(table, headers=["Migration", "Applied at"], tablefmt="fancy_grid"))


def raw_status(migrations: List[MigrationState]) -> None:
    """
    Visualize the status of all migrations in raw format.

    Args:
        migrations(List[MigrationState]): List of migrations and their state
    """
    formatted_string = ""

    for migration in migrations:
        applied_at: str = migration["applied_at"] if migration["applied_at"] is not None else "PENDING"
        formatted_string += f"{migration['name']} - {applied_at}\n"

    print(formatted_string)


async def status(namespace: Namespace):
    """
    Visualize the status of all migrations.

    Args:
        namespace(Namespace): Namespace object from argparse
    """
    logger.info("Checking status for migrations")
    migrations: List[MigrationState] = []
    output_format = cast(StatusActionFormat, namespace.format)
    config = get_migration_config(namespace)

    used_format: StatusActionFormat

    logger.debug("Getting format to use")
    if output_format is not None:
        used_format = output_format
    elif config.status_action is not None and config.status_action.default_format is not None:
        used_format = config.status_action.default_format
    else:
        used_format = StatusActionFormat.RAW

    async with MigrationClient(config) as client:
        migration_files = get_migration_files(config.migration_dir)
        migration_node = await client.get_migration_node()

        logger.debug("Checking migration state")
        for migration_name in migration_files:
            if migration_node is None:
                migrations.append({"name": migration_name, "applied_at": None})
            else:
                migration = next(
                    (migration for migration in migration_node.applied_migrations if migration.name == migration_name),
                    None,
                )

                if migration is None:
                    migrations.append({"name": migration_name, "applied_at": None})
                else:
                    migrations.append(
                        {"name": migration_name, "applied_at": migration.applied_at.strftime("%Y-%m-%d %H:%M:%S")}
                    )

        if used_format == StatusActionFormat.PRETTIFY:
            prettify_status(migrations)
        else:
            raw_status(migrations)
