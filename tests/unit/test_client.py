# pylint: disable=protected-access, missing-module-docstring

import os

import pytest

from pyneo4j_ogm.core.client import Neo4jClient
from pyneo4j_ogm.exceptions import MissingDatabaseURI

pytest_plugins = ("pytest_asyncio",)


async def test_connection():
    pyneo4j_client = Neo4jClient().connect("bolt://localhost:7687", auth=("neo4j", "password"))
    assert pyneo4j_client.is_connected
    assert pyneo4j_client._driver is not None

    await pyneo4j_client.close()
    assert not pyneo4j_client.is_connected
    assert pyneo4j_client._driver is None

    # Test that the Neo4jClient can connect to a database using ENV variables.
    os.environ["NEO4J_OGM_URI"] = "bolt://localhost:7687"

    pyneo4j_client = Neo4jClient().connect(auth=("neo4j", "password"))
    assert pyneo4j_client.is_connected
    assert pyneo4j_client._driver is not None

    await pyneo4j_client.close()
    assert not pyneo4j_client.is_connected
    assert pyneo4j_client._driver is None

    os.environ.pop("NEO4J_OGM_URI")

    with pytest.raises(MissingDatabaseURI):
        # Test raised exception when no URI is provided.
        pyneo4j_client = Neo4jClient().connect()
