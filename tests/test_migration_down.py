# pylint: disable=unused-argument, unused-import, redefined-outer-name, protected-access, missing-module-docstring, missing-class-docstring
# pyright: reportGeneralTypeIssues=false

import json
import os

import pytest

from pyneo4j_ogm.exceptions import MigrationNotInitialized
from pyneo4j_ogm.migrations import down
from pyneo4j_ogm.migrations.utils.defaults import DEFAULT_CONFIG_LABELS
from tests.fixtures.db_setup import session
from tests.fixtures.migrations import (
    CUSTOM_CONFIG_FILENAME,
    LAST_APPLIED,
    MIGRATION_FILE_NAMES,
    MIGRATION_FILE_NODE_NAMES,
    initialized_migration,
    initialized_migration_with_custom_path,
    insert_migrations,
    insert_migrations_with_custom_path,
    tmp_cwd,
)


async def test_down(tmp_cwd, insert_migrations, session):
    await down(1)

    result = await session.run(f"MATCH (n:{':'.join(DEFAULT_CONFIG_LABELS)}) RETURN n")
    query_results = await result.values()
    await result.consume()

    applied_migrations = [json.loads(migration) for migration in query_results[0][0]["applied_migrations"]]

    assert len(query_results) == 1
    assert query_results[0][0].labels == set(DEFAULT_CONFIG_LABELS)
    assert query_results[0][0]["updated_at"] != LAST_APPLIED
    assert len(applied_migrations) == 1

    result = await session.run("MATCH (n:Node) WHERE n.name IN $names RETURN n", {"names": MIGRATION_FILE_NODE_NAMES})
    query_results = await result.values()
    await result.consume()

    assert len(query_results) == 1
    assert query_results[0][0]["name"] == MIGRATION_FILE_NODE_NAMES[0]


async def test_down_count_all(tmp_cwd, insert_migrations, session):
    await down("all")

    result = await session.run(f"MATCH (n:{':'.join(DEFAULT_CONFIG_LABELS)}) RETURN n")
    query_results = await result.values()
    await result.consume()

    applied_migrations = [json.loads(migration) for migration in query_results[0][0]["applied_migrations"]]

    assert len(query_results) == 1
    assert query_results[0][0].labels == set(DEFAULT_CONFIG_LABELS)
    assert query_results[0][0]["updated_at"] != LAST_APPLIED
    assert len(applied_migrations) == 0

    result = await session.run("MATCH (n:Node) WHERE n.name IN $names RETURN n", {"names": MIGRATION_FILE_NODE_NAMES})
    query_results = await result.values()
    await result.consume()

    assert len(query_results) == 0


async def test_fails_if_not_initialized(tmp_cwd):
    with pytest.raises(MigrationNotInitialized):
        await down()


async def test_with_custom_path(tmp_cwd, insert_migrations_with_custom_path, session):
    await down(1, os.path.join(tmp_cwd, CUSTOM_CONFIG_FILENAME))

    result = await session.run(f"MATCH (n:{':'.join(DEFAULT_CONFIG_LABELS)}) RETURN n")
    query_results = await result.values()
    await result.consume()

    applied_migrations = [json.loads(migration) for migration in query_results[0][0]["applied_migrations"]]

    assert len(query_results) == 1
    assert query_results[0][0].labels == set(DEFAULT_CONFIG_LABELS)
    assert query_results[0][0]["updated_at"] != LAST_APPLIED
    assert len(applied_migrations) == 1

    result = await session.run("MATCH (n:Node) WHERE n.name IN $names RETURN n", {"names": MIGRATION_FILE_NODE_NAMES})
    query_results = await result.values()
    await result.consume()

    assert len(query_results) == 1
    assert query_results[0][0]["name"] == MIGRATION_FILE_NODE_NAMES[0]
