"""
Shows which migrations have been run or are pending.
"""
from argparse import Namespace
from datetime import datetime
from typing import List, Optional, TypedDict

from tabulate import tabulate

from pyneo4j_ogm.logger import logger
from pyneo4j_ogm.migrations.client import MigrationClient
from pyneo4j_ogm.migrations.utils.config import get_migration_config
from pyneo4j_ogm.migrations.utils.migration import get_migration_files


class MigrationState(TypedDict):
    name: str
    applied_at: Optional[str]


async def status(namespace: Namespace):
    """
    Visualize the status of all migrations.

    Args:
        namespace(Namespace): Namespace object from argparse
    """
    logger.info("Checking status for migrations")
    migrations: List[List[str]] = []
    config = get_migration_config(namespace)

    async with MigrationClient(config) as client:
        migration_files = get_migration_files(config.migration_dir)
        migration_node = await client.get_migration_node()

    logger.debug("Checking migration state")
    for _, migration_file in migration_files.items():
        if migration_node is None:
            migrations.append([migration_file["name"], "PENDING"])
        else:
            migration = next(
                (
                    applied_migration
                    for applied_migration in migration_node.applied_migrations
                    if applied_migration.name == migration_file["name"]
                ),
                None,
            )

            if migration is None:
                migrations.append([migration_file["name"], "PENDING"])
            else:
                migrations.append(
                    [
                        migration_file["name"],
                        datetime.fromtimestamp(migration.applied_at).strftime("%Y-%m-%d %H:%M:%S"),
                    ]
                )

    migrations.sort(key=lambda migration: (migration[1], migration[0]))
    print(tabulate(migrations, headers=["Migration", "Applied at"], tablefmt="fancy_grid"))
