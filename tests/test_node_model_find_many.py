# pylint: disable=unused-argument, unused-import, redefined-outer-name, protected-access, missing-module-docstring, missing-class-docstring
# pyright: reportGeneralTypeIssues=false

from typing import Any, Dict, cast
from unittest.mock import patch

import pytest
from neo4j.graph import Graph, Node

from pyneo4j_ogm.core.client import Pyneo4jClient
from pyneo4j_ogm.exceptions import UnregisteredModel
from tests.fixtures.db_setup import (
    Bestseller,
    Coffee,
    CoffeeShop,
    Developer,
    client,
    session,
    setup_test_data,
)


async def test_find_many(setup_test_data):
    found_nodes = await Coffee.find_many({"sugar": True})

    assert isinstance(found_nodes, list)
    assert len(found_nodes) == 3
    assert all(isinstance(node, Coffee) for node in found_nodes)


async def test_find_many_no_match(setup_test_data):
    found_nodes = await Coffee.find_many({"sugar": 12})

    assert isinstance(found_nodes, list)
    assert len(found_nodes) == 0


async def test_find_many_raw_result(client: Pyneo4jClient):
    await client.register_models([Coffee])

    with patch.object(client, "cypher") as mock_cypher:
        mock_node = Node(
            graph=Graph(),
            element_id="element-id",
            id_=1,
            properties={"flavor": "Espresso", "sugar": False, "milk": False, "note": '{"roast": "dark"}'},
        )
        mock_cypher.return_value = (
            [[mock_node, None]],
            [],
        )

        found_nodes = await Coffee.find_many({"sugar": False})

        assert isinstance(found_nodes, list)
        assert len(found_nodes) == 1
        assert all(isinstance(node, Coffee) for node in found_nodes)


async def test_find_many_projections(setup_test_data):
    found_nodes = await Coffee.find_many({"sugar": True}, projections={"has_sugar": "sugar"})

    assert isinstance(found_nodes, list)
    assert len(found_nodes) == 3
    assert all(isinstance(node, dict) for node in found_nodes)
    assert all("has_sugar" in cast(Dict[str, Any], node) for node in found_nodes)


async def test_find_many_options(setup_test_data):
    found_nodes = await Coffee.find_many({"sugar": True}, options={"limit": 1})

    assert isinstance(found_nodes, list)
    assert len(found_nodes) == 1
    assert all(isinstance(node, Coffee) for node in found_nodes)


async def test_find_many_projections_and_options(setup_test_data):
    found_nodes = await Coffee.find_many(options={"skip": 1}, projections={"has_sugar": "sugar"})

    assert isinstance(found_nodes, list)
    assert len(found_nodes) == 4
    assert all(isinstance(node, dict) for node in found_nodes)


async def test_find_many_projections_and_options_auto_fetch(setup_test_data):
    found_nodes = await Coffee.find_many(options={"skip": 1}, projections={"has_sugar": "sugar"}, auto_fetch_nodes=True)

    assert isinstance(found_nodes, list)
    assert len(found_nodes) == 4
    assert all(isinstance(node, dict) for node in found_nodes)


async def test_find_many_auto_fetch(setup_test_data):
    found_nodes = await Coffee.find_many({"flavor": "Mocha"}, auto_fetch_nodes=True)

    assert isinstance(found_nodes, list)
    assert len(found_nodes) == 1
    assert isinstance(found_nodes[0], Coffee)
    assert len(found_nodes[0].developers.nodes) == 1
    assert len(found_nodes[0].bestseller_for.nodes) == 1


async def test_find_many_auto_fetch_models(setup_test_data):
    found_nodes = await Coffee.find_many({"flavor": "Mocha"}, auto_fetch_nodes=True, auto_fetch_models=[Developer])

    assert isinstance(found_nodes, list)
    assert len(found_nodes) == 1
    assert isinstance(found_nodes[0], Coffee)
    assert len(found_nodes[0].developers.nodes) == 1
    assert len(found_nodes[0].bestseller_for.nodes) == 0


async def test_find_many_auto_fetch_models_as_string(setup_test_data):
    found_nodes = await Coffee.find_many({"flavor": "Mocha"}, auto_fetch_nodes=True, auto_fetch_models=["CoffeeShop"])

    assert isinstance(found_nodes, list)
    assert len(found_nodes) == 1
    assert isinstance(found_nodes[0], Coffee)
    assert len(found_nodes[0].developers.nodes) == 0
    assert len(found_nodes[0].bestseller_for.nodes) == 1


async def test_find_many_auto_fetch_models_unregistered_relationship(setup_test_data):
    Coffee._client.models.remove(Bestseller)

    with pytest.raises(UnregisteredModel):
        await Coffee.find_many({"flavor": "Mocha"}, auto_fetch_nodes=True, auto_fetch_models=[CoffeeShop])


async def test_find_many_auto_fetch_models_unregistered_node(setup_test_data):
    Coffee._client.models.remove(CoffeeShop)

    with pytest.raises(UnregisteredModel):
        await Coffee.find_many({"flavor": "Mocha"}, auto_fetch_nodes=True, auto_fetch_models=["CoffeeShop"])
