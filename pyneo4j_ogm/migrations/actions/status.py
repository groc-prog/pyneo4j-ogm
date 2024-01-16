"""
Shows which migrations have been run or are pending.
"""

from argparse import Namespace
from typing import Dict

from pyneo4j_ogm.logger import logger
from pyneo4j_ogm.migrations.utils.client import MigrationClient
from pyneo4j_ogm.migrations.utils.config import StatusFormat, get_migration_config
from pyneo4j_ogm.migrations.utils.migration import MigrationStatus, get_migration_files


def prettify_status(status_map: Dict[str, MigrationStatus]) -> None:
    """
    Visualize the status of all migrations in a pretty format.

    Args:
        status(Dict[str, MigrationStatus]): Migration status
    """
    formatted_string = ""

    print(formatted_string)


def raw_status(status_map: Dict[str, MigrationStatus]) -> None:
    """
    Visualize the status of all migrations in raw format.

    Args:
        status(Dict[str, MigrationStatus]): Migration status
    """
    formatted_string = ""

    for migration_name, migration_status in status_map.items():
        formatted_string += f"{migration_name} - {migration_status}\n"

    print(formatted_string)


async def status(namespace: Namespace):
    """
    Visualize the status of all migrations.

    Args:
        namespace(Namespace): Namespace object from argparse
    """
    logger.info("Checking status for migrations")
    migration_status: Dict[str, MigrationStatus] = {}
    config = get_migration_config(namespace)

    async with MigrationClient(config) as client:
        migration_node = await client.get_migration_node()
        migration_files = get_migration_files(config.migration_dir)

        for migration_name in migration_files:
            migration_identifier = migration_name.split("_")[0]

            if migration_node is None:
                migration_status[migration_name] = MigrationStatus.PENDING
            elif migration_node.identifier >= int(migration_identifier):
                migration_status[migration_name] = MigrationStatus.APPLIED
            else:
                migration_status[migration_name] = MigrationStatus.PENDING

        if config.status.format == StatusFormat.PRETTIFY:
            prettify_status(migration_status)
        else:
            raw_status(migration_status)
