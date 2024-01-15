"""
Handles the initialization of the migrations directory.
"""
import json
import os
import shutil
from argparse import Namespace
from typing import cast

from pyneo4j_ogm.exceptions import MigrationDirectoryExists
from pyneo4j_ogm.logger import logger

DEFAULT_MIGRATION = {
    "neo4j": {"uri": "bolt://localhost:7687", "options": {}},
}


def init(namespace: Namespace) -> None:
    """
    Initializes the migrations directory.
    """
    logger.info("Initializing migrations directory")
    root = os.getcwd()
    migration_path = cast(str, namespace.path)
    overwrite = cast(bool, namespace.overwrite)

    if not os.path.exists(path=os.path.join(root, "migration-config.json")):
        logger.debug("No config file found. Creating default config file.")
        with open(os.path.join(root, "migration.json"), "w", encoding="utf-8") as f:
            f.write(
                json.dumps(
                    {
                        **DEFAULT_MIGRATION,
                        "migration_dir": migration_path,
                    },
                    indent=4,
                )
            )

    if os.path.exists(migration_path):
        if overwrite:
            logger.debug("Overwriting existing migration directory")
            shutil.rmtree(migration_path)
        else:
            raise MigrationDirectoryExists(path=migration_path)

    logger.debug("Creating migration directory")
    os.mkdir(migration_path)
