"""
Validation models and constants for the migration configuration file.
"""

import enum
import json
import os
from argparse import Namespace
from typing import Any, Dict, Optional, Set, cast

from pydantic import BaseModel

from pyneo4j_ogm.exceptions import MigrationNotInitialized
from pyneo4j_ogm.logger import logger

DEFAULT_CONFIG_FILENAME = "migration-config.json"


class StatusFormat(enum.Enum):
    """
    Status format.
    """

    RAW = "RAW"
    PRETTIFY = "PRETTIFY"


class Neo4jMigrationConfig(BaseModel):
    """
    Neo4j migration configuration.
    """

    uri: str = "bolt://localhost:7687"
    options: Dict[str, Any] = {}
    node_labels: Set[str] = {"migration"}


class StatusConfig(BaseModel):
    """
    Status command configuration.
    """

    format: StatusFormat = StatusFormat.PRETTIFY


class MigrationConfig(BaseModel):
    """
    Migration configuration.
    """

    neo4j: Neo4jMigrationConfig = Neo4jMigrationConfig()
    migration_dir: str
    status: StatusConfig = StatusConfig()


def get_migration_config(namespace: Namespace) -> MigrationConfig:
    """
    Returns the migration configuration.

    Args:
        namespace(Namespace): Namespace object from argparse

    Raises:
        MigrationNotInitialized: If the migration directory has not been initialized.

    Returns:
        MigrationConfig: Migration configuration
    """
    logger.debug("Attempting to load migration config")
    config_path = cast(Optional[str], namespace.config_path)

    if config_path is None:
        config_path = os.path.join(os.getcwd(), DEFAULT_CONFIG_FILENAME)
    else:
        config_path = os.path.abspath(config_path)

    if not os.path.exists(config_path):
        raise MigrationNotInitialized

    logger.debug("Loading migration config from %s", config_path)
    with open(config_path, "r", encoding="utf-8") as f:
        return MigrationConfig(**json.load(f))
