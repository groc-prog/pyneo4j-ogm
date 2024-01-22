"""
Handles the creation of new migration files.
"""
import os
import re
from argparse import Namespace
from datetime import datetime
from typing import cast

from pyneo4j_ogm.logger import logger
from pyneo4j_ogm.migrations.models import MIGRATION_TEMPLATE
from pyneo4j_ogm.migrations.utils.config import get_migration_config
from pyneo4j_ogm.migrations.utils.migration import check_initialized


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


@check_initialized
def create(namespace: Namespace) -> None:
    """
    Creates a new, empty migration file.

    Args:
        namespace(Namespace): Namespace object from argparse
    """
    logger.info("Creating new migration file")
    description = cast(str, namespace.name)
    migration_timestamp = str(datetime.now().strftime("%Y%m%d%H%M%S"))
    config = get_migration_config(namespace)

    logger.debug("Generating migration file name")
    filename = f"{migration_timestamp}-{normalize_filename(description)}.py"
    filepath = os.path.join(config.migration_dir, filename)

    logger.debug("Writing migration file")
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(MIGRATION_TEMPLATE.format(name=filename))

    logger.info("Created new migration file %s at %s", filename, filepath)
