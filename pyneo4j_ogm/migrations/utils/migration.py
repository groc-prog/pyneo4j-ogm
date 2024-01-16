"""
Constants and utilities for checking if the migrations directory has been initialized.
"""

import enum
import importlib.util
import os
from functools import wraps
from typing import Any, Callable, Dict, Union

from typing_extensions import Literal

from pyneo4j_ogm.exceptions import MigrationNotInitialized
from pyneo4j_ogm.logger import logger
from pyneo4j_ogm.migrations.utils.config import DEFAULT_CONFIG_FILENAME

RunMigrationCount = Union[int, Literal["all"]]


class MigrationStatus(enum.Enum):
    """
    Migration status.
    """

    PENDING = "PENDING"
    APPLIED = "APPLIED"


MIGRATION_TEMPLATE = '''"""
Auto-generated migration file 20240115234453_something_awesome.py. Do not
rename this file or the `up` and `down` functions.
"""
from pyneo4j_ogm import Pyneo4jClient


async def up(client: Pyneo4jClient) -> None:
    """
    Write your `UP migration` here.
    """
    pass


async def down(client: Pyneo4jClient) -> None:
    """
    Write your `DOWN migration` here.
    """
    pass
'''


def check_initialized(func: Callable) -> Callable:
    """
    Checks if the migrations directory has been initialized.

    Args:
        func(Callable): Function to wrap

    Returns:
        Callable: Wrapped function
    """

    @wraps(func)
    def wrapped(*args: Any, **kwargs: Any) -> Any:
        if not os.path.exists(DEFAULT_CONFIG_FILENAME):
            raise MigrationNotInitialized
        return func(*args, **kwargs)

    return wrapped


def get_migration_files(directory: str) -> Dict[str, Callable]:
    """
    Returns all migration files in the given directory.

    Args:
        directory(str): Directory to search

    Returns:
        Dict[str, Callable]: Dictionary of migration files
    """
    migrations: Dict[str, Callable] = {}

    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith(".py"):
                filepath = os.path.join(root, file)

                logger.debug("Found migration file %s", filepath)
                module_name = os.path.splitext(os.path.basename(filepath))[0]
                spec = importlib.util.spec_from_file_location(module_name, filepath)

                if spec is None or spec.loader is None:
                    raise ImportError(f"Could not import migration file {filepath}")

                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)

                logger.debug("Adding migration %s to list", module_name)
                migrations[module_name] = module.up

    return migrations
