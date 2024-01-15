"""
Validation models and constants for the migration configuration file.
"""

from typing import Any, Dict

from pydantic import BaseModel

CONFIG_FILENAME = "migration-config.json"


class Neo4jMigrationConfig(BaseModel):
    """
    Neo4j migration configuration.
    """

    uri: str
    options: Dict[str, Any]


class MigrationConfig(BaseModel):
    """
    Migration configuration.
    """

    neo4j: Neo4jMigrationConfig = Neo4jMigrationConfig(uri="bolt://localhost:7687", options={})
    migration_dir: str
