# pylint: disable=unused-argument, unused-import, redefined-outer-name, protected-access, missing-module-docstring

from unittest.mock import patch

from neo4j import AsyncSession
from neo4j.graph import Graph, Node

from pyneo4j_ogm.core.client import Pyneo4jClient
from tests.fixtures.db_setup import (
    Bestseller,
    Coffee,
    Consumed,
    Developer,
    WorkedWith,
    client,
    coffee_model_instances,
    dev_model_instances,
    session,
    setup_test_data,
)

pytest_plugins = ("pytest_asyncio",)


async def test_find_connected_nodes(client: Pyneo4jClient, session: AsyncSession, dev_model_instances):
    await client.register_models([Developer, WorkedWith])

    john_model, *_ = dev_model_instances
    colleagues = await john_model.colleagues.find_connected_nodes()

    assert len(colleagues) == 2
    assert all(isinstance(colleague, Developer) for colleague in colleagues)


async def test_find_connected_nodes_no_result(client: Pyneo4jClient, session: AsyncSession, dev_model_instances):
    await client.register_models([Developer, Coffee, Consumed])

    bob_model = dev_model_instances[3]
    coffees = await bob_model.coffee.find_connected_nodes()

    assert len(coffees) == 0


async def test_find_connected_nodes_raw_result(client: Pyneo4jClient, session: AsyncSession, dev_model_instances):
    await client.register_models([Developer, Coffee, Consumed])

    john_model, *_ = dev_model_instances

    with patch.object(client, "cypher") as mock_cypher:
        mock_node = Node(
            graph=Graph(),
            element_id="start-element-id",
            id_=2,
            properties={"name": "Dean", "age": 25, "uid": 6},
        )
        mock_cypher.return_value = ([[mock_node, None]], [])

        colleagues = await john_model.colleagues.find_connected_nodes()

        assert len(colleagues) == 1
        assert isinstance(colleagues[0], Developer)
        assert colleagues[0].name == "Dean"
        assert colleagues[0].age == 25
        assert colleagues[0].uid == 6


async def test_find_connected_nodes_filter(client: Pyneo4jClient, session: AsyncSession, dev_model_instances):
    await client.register_models([Developer, WorkedWith])

    john_model, *_ = dev_model_instances
    colleagues = await john_model.colleagues.find_connected_nodes({"$relationship": {"language": "Java"}})

    assert len(colleagues) == 1
    assert all(isinstance(colleague, Developer) for colleague in colleagues)


async def test_find_connected_nodes_projections(client: Pyneo4jClient, session: AsyncSession, dev_model_instances):
    await client.register_models([Developer, WorkedWith])

    john_model, *_ = dev_model_instances
    colleagues = await john_model.colleagues.find_connected_nodes({}, projections={"dev_name": "name"})

    assert len(colleagues) == 2
    assert all(isinstance(colleague, dict) for colleague in colleagues)
    assert all("dev_name" in colleague for colleague in colleagues)


async def test_find_connected_nodes_options(client: Pyneo4jClient, session: AsyncSession, dev_model_instances):
    await client.register_models([Developer, Coffee, Consumed])

    alice_model = dev_model_instances[2]
    coffees = await alice_model.coffee.find_connected_nodes(options={"skip": 1})

    assert len(coffees) == 2
    assert all(isinstance(coffee, Coffee) for coffee in coffees)


async def test_find_connected_nodes_options_and_projections(
    client: Pyneo4jClient, session: AsyncSession, dev_model_instances
):
    await client.register_models([Developer, Coffee, Consumed])

    alice_model = dev_model_instances[2]
    coffees = await alice_model.coffee.find_connected_nodes(projections={"name": "flavor"}, options={"skip": 1})

    assert len(coffees) == 2
    assert all(isinstance(coffee, dict) for coffee in coffees)
    assert all("name" in coffee for coffee in coffees)


async def test_find_connected_nodes_options_and_projections_and_auto_fetch(
    client: Pyneo4jClient, session: AsyncSession, dev_model_instances
):
    await client.register_models([Developer, Coffee, Consumed, Bestseller])

    alice_model = dev_model_instances[2]
    coffees = await alice_model.coffee.find_connected_nodes(
        projections={"name": "flavor"}, options={"skip": 1}, auto_fetch_nodes=True
    )

    assert len(coffees) == 2
    assert all(isinstance(coffee, dict) for coffee in coffees)
    assert all("name" in coffee for coffee in coffees)


async def test_find_connected_nodes_auto_fetch(client: Pyneo4jClient, session: AsyncSession, dev_model_instances):
    await client.register_models([Developer, Coffee, Consumed, Bestseller])

    alice_model = dev_model_instances[2]
    coffees = await alice_model.coffee.find_connected_nodes(auto_fetch_nodes=True)

    assert len(coffees) == 3
    assert all(isinstance(coffee, Coffee) for coffee in coffees)
    assert any(len(coffee.bestseller_for.nodes) != 0 for coffee in coffees)
    assert any(len(coffee.developers.nodes) != 0 for coffee in coffees)


async def test_find_connected_nodes_auto_fetch_models(
    client: Pyneo4jClient, session: AsyncSession, dev_model_instances
):
    await client.register_models([Developer, Coffee, Consumed, Bestseller])

    alice_model = dev_model_instances[2]
    coffees = await alice_model.coffee.find_connected_nodes(auto_fetch_nodes=True, auto_fetch_models=[Developer])

    assert len(coffees) == 3
    assert all(isinstance(coffee, Coffee) for coffee in coffees)
    assert all(len(coffee.bestseller_for.nodes) == 0 for coffee in coffees)
    assert any(len(coffee.developers.nodes) != 0 for coffee in coffees)
