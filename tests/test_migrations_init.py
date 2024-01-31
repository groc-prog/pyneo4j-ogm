# pylint: disable=unused-argument, unused-import, redefined-outer-name, protected-access, missing-module-docstring, missing-class-docstring
# pyright: reportGeneralTypeIssues=false

import json
import os

import pytest
from pydantic import ValidationError

from pyneo4j_ogm.migrations import init
from pyneo4j_ogm.migrations.utils.defaults import (
    DEFAULT_CONFIG_FILENAME,
    DEFAULT_CONFIG_LABELS,
    DEFAULT_CONFIG_URI,
    DEFAULT_MIGRATION_DIR,
)
from tests.fixtures.cwd import tmp_cwd


def test_init(tmp_cwd):
    migration_dir_path = os.path.join(tmp_cwd, DEFAULT_MIGRATION_DIR)
    config_file_path = os.path.join(tmp_cwd, DEFAULT_CONFIG_FILENAME)

    init()

    assert os.path.isdir(migration_dir_path)
    assert os.path.isfile(os.path.join(migration_dir_path, ".gitkeep"))
    assert os.path.isfile(config_file_path)

    with open(config_file_path, "r", encoding="utf-8") as f:
        config = json.load(f)

        assert "migration_dir" in config
        assert config["migration_dir"] == DEFAULT_MIGRATION_DIR
        assert "neo4j" in config
        assert "uri" in config["neo4j"]
        assert config["neo4j"]["uri"] == DEFAULT_CONFIG_URI
        assert "node_labels" in config["neo4j"]
        assert config["neo4j"]["node_labels"] == DEFAULT_CONFIG_LABELS
        assert "options" in config["neo4j"]
        assert config["neo4j"]["options"] == {}


def test_existing_migration_dir(tmp_cwd):
    migration_dir_path = os.path.join(tmp_cwd, DEFAULT_MIGRATION_DIR)
    config_file_path = os.path.join(tmp_cwd, DEFAULT_CONFIG_FILENAME)
    os.mkdir(migration_dir_path)

    init()

    with open(config_file_path, "r", encoding="utf-8") as f:
        config = json.load(f)

        assert "migration_dir" in config
        assert config["migration_dir"] == DEFAULT_MIGRATION_DIR
        assert "neo4j" in config
        assert "uri" in config["neo4j"]
        assert config["neo4j"]["uri"] == DEFAULT_CONFIG_URI
        assert "node_labels" in config["neo4j"]
        assert config["neo4j"]["node_labels"] == DEFAULT_CONFIG_LABELS
        assert "options" in config["neo4j"]
        assert config["neo4j"]["options"] == {}


def test_existing_config_file(tmp_cwd):
    custom_migration_dir_path = "foo/bar"
    config_file_path = os.path.join(tmp_cwd, DEFAULT_CONFIG_FILENAME)

    with open(config_file_path, "w", encoding="utf-8") as f:
        f.write(
            json.dumps(
                {
                    "migration_dir": custom_migration_dir_path,
                    "neo4j": {"uri": DEFAULT_CONFIG_URI, "node_labels": DEFAULT_CONFIG_LABELS, "options": {}},
                }
            )
        )

    init()

    migration_dir_path = os.path.join(tmp_cwd, custom_migration_dir_path)
    assert os.path.isdir(migration_dir_path)
    assert os.path.isfile(os.path.join(migration_dir_path, ".gitkeep"))
    assert os.path.isfile(config_file_path)


def test_invalid_existing_config(tmp_cwd):
    config_file_path = os.path.join(tmp_cwd, DEFAULT_CONFIG_FILENAME)

    with open(config_file_path, "w", encoding="utf-8") as f:
        f.write(
            json.dumps(
                {
                    "migration_dir": DEFAULT_MIGRATION_DIR,
                    "neo4j": {"node_labels": DEFAULT_CONFIG_LABELS, "options": {}},
                }
            )
        )

    with pytest.raises(ValidationError):
        init()
