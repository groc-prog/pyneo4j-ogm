# pylint: disable=unused-argument, unused-import, redefined-outer-name, protected-access, missing-module-docstring, missing-class-docstring
# pyright: reportGeneralTypeIssues=false

import json
import os

import pytest

from pyneo4j_ogm.exceptions import MigrationNotInitializedError
from pyneo4j_ogm.migrations import status
from pyneo4j_ogm.migrations.utils.defaults import DEFAULT_CONFIG_LABELS
from tests.fixtures.db_setup import session
from tests.fixtures.migrations import (
    APPLIED_MIGRATIONS,
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


async def test_status(tmp_cwd, insert_migrations, session):
    result = await status()

    assert len(result) == 5
    assert result[0] == {
        "name": APPLIED_MIGRATIONS[0]["name"],
        "applied_at": APPLIED_MIGRATIONS[0]["applied_at"],
        "status": "APPLIED",
    }
    assert result[1] == {
        "name": APPLIED_MIGRATIONS[1]["name"],
        "applied_at": APPLIED_MIGRATIONS[1]["applied_at"],
        "status": "APPLIED",
    }
    assert result[2] == {"name": MIGRATION_FILE_NAMES[2], "applied_at": None, "status": "PENDING"}
    assert result[3] == {"name": MIGRATION_FILE_NAMES[3], "applied_at": None, "status": "PENDING"}
    assert result[4] == {"name": MIGRATION_FILE_NAMES[4], "applied_at": None, "status": "PENDING"}


async def test_fails_if_not_initialized(tmp_cwd):
    with pytest.raises(MigrationNotInitializedError):
        await status()


async def test_with_custom_path(tmp_cwd, insert_migrations_with_custom_path, session):
    result = await status(os.path.join(tmp_cwd, CUSTOM_CONFIG_FILENAME))

    assert len(result) == 5
    assert result[0] == {
        "name": APPLIED_MIGRATIONS[0]["name"],
        "applied_at": APPLIED_MIGRATIONS[0]["applied_at"],
        "status": "APPLIED",
    }
    assert result[1] == {
        "name": APPLIED_MIGRATIONS[1]["name"],
        "applied_at": APPLIED_MIGRATIONS[1]["applied_at"],
        "status": "APPLIED",
    }
    assert result[2] == {"name": MIGRATION_FILE_NAMES[2], "applied_at": None, "status": "PENDING"}
    assert result[3] == {"name": MIGRATION_FILE_NAMES[3], "applied_at": None, "status": "PENDING"}
    assert result[4] == {"name": MIGRATION_FILE_NAMES[4], "applied_at": None, "status": "PENDING"}
