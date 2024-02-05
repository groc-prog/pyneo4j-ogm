"""
Handles the creation of new migration files.
"""

import os
import re
from datetime import datetime
from typing import Dict, Optional

from pyneo4j_ogm.logger import logger
from pyneo4j_ogm.migrations.utils.defaults import MIGRATION_TEMPLATE
from pyneo4j_ogm.migrations.utils.migration import (
    check_initialized,
    get_migration_config,
)


def normalize_filename(name: str) -> str:
    """
    Converts a file name to snake case.

    Args:
        name(str): String to convert

    Returns:
        str: Converted string
    """
    converted = re.sub(r"(.)([A-Z][a-z]+)", r"\1_\2", name)
    converted = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", converted).lower()
    return re.sub(r"\W+", "_", converted)


def create(name: str, config_path: Optional[str] = None) -> Dict[str, str]:
    """
    Creates a new, empty migration file.

    Args:
        name(str): Name of the migration
        config_path(str, optional): Path to the migration config file. Defaults to None.
    """
    check_initialized(config_path=config_path)

    logger.info("Creating new migration file")
    migration_timestamp = str(datetime.now().strftime("%Y%m%d%H%M%S"))
    config = get_migration_config(config_path=config_path)

    logger.debug("Generating migration file name")
    filename = f"{migration_timestamp}-{normalize_filename(name)}.py"
    filepath = os.path.join(config.migration_dir, filename)

    logger.debug("Writing migration file")
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(MIGRATION_TEMPLATE.format(name=filename))

    logger.info("Created new migration file %s at %s", filename, filepath)
    return {"name": filename, "path": filepath}
