"""
Utilities for configuration file.
"""

import json
import os
from argparse import Namespace
from typing import Optional, cast

from pyneo4j_ogm.exceptions import MigrationNotInitialized
from pyneo4j_ogm.logger import logger
from pyneo4j_ogm.migrations.models import CONFIG_FILENAME, MigrationConfig


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
        config_path = os.path.join(os.getcwd(), CONFIG_FILENAME)
    else:
        config_path = os.path.abspath(config_path)

    if not os.path.exists(config_path):
        raise MigrationNotInitialized

    logger.debug("Loading migration config from %s", config_path)
    with open(config_path, "r", encoding="utf-8") as f:
        return MigrationConfig(**json.load(f))
