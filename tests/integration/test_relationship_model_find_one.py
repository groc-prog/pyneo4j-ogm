# pylint: disable=unused-argument, unused-import, redefined-outer-name, protected-access, missing-module-docstring

from typing import cast
from unittest.mock import patch

import pytest
from neo4j.graph import Graph, Node, Relationship

from pyneo4j_ogm.core.client import Pyneo4jClient
from pyneo4j_ogm.exceptions import InvalidFilters
from tests.fixtures.db_setup import WorkedWith, client, session, setup_test_data

pytest_plugins = ("pytest_asyncio",)


async def test_find_one(client: Pyneo4jClient, setup_test_data):
    await client.register_models([WorkedWith])

    result = await WorkedWith.find_one({"language": "Go"})
    assert result is not None
    assert isinstance(result, WorkedWith)
    assert result.language == "Go"


async def test_find_one_no_match(client: Pyneo4jClient, setup_test_data):
    await client.register_models([WorkedWith])

    result = await WorkedWith.find_one({"language": "non-existent"})
    assert result is None


async def test_find_one_missing_filter(client: Pyneo4jClient, setup_test_data):
    await client.register_models([WorkedWith])

    with pytest.raises(InvalidFilters):
        await WorkedWith.find_one({})


async def test_find_one_raw_result(client: Pyneo4jClient):
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

        result = await WorkedWith.find_one({"language": "Go"})
        assert result is not None
        assert isinstance(result, WorkedWith)
        assert result.language == "Go"
        assert result._start_node_element_id == mock_start_node.element_id
        assert result._start_node_id == mock_start_node.id
        assert result._end_node_element_id == mock_end_node.element_id
        assert result._end_node_id == mock_end_node.id


async def test_find_one_projections(client: Pyneo4jClient, setup_test_data):
    await client.register_models([WorkedWith])

    result = await WorkedWith.find_one({"language": "Go"}, {"lang": "language"})
    assert result is not None
    assert isinstance(result, dict)
    assert "lang" in result
    assert result["lang"] == "Go"
