"""
Applies the defined number of migrations in correct order.
"""

import importlib.util
import os
from argparse import Namespace
from typing import Callable, Dict, Generator, cast

from pyneo4j_ogm.logger import logger
from pyneo4j_ogm.migrations.client import MigrationClient
from pyneo4j_ogm.migrations.utils.config import get_migration_config
from pyneo4j_ogm.migrations.utils.migration import RunMigrationCount, check_initialized


@check_initialized
async def up(namespace: Namespace):
    """
    Applies the defined number of migrations in correct order.

    Args:
        namespace(Namespace): Namespace object from argparse
    """
    logger.info("Running UP migrations")
    migrations: Dict[str, Callable] = {}
    up_count = cast(RunMigrationCount, namespace.up_count)
    config = get_migration_config(namespace)
    client = MigrationClient(config)

    logger.debug("Searching for migration node")
    migration_node = await client.get_migration_node()

    # for file in get_migration_files(config.migration_dir):
    #     logger.debug("Found migration file %s", file)
    #     module_name = os.path.splitext(os.path.basename(file))[0]
    #     module_name_timestamp = module_name.split("_")[0]
    #     spec = importlib.util.spec_from_file_location(module_name, file)

    #     if spec is None or spec.loader is None:
    #         raise ImportError(f"Could not import migration file {file}")

    #     module = importlib.util.module_from_spec(spec)
    #     spec.loader.exec_module(module)

    #     logger.debug("Adding migration %s to list", module_name_timestamp)
    #     migrations[module_name_timestamp] = module.up

    # logger.debug("Sorting migrations")
    # sorted_migrations = sorted(migrations.keys())
