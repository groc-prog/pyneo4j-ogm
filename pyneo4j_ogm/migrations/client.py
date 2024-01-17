"""
Utility for Pyneo4jClient used in migrations.
"""

import importlib.util
import inspect
import os
from typing import Any, List, Optional, Type, Union

from pyneo4j_ogm.core.client import Pyneo4jClient
from pyneo4j_ogm.core.node import NodeModel
from pyneo4j_ogm.core.relationship import RelationshipModel
from pyneo4j_ogm.logger import logger
from pyneo4j_ogm.migrations.models import Migration
from pyneo4j_ogm.migrations.utils.config import MigrationConfig
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

        logger.debug("Initializing Pyneo4jClient")
        await self.client.connect(uri=self.config.neo4j.uri, **self.config.neo4j.options or {})
        await self.client.register_models([Migration])
        await self._register_models_dir()

        return self

    async def __aexit__(self, exc_type: Any, exc_value: Any, traceback: Any) -> None:
        await self.client.close()

    async def _register_models_dir(self) -> None:
        """
        Register models from models_dir.
        """
        if self.config.models_dir is None:
            return

        if not os.path.isdir(self.config.models_dir):
            logger.warning("Defined models_dir %s is not a directory", self.config.models_dir)

        logger.debug("Registering models from models_dir %s", self.config.models_dir)
        subclasses: List[Type[Union[NodeModel, RelationshipModel]]] = []

        # Iterate over all Python files in the directory and its subdirectories
        for root, _, files in os.walk(self.config.models_dir):
            for file in files:
                if file.endswith(".py"):
                    file_path = os.path.join(root, file)
                    spec = importlib.util.spec_from_file_location(file[:-3], file_path)

                    if spec is None or spec.loader is None:
                        continue

                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)

                    for _, obj in inspect.getmembers(module):
                        if inspect.isclass(obj):
                            if issubclass(obj, (NodeModel, RelationshipModel)) and obj not in [
                                NodeModel,
                                RelationshipModel,
                            ]:
                                subclasses.append(obj)

        await self.client.register_models(subclasses)

    async def get_migration_node(self) -> Optional[Migration]:
        """
        Get the migration node from the database.

        Returns:
            Optional[Migration]: Migration node if exists, None otherwise.
        """
        logger.debug("Checking for existing migration node")
        migration = await Migration.find_many(
            options={"limit": 1, "sort": "last_applied", "order": QueryOptionsOrder.DESCENDING}
        )

        if len(migration) > 0 and isinstance(migration[0], Migration):
            return migration[0]
        return None
