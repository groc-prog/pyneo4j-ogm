"""
Utility for checking if the migrations directory has been initialized.
"""

import json
import os
from functools import wraps
from typing import Any, Callable

from pyneo4j_ogm.exceptions import MigrationNotInitialized
from pyneo4j_ogm.migrations.utils.config import CONFIG_FILENAME, MigrationConfig

MIGRATION_TEMPLATE = '''"""
Auto-generated migration file 20240115234453_something_awesome.py. `DO NOT RENAME` this file.
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
        if not os.path.exists(CONFIG_FILENAME):
            raise MigrationNotInitialized
        return func(*args, **kwargs)

    return wrapped


def provide_config(func: Callable) -> Callable:
    """
    Provides the config to the wrapped function.

    Args:
        func(Callable): Function to wrap

    Returns:
        Callable: Wrapped function
    """

    @wraps(func)
    def wrapped(*args: Any, **kwargs: Any) -> Any:
        if not os.path.exists(CONFIG_FILENAME):
            raise MigrationNotInitialized

        with open(CONFIG_FILENAME, "r", encoding="utf-8") as f:
            kwargs["config"] = MigrationConfig(**json.load(f))

        return func(*args, **kwargs)

    return wrapped
