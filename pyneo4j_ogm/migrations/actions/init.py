"""
Handles the initialization of the migrations directory.
"""

import json
import os

from pyneo4j_ogm.logger import logger
from pyneo4j_ogm.migrations.utils.defaults import (
    DEFAULT_CONFIG_FILENAME,
    DEFAULT_CONFIG_URI,
    DEFAULT_MIGRATION_DIR,
)
from pyneo4j_ogm.migrations.utils.models import MigrationConfig, Neo4jDatabaseConfig
from pyneo4j_ogm.pydantic_utils import get_model_dump_json


def init(migration_dir: str = DEFAULT_MIGRATION_DIR, uri: str = DEFAULT_CONFIG_URI) -> None:
    """
    Initializes the migrations directory.

    Args:
        migration_dir(str): Path to the migrations directory. Defaults to "migrations".
        uri(str): Neo4j database URI. Defaults to "bolt://localhost:7687".
    """
    logger.info("Initializing migrations directory")

    config: MigrationConfig
    root = os.getcwd()

    # Check if a config file already exists, if so use that, otherwise create a new one
    if not os.path.exists(path=os.path.join(root, DEFAULT_CONFIG_FILENAME)):
        logger.debug("No config file found. Creating default config file.")
        config = MigrationConfig(migration_dir=migration_dir, neo4j=Neo4jDatabaseConfig(uri=uri))

        with open(os.path.join(root, DEFAULT_CONFIG_FILENAME), "w", encoding="utf-8") as f:
            f.write(get_model_dump_json(config, exclude_none=True, indent=2))
    else:
        logger.debug("Config file found. Loading config.")
        with open(os.path.join(root, DEFAULT_CONFIG_FILENAME), "r", encoding="utf-8") as f:
            config = MigrationConfig(**json.load(f))

    if not os.path.exists(config.migration_dir):
        logger.debug("Creating migration directory")
        os.makedirs(config.migration_dir, exist_ok=True)

        # Add .gitignore file so the setup does not get omitted of no migration is cerated initially
        logger.debug("Creating .gitkeep file")
        with open(os.path.join(config.migration_dir, ".gitkeep"), "w", encoding="utf-8") as f:
            f.write("")

    logger.info("Initialized migrations directory at %s", os.path.abspath(config.migration_dir))
