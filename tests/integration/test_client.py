"""
Integration tests for neo4j_ogm.core.client.
"""
import os

import pytest

from neo4j_ogm.core.client import Neo4jClient
from neo4j_ogm.exceptions import MissingDatabaseURI, NotConnectedToDatabase

pytest_plugins = ("pytest_asyncio",)


@pytest.mark.asyncio
async def test_connection():
    """
    Test that the Neo4jClient can connect to a database.
    """
    client = Neo4jClient().connect("bolt://localhost:7687", ("neo4j", "password"))
    assert client.is_connected

    await client.close()
    assert not client.is_connected

    # Test that the Neo4jClient can connect to a database using ENV variables.
    os.environ["NEO4J_OGM_URI"] = "bolt://localhost:7687"
    os.environ["NEO4J_OGM_USERNAME"] = "neo4j"
    os.environ["NEO4J_OGM_PASSWORD"] = "password"

    client = Neo4jClient().connect()
    assert client.is_connected

    await client.close()
    assert not client.is_connected

    os.environ.pop("NEO4J_OGM_URI")
    os.environ.pop("NEO4J_OGM_USERNAME")
    os.environ.pop("NEO4J_OGM_PASSWORD")

    with pytest.raises(MissingDatabaseURI):
        # Test raised exception when no URI is provided.
        client = Neo4jClient().connect()


@pytest.mark.asyncio
async def test_ensure_connection():
    """
    Test that the Neo4jClient raises an exception when attempting to execute a query
    without first connecting to a database.
    """
    with pytest.raises(NotConnectedToDatabase):
        client = Neo4jClient()
        await client.cypher("MATCH (n) RETURN n")

    with pytest.raises(NotConnectedToDatabase):
        client = Neo4jClient().connect("bolt://localhost:7687", ("neo4j", "password"))
        await client.close()
        await client.cypher("MATCH (n) RETURN n")
