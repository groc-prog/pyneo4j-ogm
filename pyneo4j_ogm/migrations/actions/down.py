"""
Reverts the defined number of migrations in correct order.
"""

from argparse import Namespace
from copy import deepcopy
from datetime import datetime
from typing import cast

from pyneo4j_ogm.logger import logger
from pyneo4j_ogm.migrations.client import MigrationClient
from pyneo4j_ogm.migrations.utils.config import get_migration_config
from pyneo4j_ogm.migrations.utils.migration import (
    RunMigrationCount,
    check_initialized,
    get_migration_files,
)


@check_initialized
async def down(namespace: Namespace):
    """
    Reverts the defined number of migrations in correct order.

    Args:
        namespace(Namespace): Namespace object from argparse
    """
    logger.info("Running DOWN migrations")
    down_count = cast(RunMigrationCount, namespace.down_count)
    config = get_migration_config(namespace)

    async with MigrationClient(config) as migration_client:
        migration_files = get_migration_files(config.migration_dir)
        migration_node = await migration_client.get_migration_node()

        logger.debug("Removing unapplied migrations from migration files")
        applied_migration_identifiers = migration_node.get_applied_migration_identifiers
        for identifier in deepcopy(migration_files).keys():
            if identifier not in applied_migration_identifiers:
                migration_files.pop(identifier, None)

        logger.debug("Reverting last %s migrations", down_count)
        for count, _ in enumerate(deepcopy(migration_files).values()):
            if down_count != "all" and count >= down_count:
                break

            current_migration_identifier = max(migration_files.keys())
            current_migration = migration_files[current_migration_identifier]

            await current_migration["down"](migration_client.client)
            migration_files.pop(current_migration_identifier)
            migration_node.applied_migrations = [
                migration
                for migration in migration_node.applied_migrations
                if migration.name != current_migration["name"]
            ]

        migration_node.last_applied = (
            migration_node.applied_migrations[-1].applied_at
            if len(migration_node.applied_migrations) > 0
            else datetime.timestamp(datetime.now())
        )
        await migration_node.update()
