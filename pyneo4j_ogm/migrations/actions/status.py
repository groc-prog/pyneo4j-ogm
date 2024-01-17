"""
Shows which migrations have been run or are pending.
"""
from argparse import Namespace
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

    logger.debug("Getting format to use")

    async with MigrationClient(config) as client:
        migration_files = get_migration_files(config.migration_dir)
        migration_node = await client.get_migration_node()

        logger.debug("Checking migration state")
        for migration_name in migration_files:
            if migration_node is None:
                migrations.append([migration_name, "PENDING"])
            else:
                migration = next(
                    (migration for migration in migration_node.applied_migrations if migration.name == migration_name),
                    None,
                )

                if migration is None:
                    migrations.append([migration_name, "PENDING"])
                else:
                    migrations.append([migration_name, migration.applied_at.strftime("%Y-%m-%d %H:%M:%S")])

    print(tabulate(migrations, headers=["Migration name", "Applied at"], tablefmt="fancy_grid"))
