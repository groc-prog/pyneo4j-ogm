"""
Shows which migrations have been run or are pending.
"""

from datetime import datetime
from typing import List, Optional, TypedDict

from tabulate import tabulate
from typing_extensions import Literal

from pyneo4j_ogm.logger import logger
from pyneo4j_ogm.migrations.utils.client import MigrationClient
from pyneo4j_ogm.migrations.utils.migration import (
    check_initialized,
    get_migration_config,
    get_migration_files,
)


class MigrationState(TypedDict):
    name: str
    applied_at: Optional[str]


class MigrationStatus(TypedDict):
    name: str
    applied_at: Optional[float]
    status: Literal["APPLIED", "PENDING"]


async def status(config_path: Optional[str] = None) -> List[MigrationStatus]:
    """
    Visualize the status of all migrations.

    Args:
        config_path(str, optional): Path to the migration config file. Defaults to None.
    """
    check_initialized(config_path=config_path)

    logger.info("Checking status for migrations")
    migrations: List[List[str]] = []
    migration_status: List[MigrationStatus] = []
    config = get_migration_config(config_path)

    async with MigrationClient(config) as client:
        migration_files = get_migration_files(config.migration_dir)
        migration_node = await client.get_migration_node()

    logger.debug("Building migration state")
    for _, migration_file in migration_files.items():
        if migration_node is None:
            migrations.append([migration_file["name"], "PENDING"])
            migration_status.append({"name": migration_file["name"], "applied_at": None, "status": "PENDING"})
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
                migration_status.append({"name": migration_file["name"], "applied_at": None, "status": "PENDING"})
            else:
                migrations.append(
                    [
                        migration_file["name"],
                        datetime.fromtimestamp(migration.applied_at).strftime("%Y-%m-%d %H:%M:%S"),
                    ]
                )
                migration_status.append(
                    {
                        "name": migration_file["name"],
                        "applied_at": migration.applied_at,
                        "status": "APPLIED",
                    }
                )

    logger.debug("Sorting %s migrations by applied_at timestamp and name", len(migrations))
    migrations.sort(key=lambda migration: (migration[1], migration[0]))
    print(tabulate(migrations, headers=["Migration", "Applied at"], tablefmt="fancy_grid"))

    migration_status.sort(
        key=lambda migration: (migration["applied_at"] is None, migration["applied_at"], migration["name"])
    )
    return migration_status
