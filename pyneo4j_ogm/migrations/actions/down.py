"""
Reverts the defined number of migrations in correct order.
"""

from copy import deepcopy
from datetime import datetime
from typing import Optional

from pyneo4j_ogm.logger import logger
from pyneo4j_ogm.migrations.utils.client import MigrationClient
from pyneo4j_ogm.migrations.utils.migration import (
    RunMigrationCount,
    check_initialized,
    get_migration_config,
    get_migration_files,
)


async def down(down_count: RunMigrationCount = "all", config_path: Optional[str] = None) -> None:
    """
    Reverts the defined number of migrations in correct order.

    Args:
        down_count(int, optional): Number of migrations to revert. Can be "all" to revert all migrations.
            Defaults to "all".
        config_path(str, optional): Path to the migration config file. Defaults to None.
    """
    check_initialized(config_path=config_path)
    config = get_migration_config(config_path)

    logger.info("Rolling back %s migrations", down_count)
    async with MigrationClient(config) as migration_client:
        migration_files = get_migration_files(config.migration_dir)
        migration_node = await migration_client.get_migration_node()

        logger.debug("Filtering migration files for applied migrations")
        applied_migration_identifiers = migration_node.get_applied_migration_identifiers
        for identifier in deepcopy(migration_files).keys():
            if identifier not in applied_migration_identifiers:
                migration_files.pop(identifier, None)

        for count, _ in enumerate(deepcopy(migration_files).values()):
            if down_count != "all" and count >= down_count:
                break

            current_migration_identifier = max(migration_files.keys())
            current_migration = migration_files[current_migration_identifier]

            logger.debug("Rolling back migration %s", current_migration["name"])
            await current_migration["down"](migration_client.client)
            migration_files.pop(current_migration_identifier)
            migration_node.applied_migrations = [
                migration
                for migration in migration_node.applied_migrations
                if migration.name != current_migration["name"]
            ]

        migration_node.updated_at = (
            migration_node.applied_migrations[-1].applied_at
            if len(migration_node.applied_migrations) > 0
            else datetime.timestamp(datetime.now())
        )
        await migration_node.update()
