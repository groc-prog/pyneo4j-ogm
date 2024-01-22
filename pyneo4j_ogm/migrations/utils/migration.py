"""
Constants and utilities for checking if the migrations directory has been initialized.
"""

import importlib.util
import os
from asyncio import iscoroutinefunction
from functools import wraps
from typing import Any, Callable, Dict, TypedDict, Union

from typing_extensions import Literal

from pyneo4j_ogm.exceptions import MigrationNotInitialized
from pyneo4j_ogm.logger import logger
from pyneo4j_ogm.migrations.models import CONFIG_FILENAME

RunMigrationCount = Union[int, Literal["all"]]
MigrationFile = TypedDict("MigrationFile", {"up": Callable, "down": Callable, "name": str})


def check_initialized(func: Callable) -> Callable:
    """
    Checks if the migrations directory has been initialized.

    Args:
        func(Callable): Function to wrap

    Returns:
        Callable: Wrapped function
    """

    logger.debug("Checking if migrations directory and config have been initialized")
    if iscoroutinefunction(func):

        @wraps(func)
        async def async_wrapped(*args: Any, **kwargs: Any) -> Any:
            if not os.path.exists(CONFIG_FILENAME):
                raise MigrationNotInitialized
            return await func(*args, **kwargs)

        return async_wrapped
    else:

        @wraps(func)
        def sync_wrapped(*args: Any, **kwargs: Any) -> Any:
            if not os.path.exists(CONFIG_FILENAME):
                raise MigrationNotInitialized
            return func(*args, **kwargs)

        return sync_wrapped


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
