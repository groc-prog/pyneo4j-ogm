# pylint: disable=unused-argument, unused-import, redefined-outer-name, protected-access, missing-module-docstring
# pyright: reportGeneralTypeIssues=false

from typing import List
from unittest.mock import patch

import pytest
from neo4j import AsyncSession
from neo4j.graph import Graph, Node

from pyneo4j_ogm.core.client import Pyneo4jClient
from tests.fixtures.db_clients import neo4j_session, pyneo4j_client
from tests.fixtures.models import SinglePropModel

pytest_plugins = ("pytest_asyncio",)


async def test_update_many(pyneo4j_client: Pyneo4jClient, neo4j_session: AsyncSession):
    await pyneo4j_client.register_models([SinglePropModel])

    node1 = SinglePropModel(my_prop="value1")
    node2 = SinglePropModel(my_prop="value2")
    node3 = SinglePropModel(my_prop="other")
    await node1.create()
    await node2.create()
    await node3.create()

    updated_nodes = await SinglePropModel.update_many({"my_prop": "updated"}, {"my_prop": {"$contains": "value"}})

    assert isinstance(updated_nodes, list)
    assert len(updated_nodes) == 2
    assert all(isinstance(node, SinglePropModel) for node in updated_nodes)
    assert all(node.my_prop != "updated" for node in updated_nodes)

    results = await neo4j_session.run("MATCH (n:Test) WHERE n.my_prop CONTAINS $val RETURN n", {"val": "updated"})
    query_result: List[List[Node]] = await results.values()

    assert len(query_result) == 2


async def test_update_many_return_updated(pyneo4j_client: Pyneo4jClient):
    await pyneo4j_client.register_models([SinglePropModel])

    node1 = SinglePropModel(my_prop="value1")
    node2 = SinglePropModel(my_prop="value2")
    node3 = SinglePropModel(my_prop="other")
    await node1.create()
    await node2.create()
    await node3.create()

    updated_nodes = await SinglePropModel.update_many(
        {"my_prop": "updated"}, {"my_prop": {"$contains": "value"}}, new=True
    )

    assert isinstance(updated_nodes, list)
    assert len(updated_nodes) == 2
    assert all(isinstance(node, SinglePropModel) for node in updated_nodes)
    assert all(node.my_prop == "updated" for node in updated_nodes)


async def test_update_many_raw_results(pyneo4j_client: Pyneo4jClient):
    await pyneo4j_client.register_models([SinglePropModel])

    node1 = SinglePropModel(my_prop="value1")
    node3 = SinglePropModel(my_prop="other")
    await node1.create()
    await node3.create()

    with patch.object(pyneo4j_client, "cypher") as mock_cypher:
        mock_nodes = [
            Node(graph=Graph(), element_id=node1.element_id, id_=node1.id, properties={"my_prop": "value1"}),
            None,
        ]
        mock_cypher.return_value = (
            [mock_nodes],
            [],
        )
        updated_nodes = await SinglePropModel.update_many({"my_prop": "updated"}, {"my_prop": {"$contains": "value"}})

        assert isinstance(updated_nodes, list)
        assert len(updated_nodes) == 1
        assert all(isinstance(node, SinglePropModel) for node in updated_nodes)


async def test_update_many_no_results(pyneo4j_client: Pyneo4jClient):
    await pyneo4j_client.register_models([SinglePropModel])

    node1 = SinglePropModel(my_prop="value1")
    node3 = SinglePropModel(my_prop="other")
    await node1.create()
    await node3.create()

    with patch.object(pyneo4j_client, "cypher") as mock_cypher:
        mock_nodes = [
            None,
        ]
        mock_cypher.return_value = (
            [mock_nodes],
            [],
        )
        updated_nodes = await SinglePropModel.update_many({"my_prop": "updated"}, {"my_prop": {"$contains": "value"}})

        assert isinstance(updated_nodes, list)
        assert len(updated_nodes) == 0
