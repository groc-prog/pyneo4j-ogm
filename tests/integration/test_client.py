"""
Integration tests for neo4j_ogm.core.client.
"""

# pylint: disable=unused-argument, unused-import, redefined-outer-name, protected-access

import os
from typing import Any, AsyncGenerator

import pytest

from neo4j_ogm.core.client import EntityType, IndexType, Neo4jClient
from neo4j_ogm.exceptions import MissingDatabaseURI, NotConnectedToDatabase
from tests.integration.fixtures.database import database_client
from tests.integration.fixtures.models import TestNodeModel, TestRelationshipModel

pytest_plugins = ("pytest_asyncio",)


@pytest.mark.asyncio
async def test_connection():
    """
    Test that the Neo4jClient can connect to a database.
    """
    client = Neo4jClient().connect("bolt://localhost:7687", auth=("neo4j", "password"))
    assert client.is_connected
    assert client._driver is not None

    await client.close()
    assert not client.is_connected
    assert client._driver is None

    # Test that the Neo4jClient can connect to a database using ENV variables.
    os.environ["NEO4J_OGM_URI"] = "bolt://localhost:7687"

    client = Neo4jClient().connect(auth=("neo4j", "password"))
    assert client.is_connected
    assert client._driver is not None

    await client.close()
    assert not client.is_connected
    assert client._driver is None

    os.environ.pop("NEO4J_OGM_URI")

    with pytest.raises(MissingDatabaseURI):
        # Test raised exception when no URI is provided.
        client = Neo4jClient().connect()


@pytest.mark.asyncio
async def test_ensure_connection(database_client: AsyncGenerator[Neo4jClient, Any]):
    """
    Test that the Neo4jClient raises an exception when attempting to execute a query
    without first connecting to a database.
    """
    with pytest.raises(NotConnectedToDatabase):
        client = Neo4jClient()
        await client.cypher("MATCH (n) RETURN n")

    client = await anext(database_client)
    with pytest.raises(NotConnectedToDatabase):
        await client.close()
        await client.cypher("MATCH (n) RETURN n")

    client.connect("bolt://localhost:7687", auth=("neo4j", "password"))
    results, _ = await client.cypher("MATCH (n) RETURN n")
    assert results == []


@pytest.mark.asyncio
async def test_register_models(database_client: AsyncGenerator[Neo4jClient, Any]):
    """
    Test that the Neo4jClient correctly registers models.
    """
    client = await anext(database_client)
    await client.register_models([TestNodeModel, TestRelationshipModel])

    assert TestNodeModel in client.models
    assert TestRelationshipModel in client.models

    results, _ = await client.cypher("SHOW CONSTRAINTS")

    assert len(results) == 3

    assert results[0][1] == "TestNodeModel_Node_a_unique_constraint"
    assert results[0][2] == "UNIQUENESS"
    assert results[0][3] == EntityType.NODE
    assert results[0][4] == ["Node"]
    assert results[0][5] == ["a"]

    assert results[1][1] == "TestNodeModel_Test_a_unique_constraint"
    assert results[1][2] == "UNIQUENESS"
    assert results[1][3] == EntityType.NODE
    assert results[1][4] == ["Test"]
    assert results[1][5] == ["a"]

    assert results[2][1] == "TestRelationshipModel_TEST_RELATIONSHIP_a_unique_constraint"
    assert results[2][2] == "RELATIONSHIP_UNIQUENESS"
    assert results[2][3] == EntityType.RELATIONSHIP
    assert results[2][4] == ["TEST_RELATIONSHIP"]
    assert results[2][5] == ["a"]

    results, _ = await client.cypher("SHOW INDEXES")

    assert len(results) == 12

    # Indexes for 'Node' label
    assert results[0][1] == "TestNodeModel_Node_a_unique_constraint"
    assert results[0][4] == IndexType.RANGE
    assert results[0][5] == EntityType.NODE
    assert results[0][6] == ["Node"]
    assert results[0][7] == ["a"]

    assert results[1][1] == "TestNodeModel_Node_b_range_index"
    assert results[1][4] == IndexType.RANGE
    assert results[1][5] == EntityType.NODE
    assert results[1][6] == ["Node"]
    assert results[1][7] == ["b"]

    assert results[2][1] == "TestNodeModel_Node_c_text_index"
    assert results[2][4] == IndexType.TEXT
    assert results[2][5] == EntityType.NODE
    assert results[2][6] == ["Node"]
    assert results[2][7] == ["c"]

    assert results[3][1] == "TestNodeModel_Node_d_point_index"
    assert results[3][4] == IndexType.POINT
    assert results[3][5] == EntityType.NODE
    assert results[3][6] == ["Node"]
    assert results[3][7] == ["d"]

    # Indexes for 'Test' label
    assert results[4][1] == "TestNodeModel_Test_a_unique_constraint"
    assert results[4][4] == IndexType.RANGE
    assert results[4][5] == EntityType.NODE
    assert results[4][6] == ["Test"]
    assert results[4][7] == ["a"]

    assert results[5][1] == "TestNodeModel_Test_b_range_index"
    assert results[5][4] == IndexType.RANGE
    assert results[5][5] == EntityType.NODE
    assert results[5][6] == ["Test"]
    assert results[5][7] == ["b"]

    assert results[6][1] == "TestNodeModel_Test_c_text_index"
    assert results[6][4] == IndexType.TEXT
    assert results[6][5] == EntityType.NODE
    assert results[6][6] == ["Test"]
    assert results[6][7] == ["c"]

    assert results[7][1] == "TestNodeModel_Test_d_point_index"
    assert results[7][4] == IndexType.POINT
    assert results[7][5] == EntityType.NODE
    assert results[7][6] == ["Test"]
    assert results[7][7] == ["d"]

    # Indexes for 'TEST_RELATIONSHIP' type
    assert results[8][1] == "TestRelationshipModel_TEST_RELATIONSHIP_a_unique_constraint"
    assert results[8][4] == IndexType.RANGE
    assert results[8][5] == EntityType.RELATIONSHIP
    assert results[8][6] == ["TEST_RELATIONSHIP"]
    assert results[8][7] == ["a"]

    assert results[9][1] == "TestRelationshipModel_TEST_RELATIONSHIP_b_range_index"
    assert results[9][4] == IndexType.RANGE
    assert results[9][5] == EntityType.RELATIONSHIP
    assert results[9][6] == ["TEST_RELATIONSHIP"]
    assert results[9][7] == ["b"]

    assert results[10][1] == "TestRelationshipModel_TEST_RELATIONSHIP_c_text_index"
    assert results[10][4] == IndexType.TEXT
    assert results[10][5] == EntityType.RELATIONSHIP
    assert results[10][6] == ["TEST_RELATIONSHIP"]
    assert results[10][7] == ["c"]

    assert results[11][1] == "TestRelationshipModel_TEST_RELATIONSHIP_d_point_index"
    assert results[11][4] == IndexType.POINT
    assert results[11][5] == EntityType.RELATIONSHIP
    assert results[11][6] == ["TEST_RELATIONSHIP"]
    assert results[11][7] == ["d"]
