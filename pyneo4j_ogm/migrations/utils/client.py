"""
Utility for Pyneo4jClient used in migrations.
"""

from typing import Any, Optional, cast

from pyneo4j_ogm.core.client import Pyneo4jClient
from pyneo4j_ogm.core.node import NodeModel
from pyneo4j_ogm.logger import logger
from pyneo4j_ogm.migrations.utils.config import MigrationConfig
from pyneo4j_ogm.queries.types import QueryOptionsOrder


class Migration(NodeModel):
    """
    Migration node model.
    """

    name: str
    last_applied: int

    @property
    def identifier(self) -> int:
        """
        Returns the migration identifier.

        Returns:
            int: Migration identifier
        """
        return int(self.name.split("_")[0])


class MigrationClient:
    """
    Utility for Pyneo4jClient used in migrations.
    """

    def __init__(self, config: MigrationConfig) -> None:
        self.config = config
        self.client = Pyneo4jClient()

    async def __aenter__(self):
        Migration._settings.labels = self.config.neo4j.node_labels

        logger.debug("Initializing Pyneo4jClient")
        await self.client.connect(uri=self.config.neo4j.uri, **self.config.neo4j.options)
        await self.client.register_models([Migration])
        return self

    async def __aexit__(self, exc_type: Any, exc_value: Any, traceback: Any) -> None:
        await self.client.close()

    async def get_migration_node(self) -> Optional[Migration]:
        """
        Returns the migration node.

        Returns:
            Optional[Migration]: Migration node or None if not found
        """
        logger.debug("Searching for migration node")
        migration = await Migration.find_many(
            options={"limit": 1, "sort": "last_applied", "order": QueryOptionsOrder.DESCENDING}
        )

        if len(migration) == 0:
            return None
        return cast(Migration, migration)

    async def update_migration_node(self, name: str) -> None:
        """
        Updates the migration node.

        Args:
            name(str): Migration name
        """
        logger.debug("Updating migration node")
        await Migration.update_many({"name": name})
