# pylint: disable=unused-argument, unused-import, redefined-outer-name, protected-access, missing-module-docstring
# pyright: reportGeneralTypeIssues=false

import json
from typing import Any, Dict, List
from unittest.mock import patch

import pytest
from neo4j import AsyncSession
from neo4j.graph import Node

from pyneo4j_ogm.core.client import Pyneo4jClient
from pyneo4j_ogm.core.node import NodeModel
from pyneo4j_ogm.exceptions import NoResultsFound
from tests.fixtures.db_clients import neo4j_session, pyneo4j_client

pytest_plugins = ("pytest_asyncio",)


class CreateNodeTest(NodeModel):
    str_prop: str
    int_prop: int
    bool_prop: bool
    dict_prop: Dict[str, Any]

    class Settings:
        labels = {"Test"}


class UpdateNodeTest(NodeModel):
    my_prop: str = "default"

    class Settings:
        labels = {"Test"}


class DeleteNodeTest(NodeModel):
    class Settings:
        labels = {"Test"}


async def test_create(pyneo4j_client: Pyneo4jClient, neo4j_session: AsyncSession):
    dict_prop = {"key1": "value1", "key2": 2, "key3": [1, 2, 3]}

    await pyneo4j_client.register_models([CreateNodeTest])

    node = CreateNodeTest(str_prop="string", int_prop=1, bool_prop=True, dict_prop=dict_prop)
    await node.create()

    assert node._element_id is not None
    assert node._id is not None
    assert node._db_properties == {
        "str_prop": "string",
        "int_prop": 1,
        "bool_prop": True,
        "dict_prop": dict_prop,
    }

    results = await neo4j_session.run("MATCH (n:Test) RETURN n")
    query_result: List[List[Node]] = await results.values()

    assert len(query_result) == 1
    assert len(query_result[0]) == 1

    node_result = query_result[0][0]
    assert isinstance(node_result, Node)
    assert node_result.element_id == node._element_id
    assert node_result.id == node._id

    assert node_result["str_prop"] == "string"
    assert node_result["int_prop"] == 1
    assert node_result["bool_prop"]
    assert node_result["dict_prop"] == json.dumps(dict_prop)


async def test_create_no_result(pyneo4j_client: Pyneo4jClient):
    with patch.object(pyneo4j_client, "cypher") as mock_cypher:
        mock_cypher.return_value = ([], [])

        await pyneo4j_client.register_models([CreateNodeTest])

        node = CreateNodeTest(str_prop="string", int_prop=1, bool_prop=True, dict_prop={"key": "value"})

        with pytest.raises(NoResultsFound):
            await node.create()


async def test_update(pyneo4j_client: Pyneo4jClient, neo4j_session: AsyncSession):
    await pyneo4j_client.register_models([UpdateNodeTest])

    node = UpdateNodeTest()
    await node.create()
    assert node.my_prop == "default"

    node.my_prop = "new value"
    await node.update()
    assert node.my_prop == "new value"
    assert node._db_properties == {"my_prop": "new value"}

    results = await neo4j_session.run("MATCH (n:Test) RETURN n")
    query_result: List[List[Node]] = await results.values()

    assert len(query_result) == 1
    assert len(query_result[0]) == 1

    node_result = query_result[0][0]
    assert node_result["my_prop"] == "new value"


async def test_update_no_result(pyneo4j_client: Pyneo4jClient):
    await pyneo4j_client.register_models([UpdateNodeTest])

    node = UpdateNodeTest()
    await node.create()
    assert node.my_prop == "default"

    with patch.object(pyneo4j_client, "cypher") as mock_cypher:
        mock_cypher.return_value = ([], [])

        with pytest.raises(NoResultsFound):
            node.my_prop = "new value"
            await node.update()


async def test_delete(pyneo4j_client: Pyneo4jClient, neo4j_session: AsyncSession):
    await pyneo4j_client.register_models([DeleteNodeTest])

    node = DeleteNodeTest()
    await node.create()
    assert node._destroyed is False

    await node.delete()
    assert node._destroyed

    results = await neo4j_session.run("MATCH (n:Test) RETURN n")
    query_result: List[List[Node]] = await results.values()

    assert len(query_result) == 0


async def test_delete_no_result(pyneo4j_client: Pyneo4jClient):
    await pyneo4j_client.register_models([DeleteNodeTest])

    node = DeleteNodeTest()
    await node.create()

    with patch.object(pyneo4j_client, "cypher") as mock_cypher:
        mock_cypher.return_value = ([], [])

        with pytest.raises(NoResultsFound):
            await node.delete()


async def test_refresh(pyneo4j_client: Pyneo4jClient, neo4j_session: AsyncSession):
    await pyneo4j_client.register_models([UpdateNodeTest])

    node = UpdateNodeTest()
    await node.create()

    node.my_prop = "new value"

    await node.refresh()
    assert node.my_prop == "default"

    results = await neo4j_session.run("MATCH (n:Test) RETURN n")
    query_result: List[List[Node]] = await results.values()

    assert len(query_result) == 1
    assert len(query_result[0]) == 1

    node_result = query_result[0][0]
    assert node_result["my_prop"] == "default"


async def test_refresh_no_result(pyneo4j_client: Pyneo4jClient):
    await pyneo4j_client.register_models([UpdateNodeTest])

    node = UpdateNodeTest()
    await node.create()

    with patch.object(pyneo4j_client, "cypher") as mock_cypher:
        mock_cypher.return_value = ([], [])

        with pytest.raises(NoResultsFound):
            await node.refresh()
