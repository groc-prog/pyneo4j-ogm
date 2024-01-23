# pylint: disable=unused-argument, unused-import, redefined-outer-name, protected-access, missing-module-docstring, missing-class-docstring
# pyright: reportGeneralTypeIssues=false

from typing import Any, Dict, cast

import pytest

from pyneo4j_ogm.exceptions import UnregisteredModel
from pyneo4j_ogm.queries.types import RelationshipMatchDirection
from tests.fixtures.db_setup import (
    CoffeeShop,
    Developer,
    WorkedWith,
    client,
    session,
    setup_test_data,
)


async def test_find_connected_nodes(setup_test_data):
    node = await Developer.find_one({"uid": 3})
    assert node is not None

    results = await cast(Developer, node).find_connected_nodes(
        {"$node": {"$labels": list(CoffeeShop.model_settings().labels), "tags": {"$in": ["cozy"]}}},
    )

    assert len(results) == 1
    assert isinstance(results[0], CoffeeShop)
    assert results[0].rating == 5


async def test_find_connected_nodes_filter_relationships(setup_test_data):
    node = await Developer.find_one({"uid": 3})
    assert node is not None

    results = await cast(Developer, node).find_connected_nodes(
        {
            "$node": {"$labels": list(CoffeeShop.model_settings().labels)},
            "$relationships": [{"$type": "LIKES_TO_DRINK", "liked": True}],
            "$minHops": 1,
            "$maxHops": 2,
        },
    )

    assert len(results) == 1
    assert isinstance(results[0], CoffeeShop)
    assert results[0].rating == 5


async def test_find_connected_nodes_direction_incoming(setup_test_data):
    node = await Developer.find_one({"uid": 3})
    assert node is not None

    results = await cast(Developer, node).find_connected_nodes(
        {
            "$node": {"$labels": list(Developer.model_settings().labels)},
            "$direction": RelationshipMatchDirection.INCOMING,
            "$minHops": 2,
            "$maxHops": 2,
        },
    )

    assert len(results) == 2


async def test_find_connected_nodes_projections(setup_test_data):
    node = await Developer.find_one({"uid": 3})
    assert node is not None

    results = await cast(Developer, node).find_connected_nodes(
        {
            "$node": {"$labels": list(CoffeeShop.model_settings().labels)},
            "$maxHops": 2,
        },
        projections={"coffee_rating": "rating"},
    )

    assert len(results) == 2
    assert all(isinstance(result, dict) for result in results)
    assert all("coffee_rating" in cast(Dict[str, Any], result) for result in results)


async def test_find_connected_nodes_options(setup_test_data):
    node = await Developer.find_one({"uid": 3})
    assert node is not None

    results = await cast(Developer, node).find_connected_nodes(
        {
            "$node": {"$labels": list(CoffeeShop.model_settings().labels)},
            "$maxHops": 2,
        },
        options={"limit": 1},
    )

    assert len(results) == 1
    assert all(isinstance(result, CoffeeShop) for result in results)


async def test_find_connected_nodes_options_and_projections(setup_test_data):
    node = await Developer.find_one({"uid": 1})
    assert node is not None

    results = await cast(Developer, node).find_connected_nodes(
        {
            "$node": {"$labels": list(Developer.model_settings().labels)},
        },
        options={"skip": 1},
        projections={"dev_name": "name"},
    )

    assert len(results) == 3
    assert all(isinstance(result, dict) for result in results)


async def test_find_connected_nodes_auto_fetch(setup_test_data):
    node = await CoffeeShop.find_one({"rating": 5})
    assert node is not None

    results = await cast(CoffeeShop, node).find_connected_nodes(
        {
            "$node": {"$labels": list(Developer.model_settings().labels), "uid": 3},
            "$direction": RelationshipMatchDirection.INCOMING,
        },
        auto_fetch_nodes=True,
    )

    assert len(results) == 1
    assert isinstance(results[0], Developer)
    assert len(results[0].colleagues.nodes) == 2
    assert len(results[0].coffee.nodes) == 3


async def test_find_connected_nodes_auto_fetch_models(setup_test_data):
    node = await CoffeeShop.find_one({"rating": 5})
    assert node is not None

    results = await cast(CoffeeShop, node).find_connected_nodes(
        {
            "$node": {"$labels": list(Developer.model_settings().labels), "uid": 3},
            "$direction": RelationshipMatchDirection.INCOMING,
        },
        auto_fetch_nodes=True,
        auto_fetch_models=[Developer],
    )

    assert len(results) == 1
    assert isinstance(results[0], Developer)
    assert len(results[0].colleagues.nodes) == 2
    assert len(results[0].coffee.nodes) == 0


async def test_find_connected_nodes_auto_fetch_models_as_string(setup_test_data):
    node = await CoffeeShop.find_one({"rating": 5})
    assert node is not None

    results = await cast(CoffeeShop, node).find_connected_nodes(
        {
            "$node": {"$labels": list(Developer.model_settings().labels), "uid": 3},
            "$direction": RelationshipMatchDirection.INCOMING,
        },
        auto_fetch_nodes=True,
        auto_fetch_models=["Developer"],
    )

    assert len(results) == 1
    assert isinstance(results[0], Developer)
    assert len(results[0].colleagues.nodes) == 2
    assert len(results[0].coffee.nodes) == 0


async def test_find_connected_nodes_auto_fetch_models_unregistered_node(setup_test_data):
    node = await CoffeeShop.find_one({"rating": 5})
    assert node is not None

    CoffeeShop._client.models.remove(Developer)

    with pytest.raises(UnregisteredModel):
        await cast(CoffeeShop, node).find_connected_nodes(
            {
                "$node": {"$labels": list(Developer.model_settings().labels), "uid": 3},
                "$direction": RelationshipMatchDirection.INCOMING,
            },
            auto_fetch_nodes=True,
            auto_fetch_models=["Developer"],
        )


async def test_find_connected_nodes_auto_fetch_models_unregistered_relationship(setup_test_data):
    node = await CoffeeShop.find_one({"rating": 5})
    assert node is not None

    CoffeeShop._client.models.remove(WorkedWith)

    with pytest.raises(UnregisteredModel):
        await cast(CoffeeShop, node).find_connected_nodes(
            {
                "$node": {"$labels": list(Developer.model_settings().labels), "uid": 3},
                "$direction": RelationshipMatchDirection.INCOMING,
            },
            auto_fetch_nodes=True,
            auto_fetch_models=[Developer],
        )
