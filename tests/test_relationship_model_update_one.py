# pylint: disable=unused-argument, unused-import, redefined-outer-name, protected-access, missing-module-docstring, missing-class-docstring
# pyright: reportGeneralTypeIssues=false

from unittest.mock import patch

import pytest
from neo4j import AsyncSession
from neo4j.graph import Graph, Node, Relationship

from pyneo4j_ogm.core.client import Pyneo4jClient
from pyneo4j_ogm.exceptions import InvalidFilters, NoResultFound
from tests.fixtures.db_setup import WorkedWith, client, session, setup_test_data


async def test_update_one(client: Pyneo4jClient, session: AsyncSession, setup_test_data):
    await client.register_models([WorkedWith])

    result = await WorkedWith.update_one({"language": "Rust"}, {"language": "Python"})
    assert result is not None
    assert isinstance(result, WorkedWith)
    assert result.language == "Python"

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

    assert len(query_result) == 1


async def test_update_one_return_new(client: Pyneo4jClient, setup_test_data):
    await client.register_models([WorkedWith])

    result = await WorkedWith.update_one({"language": "Rust"}, {"language": "Python"}, new=True)
    assert result is not None
    assert isinstance(result, WorkedWith)
    assert result.language == "Rust"


async def test_update_one_no_match(client: Pyneo4jClient, setup_test_data):
    await client.register_models([WorkedWith])

    result = await WorkedWith.update_one({"language": "non-existent"}, {"language": "non-existent"})
    assert result is None

    with pytest.raises(NoResultFound):
        await WorkedWith.update_one({"language": "non-existent"}, {"language": "non-existent"}, raise_on_empty=True)


async def test_update_one_missing_filter(client: Pyneo4jClient, setup_test_data):
    await client.register_models([WorkedWith])

    with pytest.raises(InvalidFilters):
        await WorkedWith.update_one({}, {})


async def test_update_one_raw_result(client: Pyneo4jClient):
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
            [[mock_relationship]],
            [],
        )

        result = await WorkedWith.update_one({"language": "Rust"}, {"language": "Go"})
        assert result is not None
        assert isinstance(result, WorkedWith)
        assert result.language == "Go"
        assert result._start_node_element_id == mock_start_node.element_id
        assert result._start_node_id == mock_start_node.id
        assert result._end_node_element_id == mock_end_node.element_id
        assert result._end_node_id == mock_end_node.id
