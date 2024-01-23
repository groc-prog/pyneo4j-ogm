# pylint: disable=unused-argument, unused-import, redefined-outer-name, protected-access, missing-module-docstring, missing-class-docstring
# pyright: reportGeneralTypeIssues=false

import os
from unittest.mock import AsyncMock, MagicMock, PropertyMock, patch

import pytest
from neo4j import AsyncSession

from pyneo4j_ogm.core.client import EntityType, Pyneo4jClient
from pyneo4j_ogm.core.node import NodeModel
from pyneo4j_ogm.core.relationship import RelationshipModel
from pyneo4j_ogm.exceptions import (
    MissingDatabaseURI,
    NotConnectedToDatabase,
    UnsupportedNeo4jVersion,
)
from pyneo4j_ogm.fields.property_options import WithOptions
from pyneo4j_ogm.logger import logger
from tests.fixtures.db_setup import client, session


async def test_connection():
    client = await Pyneo4jClient().connect("bolt://localhost:7687", auth=("neo4j", "password"))
    assert client.is_connected
    assert client._driver is not None

    await client.close()
    assert not client.is_connected
    assert client._driver is None

    os.environ["NEO4J_OGM_URI"] = "bolt://localhost:7687"

    client = await Pyneo4jClient().connect(auth=("neo4j", "password"))
    assert client.is_connected
    assert client._driver is not None

    await client.close()
    assert not client.is_connected
    assert client._driver is None

    os.environ.pop("NEO4J_OGM_URI")

    with pytest.raises(MissingDatabaseURI):
        client = await Pyneo4jClient().connect()


async def test_ensure_connection(client: Pyneo4jClient):
    with pytest.raises(NotConnectedToDatabase):
        client = Pyneo4jClient()
        await client.cypher("MATCH (n) RETURN n")

    await client.connect("bolt://localhost:7687", auth=("neo4j", "password"))
    results, _ = await client.cypher("MATCH (n) RETURN n")
    assert results == []

    with pytest.raises(NotConnectedToDatabase):
        await client.close()
        await client.cypher("MATCH (n) RETURN n")


async def test_register_models(client: Pyneo4jClient, session: AsyncSession):
    class ClientNodeModel(NodeModel):
        a: WithOptions(str, unique=True)
        b: WithOptions(str, range_index=True)
        c: WithOptions(str, text_index=True)
        d: WithOptions(str, point_index=True)

        class Settings:
            labels = {"Test", "Node"}

    class ClientRelationshipModel(RelationshipModel):
        a: WithOptions(str, unique=True)
        b: WithOptions(str, range_index=True)
        c: WithOptions(str, text_index=True)
        d: WithOptions(str, point_index=True)

        class Settings:
            type = "TEST_RELATIONSHIP"

    await client.register_models([ClientNodeModel, ClientRelationshipModel])

    assert ClientNodeModel in client.models
    assert ClientRelationshipModel in client.models

    query_results = await session.run("SHOW CONSTRAINTS")
    constraint_results = [result.values() async for result in query_results]
    await query_results.consume()

    assert len(constraint_results) == 3

    query_results = await session.run("SHOW INDEXES")
    index_results = [result.values() async for result in query_results]
    await query_results.consume()

    assert len(index_results) == 12

    assert index_results[8][1] == "ClientRelationshipModel_TEST_RELATIONSHIP_a_unique_constraint"
    assert index_results[8][4] == "RANGE"
    assert index_results[8][5] == EntityType.RELATIONSHIP
    assert index_results[8][6] == ["TEST_RELATIONSHIP"]
    assert index_results[8][7] == ["a"]

    assert index_results[9][1] == "ClientRelationshipModel_TEST_RELATIONSHIP_b_range_index"
    assert index_results[9][4] == "RANGE"
    assert index_results[9][5] == EntityType.RELATIONSHIP
    assert index_results[9][6] == ["TEST_RELATIONSHIP"]
    assert index_results[9][7] == ["b"]

    assert index_results[10][1] == "ClientRelationshipModel_TEST_RELATIONSHIP_c_text_index"
    assert index_results[10][4] == "TEXT"
    assert index_results[10][5] == EntityType.RELATIONSHIP
    assert index_results[10][6] == ["TEST_RELATIONSHIP"]
    assert index_results[10][7] == ["c"]

    assert index_results[11][1] == "ClientRelationshipModel_TEST_RELATIONSHIP_d_point_index"
    assert index_results[11][4] == "POINT"
    assert index_results[11][5] == EntityType.RELATIONSHIP
    assert index_results[11][6] == ["TEST_RELATIONSHIP"]
    assert index_results[11][7] == ["d"]


async def test_supported_neo4j_version():
    mock_driver = MagicMock()
    mock_driver.get_server_info = AsyncMock(return_value=MagicMock(agent="Neo4j/4.0.0"))

    with patch("neo4j.AsyncGraphDatabase.driver", return_value=mock_driver):
        with pytest.raises(UnsupportedNeo4jVersion):
            await Pyneo4jClient().connect("bolt://localhost:7687", auth=("neo4j", "password"))


async def test_close():
    mock_driver = MagicMock()
    mock_driver.close = AsyncMock()

    with patch("pyneo4j_ogm.core.client.Pyneo4jClient.is_connected", new_callable=PropertyMock) as mock_is_connected:
        mock_is_connected.return_value = False
        client = await Pyneo4jClient().connect("bolt://localhost:7687", auth=("neo4j", "password"))

        with patch("neo4j.AsyncGraphDatabase.driver", return_value=mock_driver):
            await client.close()
            mock_driver.close.assert_not_called()

    await client.close()
