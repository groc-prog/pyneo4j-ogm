"""
Utilities for checking if the migrations directory has been initialized.
"""

import importlib.util
import json
import os
from typing import Callable, Dict, Optional, TypedDict, Union

from typing_extensions import Literal

from pyneo4j_ogm.exceptions import MigrationNotInitialized
from pyneo4j_ogm.logger import logger
from pyneo4j_ogm.migrations.utils.defaults import DEFAULT_CONFIG_FILENAME
from pyneo4j_ogm.migrations.utils.models import MigrationConfig

RunMigrationCount = Union[int, Literal["all"]]
MigrationFile = TypedDict("MigrationFile", {"up": Callable, "down": Callable, "name": str})


def check_initialized(config_path: Optional[str]) -> None:
    """
    Checks if the migrations directory has been initialized.

    Args:
        config_path(str, optional): Path to the migration config file. Defaults to None.
    """
    logger.debug("Checking if migrations directory and config have been initialized")
    if config_path is not None:
        if not os.path.exists(config_path):
            raise MigrationNotInitialized
    else:
        if not os.path.exists(DEFAULT_CONFIG_FILENAME):
            raise MigrationNotInitialized


def get_migration_files(directory: str) -> Dict[str, MigrationFile]:
    """
    Returns all migration files in the given directory.

    Args:
        directory(str): Directory to search

    Returns:
        Dict[str, MigrationFile]: Dictionary of migration files
    """
    migrations: Dict[str, MigrationFile] = {}

    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith(".py"):
                filepath = os.path.join(root, file)

                logger.debug("Found migration file %s", filepath)
                module_name = os.path.splitext(os.path.basename(filepath))[0]
                module_timestamp = module_name.split("-")[0]
                spec = importlib.util.spec_from_file_location(module_name, filepath)

                if spec is None or spec.loader is None:
                    raise ImportError(f"Could not import migration file {filepath}")

                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)

                logger.debug("Adding migration %s to list", module_name)
                migrations[module_timestamp] = {
                    "name": module_name,
                    "up": getattr(module, "up"),
                    "down": getattr(module, "down"),
                }

    return migrations


def get_migration_config(config_path: Optional[str]) -> MigrationConfig:
    """
    Returns the migration configuration.

    Args:
        config_path(str, optional): Path to the migration config file.

    Raises:
        MigrationNotInitialized: If the migration directory has not been initialized.

    Returns:
        MigrationConfig: Migration configuration
    """
    logger.debug("Attempting to load migration config")

    if config_path is None:
        config_path = os.path.join(os.getcwd(), DEFAULT_CONFIG_FILENAME)
    else:
        config_path = os.path.abspath(config_path)

    if not os.path.exists(config_path):
        raise MigrationNotInitialized

    logger.debug("Loading migration config from %s", config_path)
    with open(config_path, "r", encoding="utf-8") as f:
        return MigrationConfig(**json.load(f))
