"""
Applies the defined number of migrations in correct order.
"""

from argparse import Namespace
from copy import deepcopy
from typing import cast

from pyneo4j_ogm.logger import logger
from pyneo4j_ogm.migrations.client import MigrationClient
from pyneo4j_ogm.migrations.models import AppliedMigration
from pyneo4j_ogm.migrations.utils.config import get_migration_config
from pyneo4j_ogm.migrations.utils.migration import (
    RunMigrationCount,
    check_initialized,
    get_migration_files,
)


@check_initialized
async def up(namespace: Namespace):
    """
    Applies the defined number of migrations in correct order.

    Args:
        namespace(Namespace): Namespace object from argparse
    """
    up_count = cast(RunMigrationCount, namespace.up_count)
    config = get_migration_config(namespace)

    logger.info("Applying next %s migrations", up_count)
    async with MigrationClient(config) as migration_client:
        migration_files = get_migration_files(config.migration_dir)
        migration_node = await migration_client.get_migration_node()

        logger.debug("Filtering migration files for unapplied migrations")
        for applied_migration in migration_node.get_applied_migration_identifiers:
            migration_files.pop(applied_migration, None)

        for count, _ in enumerate(deepcopy(migration_files).values()):
            if up_count != "all" and count >= up_count:
                break

            current_migration_identifier = min(migration_files.keys())
            current_migration = migration_files[current_migration_identifier]

            logger.debug("Applying migration %s", current_migration["name"])
            await current_migration["up"](migration_client.client)
            migration_files.pop(current_migration_identifier)
            migration_node.applied_migrations.append(AppliedMigration(name=current_migration["name"]))

        migration_node.last_applied = migration_node.applied_migrations[-1].applied_at
        await migration_node.update()
