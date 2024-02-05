"""
Fixture for setup/teardown of unit tests using temporary paths.
"""

# pylint: disable=redefined-outer-name, unused-import

import json
import os
from typing import cast

import pytest
from neo4j import AsyncSession
from typing_extensions import LiteralString

from pyneo4j_ogm.migrations.utils.defaults import (
    DEFAULT_CONFIG_FILENAME,
    DEFAULT_CONFIG_LABELS,
    DEFAULT_CONFIG_URI,
    DEFAULT_MIGRATION_DIR,
)
from tests.fixtures.db_setup import session

MIGRATION_FILE_NAMES = [
    "20240205190143-mig-one",
    "20240205190146-mig-two",
    "20240205190149-mig-three",
    "20240205190152-mig-four",
    "20240205190156-mig-five",
]
MIGRATION_FILE_NODE_NAMES = ["Bob", "Alice", "Charlie", "David", "Cooper"]
MIGRATION_FILE_TEMPLATE = """
from pyneo4j_ogm.core.client import Pyneo4jClient


async def up(client: Pyneo4jClient) -> None:
    '''
    Write your `UP migration` here.
    '''
    await client.cypher("CREATE (n:Node {{name: '{name}'}})")


async def down(client: Pyneo4jClient) -> None:
    '''
    Write your `DOWN migration` here.
    '''
    await client.cypher("MATCH (n:Node {{name: '{name}'}}) DETACH DELETE n")
"""

CUSTOM_MIGRATION_DIR = "my_migrations"
CUSTOM_CONFIG_FILENAME = "config.json"

LAST_APPLIED = 1707158029.012884
APPLIED_MIGRATIONS = [
    {"name": "20240205190143-mig-one", "applied_at": 1707158029.012881},
    {"name": "20240205190146-mig-two", "applied_at": 1707158029.012884},
]


def insert_migration_config_files(migration_dir_path, config_file_path):
    """
    Inserts the migration directory and config file into the given path.
    """
    with open(os.path.join(migration_dir_path, ".gitkeep"), "w", encoding="utf-8") as f:
        f.write("")
    with open(config_file_path, "w", encoding="utf-8") as f:
        f.write(
            json.dumps(
                {
                    "migration_dir": migration_dir_path,
                    "neo4j": {
                        "uri": DEFAULT_CONFIG_URI,
                        "node_labels": DEFAULT_CONFIG_LABELS,
                        "options": {"scheme": "basic", "auth": {"username": "neo4j", "password": "password"}},
                    },
                }
            )
        )


async def insert_migration_nodes_and_files(session_: AsyncSession, migration_dir_path: str):
    await session_.run("MATCH (n) DETACH DELETE n")
    await session_.run(
        cast(
            LiteralString,
            f"""
        CREATE (m:{':'.join(DEFAULT_CONFIG_LABELS)} {{
            updated_at: $updated_at,
            applied_migrations: $applied_migrations
        }})
        """,
        ),
        {
            "applied_migrations": [json.dumps(migration) for migration in APPLIED_MIGRATIONS],
            "updated_at": LAST_APPLIED,
        },
    )

    for migration_file_name, migration_file_node_name in zip(MIGRATION_FILE_NAMES, MIGRATION_FILE_NODE_NAMES):
        with open(os.path.join(migration_dir_path, f"{migration_file_name}.py"), "w", encoding="utf-8") as f:
            f.write(MIGRATION_FILE_TEMPLATE.format(name=migration_file_node_name))

        if migration_file_name in [applied_migration["name"] for applied_migration in APPLIED_MIGRATIONS]:
            result = await session_.run(
                "CREATE (n:Node {name: $name})",
                {"name": migration_file_node_name},
            )
            await result.consume()


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
        insert_migration_config_files(migration_dir_path, config_file_path)

        yield tmp_path
    finally:
        os.chdir(original_cwd)


@pytest.fixture
def initialized_migration_with_custom_path(tmp_path):
    """
    Fixture for changing the cwd to the temporary path with a custom config path.
    """
    original_cwd = os.getcwd()
    migration_dir_path = os.path.join(tmp_path, CUSTOM_MIGRATION_DIR)
    config_file_path = os.path.join(tmp_path, CUSTOM_CONFIG_FILENAME)

    try:
        os.chdir(tmp_path)
        os.mkdir(migration_dir_path)
        insert_migration_config_files(migration_dir_path, config_file_path)

        yield tmp_path
    finally:
        os.chdir(original_cwd)


@pytest.fixture
async def insert_migrations(initialized_migration, session):
    """
    Fixture for inserting migrations into the database.
    """
    await insert_migration_nodes_and_files(session, os.path.join(initialized_migration, DEFAULT_MIGRATION_DIR))
    yield initialized_migration


@pytest.fixture
async def insert_migrations_with_custom_path(initialized_migration_with_custom_path, session):
    """
    Fixture for inserting migrations into the database with a custom config path.
    """
    await insert_migration_nodes_and_files(
        session, os.path.join(initialized_migration_with_custom_path, CUSTOM_MIGRATION_DIR)
    )
    yield initialized_migration_with_custom_path
