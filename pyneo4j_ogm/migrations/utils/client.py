"""
Utility for Pyneo4jClient used in migrations.
"""

from typing import Any

from pyneo4j_ogm.core.client import Pyneo4jClient
from pyneo4j_ogm.migrations.utils.models import Migration, MigrationConfig
from pyneo4j_ogm.queries.types import QueryOptionsOrder


class MigrationClient:
    """
    Utility for Pyneo4jClient used in migrations.
    """

    config: MigrationConfig
    client: Pyneo4jClient

    def __init__(self, config: MigrationConfig) -> None:
        self.client = Pyneo4jClient()
        self.config = config

    async def __aenter__(self):
        Migration._settings.labels = set(self.config.neo4j.node_labels)

        await self.client.connect(uri=self.config.neo4j.uri, **self.config.neo4j.options or {})
        await self.client.register_models([Migration])

        return self

    async def __aexit__(self, exc_type: Any, exc_value: Any, traceback: Any) -> None:
        await self.client.close()

    async def get_migration_node(self) -> Migration:
        """
        Get the migration node from the database.

        Returns:
            Migration: If a migration node exists, it will be returned. Otherwise, a
                new migration node will be created and returned.
        """
        migration = await Migration.find_many(
            options={"limit": 1, "sort": "last_applied", "order": QueryOptionsOrder.DESCENDING}
        )

        if len(migration) > 0 and isinstance(migration[0], Migration):
            return migration[0]

        migration = Migration()
        await migration.create()

        return migration
