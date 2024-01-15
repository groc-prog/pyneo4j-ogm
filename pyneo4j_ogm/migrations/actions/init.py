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
from pyneo4j_ogm.migrations.utils.config import CONFIG_FILENAME, MigrationConfig
from pyneo4j_ogm.pydantic_utils import get_model_dump_json


def init(namespace: Namespace) -> None:
    """
    Initializes the migrations directory.
    """
    logger.info("Initializing migrations directory")

    config: MigrationConfig
    root = os.getcwd()
    migration_path = cast(str, namespace.path)
    overwrite = cast(bool, namespace.overwrite)

    if not os.path.exists(path=os.path.join(root, CONFIG_FILENAME)):
        logger.debug("No config file found. Creating default config file.")
        config = MigrationConfig(migration_dir=migration_path)

        with open(os.path.join(root, CONFIG_FILENAME), "w", encoding="utf-8") as f:
            f.write(get_model_dump_json(config, indent=2))
    else:
        logger.debug("Config file found. Loading config.")
        with open(os.path.join(root, CONFIG_FILENAME), "r", encoding="utf-8") as f:
            config = MigrationConfig(**json.load(f))

    if os.path.exists(config.migration_dir):
        if overwrite:
            logger.debug("Overwriting existing migration directory")
            shutil.rmtree(config.migration_dir)
        else:
            raise MigrationDirectoryExists(path=config.migration_dir)

    logger.debug("Creating migration directory")
    os.makedirs(config.migration_dir, exist_ok=True)

    logger.debug("Creating .gitkeep file")
    with open(os.path.join(config.migration_dir, ".gitkeep"), "w", encoding="utf-8") as f:
        f.write("")

    logger.info("Initialized migrations directory at %s", os.path.abspath(config.migration_dir))
