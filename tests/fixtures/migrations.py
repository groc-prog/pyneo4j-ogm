"""
Fixture for setup/teardown of unit tests using temporary paths.
"""

# pylint: disable=redefined-outer-name

import json
import os

import pytest

from pyneo4j_ogm.migrations.utils.defaults import (
    DEFAULT_CONFIG_FILENAME,
    DEFAULT_CONFIG_LABELS,
    DEFAULT_CONFIG_URI,
    DEFAULT_MIGRATION_DIR,
)


@pytest.fixture
def tmp_cwd(tmp_path):
    """
    Fixture for changing the cwd to the temporary path.
    """
    original_cwd = os.getcwd()

    try:
        os.chdir(tmp_path)
        yield tmp_path
    finally:
        os.chdir(original_cwd)


@pytest.fixture
def initialized_migration(tmp_path):
    """
    Fixture for changing the cwd to the temporary path.
    """
    original_cwd = os.getcwd()
    migration_dir_path = os.path.join(tmp_path, DEFAULT_MIGRATION_DIR)
    config_file_path = os.path.join(tmp_path, DEFAULT_CONFIG_FILENAME)

    try:
        os.chdir(tmp_path)
        os.mkdir(migration_dir_path)
        with open(os.path.join(migration_dir_path, ".gitkeep"), "w", encoding="utf-8") as f:
            f.write("")
        with open(config_file_path, "w", encoding="utf-8") as f:
            f.write(
                json.dumps(
                    {
                        "migration_dir": DEFAULT_MIGRATION_DIR,
                        "neo4j": {
                            "uri": DEFAULT_CONFIG_URI,
                            "node_labels": DEFAULT_CONFIG_LABELS,
                            "options": {"auth": ["neo4j", "password"]},
                        },
                    }
                )
            )

        yield tmp_path
    finally:
        os.chdir(original_cwd)
