# pylint: disable=unused-argument, unused-import, redefined-outer-name, protected-access, missing-module-docstring

from typing import List, cast
from unittest.mock import patch

from neo4j import AsyncSession
from neo4j.graph import Graph, Node
from typing_extensions import LiteralString

from pyneo4j_ogm.core.client import Pyneo4jClient
from tests.fixtures.db_setup import Developer, client, session, setup_test_data

pytest_plugins = ("pytest_asyncio",)


async def test_update_many(session: AsyncSession, setup_test_data):
    updated_nodes = await Developer.update_many({"age": 50}, {"age": {"$gte": 30}})

    assert isinstance(updated_nodes, list)
    assert len(updated_nodes) == 2
    assert all(isinstance(node, Developer) for node in updated_nodes)
    assert all(node.age != 50 for node in updated_nodes)

    results = await session.run(
        cast(
            LiteralString,
            f"""
            MATCH (n:{':'.join(Developer.model_settings().labels)})
            WHERE n.age = $age
            RETURN n
            """,
        ),
        {"age": 50},
    )
    query_result: List[List[Node]] = await results.values()
    await results.consume()

    assert len(query_result) == 2


async def test_update_many_return_updated(setup_test_data):
    updated_nodes = await Developer.update_many({"age": 50}, {"age": {"$gte": 30}}, new=True)

    assert isinstance(updated_nodes, list)
    assert len(updated_nodes) == 2
    assert all(isinstance(node, Developer) for node in updated_nodes)
    assert all(node.age == 50 for node in updated_nodes)


async def test_update_many_raw_results(client: Pyneo4jClient):
    await client.register_models([Developer])

    with patch.object(client, "cypher") as mock_cypher:
        mock_nodes = [
            Node(
                graph=Graph(),
                element_id="element-id",
                id_=1,
                properties={"age": 30, "uid": 1, "name": "John"},
            ),
            None,
        ]
        mock_cypher.return_value = (
            [mock_nodes],
            [],
        )
        updated_nodes = await Developer.update_many({"age": 50}, {"age": {"$gte": 30}})

        assert isinstance(updated_nodes, list)
        assert len(updated_nodes) == 1
        assert all(isinstance(node, Developer) for node in updated_nodes)


async def test_update_many_no_results(client: Pyneo4jClient):
    await client.register_models([Developer])

    with patch.object(client, "cypher") as mock_cypher:
        mock_nodes = [
            None,
        ]
        mock_cypher.return_value = (
            [mock_nodes],
            [],
        )
        updated_nodes = await Developer.update_many({"age": 50}, {"age": {"$gte": 30}})

        assert isinstance(updated_nodes, list)
        assert len(updated_nodes) == 0
