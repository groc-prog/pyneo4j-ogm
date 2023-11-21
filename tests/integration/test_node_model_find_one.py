# pylint: disable=unused-argument, unused-import, redefined-outer-name, protected-access, missing-module-docstring

from typing import cast
from unittest.mock import patch

import pytest
from neo4j.graph import Graph, Node

from pyneo4j_ogm.core.client import Pyneo4jClient
from pyneo4j_ogm.exceptions import InvalidFilters, UnregisteredModel
from tests.fixtures.db_setup import (
    Coffee,
    Consumed,
    Developer,
    client,
    session,
    setup_test_data,
)

pytest_plugins = ("pytest_asyncio",)


async def test_find_one(setup_test_data):
    found_node = await Developer.find_one({"uid": 1})

    assert found_node is not None
    assert isinstance(found_node, Developer)
    assert found_node.uid == 1

    found_node = await Developer.find_one({"age": {"$gte": 30}})

    assert found_node is not None
    assert isinstance(found_node, Developer)


async def test_find_one_no_match(setup_test_data):
    found_node = await Developer.find_one({"my_prop": "non-existent"})

    assert found_node is None


async def test_find_one_raw_result(client: Pyneo4jClient):
    await client.register_models([Developer])

    with patch.object(client, "cypher") as mock_cypher:
        mock_node = Node(
            graph=Graph(),
            element_id="element-id",
            id_=1,
            properties={"age": 30, "uid": 1, "name": "John"},
        )
        mock_cypher.return_value = (
            [[mock_node]],
            [],
        )

        found_node = await Developer.find_one({"my_prop": "non-existent"})

        assert found_node is not None
        assert isinstance(found_node, Developer)
        assert found_node._id == mock_node.id
        assert found_node._element_id == mock_node.element_id
        assert found_node.age == mock_node["age"]
        assert found_node.uid == mock_node["uid"]
        assert found_node.name == mock_node["name"]


async def test_find_one_missing_filter(client: Pyneo4jClient):
    await client.register_models([Developer])

    with pytest.raises(InvalidFilters):
        await Developer.find_one({})


async def test_find_one_projections(setup_test_data):
    found_node = await Developer.find_one({"uid": 1}, projections={"dev_name": "name"})

    assert found_node is not None
    assert isinstance(found_node, dict)
    assert found_node["dev_name"] == "John"


async def test_find_one_auto_fetch(setup_test_data):
    found_node = await Developer.find_one({"uid": 1}, auto_fetch_nodes=True)

    assert found_node is not None
    assert isinstance(found_node, Developer)
    assert len(found_node.colleagues.nodes) == 2
    assert len(found_node.coffee.nodes) == 2


async def test_find_one_auto_fetch_models(setup_test_data):
    found_node = await Developer.find_one({"uid": 1}, auto_fetch_nodes=True, auto_fetch_models=[Coffee])

    assert found_node is not None
    assert isinstance(found_node, Developer)
    assert len(found_node.colleagues.nodes) == 0
    assert len(found_node.coffee.nodes) == 2


async def test_find_one_auto_fetch_models_as_string(setup_test_data):
    found_node = await Developer.find_one({"uid": 1}, auto_fetch_nodes=True, auto_fetch_models=["Coffee"])

    assert found_node is not None
    assert isinstance(found_node, Developer)
    assert len(found_node.colleagues.nodes) == 0
    assert len(found_node.coffee.nodes) == 2


async def test_find_one_auto_fetch_models_unregistered_relationship(setup_test_data):
    Developer._client.models.remove(Consumed)

    with pytest.raises(UnregisteredModel):
        await Developer.find_one({"uid": 1}, auto_fetch_nodes=True, auto_fetch_models=[Coffee])


async def test_find_one_auto_fetch_models_unregistered_node(setup_test_data):
    Developer._client.models.remove(Coffee)

    with pytest.raises(UnregisteredModel):
        await Developer.find_one({"uid": 1}, auto_fetch_nodes=True, auto_fetch_models=[Coffee])
