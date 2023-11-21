# pylint: disable=unused-argument, unused-import, redefined-outer-name, protected-access, missing-module-docstring

from typing import cast
from unittest.mock import patch

from neo4j import AsyncSession
from neo4j.graph import Graph, Node, Relationship

from pyneo4j_ogm.core.client import Pyneo4jClient
from tests.fixtures.db_setup import WorkedWith, client, session, setup_test_data

pytest_plugins = ("pytest_asyncio",)


async def test_update_many(client: Pyneo4jClient, session: AsyncSession, setup_test_data):
    await client.register_models([WorkedWith])

    results = await WorkedWith.update_many({"language": "Rust"}, {"language": "Python"})
    assert len(results) == 2
    assert all(isinstance(result, WorkedWith) for result in results)
    assert all(result.language == "Python" for result in results)

    results = await session.run(
        """
        MATCH ()-[r:WAS_WORK_BUDDY_WITH]->()
        WHERE r.language = $language
        RETURN r
        """,
        {"language": "Python"},
    )

    query_result = await results.values()
    await results.consume()

    assert len(query_result) == 0


async def test_update_many_return_new(client: Pyneo4jClient, setup_test_data):
    await client.register_models([WorkedWith])

    results = await WorkedWith.update_many({"language": "Rust"}, {"language": "Python"}, new=True)
    assert len(results) == 2
    assert all(isinstance(result, WorkedWith) for result in results)
    assert all(result.language == "Rust" for result in results)


async def test_update_many_no_match(client: Pyneo4jClient, setup_test_data):
    await client.register_models([WorkedWith])

    results = await WorkedWith.update_many({"language": "non-existent"}, {"language": "non-existent"})
    assert len(results) == 0


async def test_update_many_raw_result(client: Pyneo4jClient):
    await client.register_models([WorkedWith])

    with patch.object(client, "cypher") as mock_cypher:
        mock_start_node = Node(
            graph=Graph(),
            element_id="start-element-id",
            id_=2,
            properties={},
        )
        mock_end_node = Node(
            graph=Graph(),
            element_id="end-element-id",
            id_=3,
            properties={},
        )

        mock_relationship = Relationship(
            graph=Graph(),
            element_id="element-id",
            id_=1,
            properties={"language": "Go"},
        )
        setattr(mock_relationship, "_start_node", mock_start_node)
        setattr(mock_relationship, "_end_node", mock_end_node)

        mock_cypher.return_value = (
            [[mock_relationship, None]],
            [],
        )

        results = await WorkedWith.update_many({"language": "Rust"}, {"language": "Go"})
        assert len(results) == 1
        assert isinstance(results[0], WorkedWith)
        assert results[0].language == "Go"
        assert results[0]._start_node_element_id == mock_start_node.element_id
        assert results[0]._start_node_id == mock_start_node.id
        assert results[0]._end_node_element_id == mock_end_node.element_id
        assert results[0]._end_node_id == mock_end_node.id
