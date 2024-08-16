# pylint: disable=unused-argument, unused-import, redefined-outer-name, protected-access, missing-module-docstring, missing-class-docstring
# pyright: reportGeneralTypeIssues=false

from typing import cast
from unittest.mock import patch

import pytest
from neo4j import AsyncSession
from neo4j.graph import Graph, Node, Relationship
from typing_extensions import LiteralString

from pyneo4j_ogm.core.client import Pyneo4jClient
from pyneo4j_ogm.exceptions import (
    CardinalityViolationError,
    InstanceDestroyedError,
    InstanceNotHydratedError,
    InvalidTargetNodeModelError,
    NotConnectedToSourceNodeError,
    UnexpectedEmptyResultError,
)
from tests.fixtures.db_setup import (
    Bestseller,
    Coffee,
    CoffeeShop,
    Consumed,
    Developer,
    WorkedWith,
    client,
    coffee_model_instances,
    coffee_shop_model_instances,
    dev_model_instances,
    session,
    setup_test_data,
)


async def test_replace(client: Pyneo4jClient, session: AsyncSession, dev_model_instances, coffee_model_instances):
    john_model, *_ = dev_model_instances
    latte_model, mocha_model, *_ = coffee_model_instances
    replaced_relationships = await john_model.coffee.replace(latte_model, mocha_model)

    assert len(replaced_relationships) == 1
    assert not replaced_relationships[0].liked
    assert replaced_relationships[0].start_node_element_id == john_model.element_id
    assert replaced_relationships[0].end_node_element_id == mocha_model.element_id

    query_result = await session.run(
        cast(
            LiteralString,
            f"""
            MATCH (start)-[:{Consumed.model_settings().type}]->(end)
            WHERE elementId(start) = $start_element_id AND elementId(end) = $end_element_id
            RETURN count(end)
            """,
        ),
        {
            "start_element_id": john_model.element_id,
            "end_element_id": latte_model.element_id,
        },
    )
    result = await query_result.values()
    await query_result.consume()

    assert result[0][0] == 0

    query_result = await session.run(
        cast(
            LiteralString,
            f"""
            MATCH (start)-[:{Consumed.model_settings().type}]->(end)
            WHERE elementId(start) = $start_element_id AND elementId(end) = $end_element_id
            RETURN count(end)
            """,
        ),
        {
            "start_element_id": john_model.element_id,
            "end_element_id": mocha_model.element_id,
        },
    )
    result = await query_result.values()
    await query_result.consume()

    assert result[0][0] == 1


async def test_replace_with_existing(
    client: Pyneo4jClient, session: AsyncSession, dev_model_instances, coffee_model_instances
):
    john_model, *_ = dev_model_instances
    latte_model, _, espresso_model, *_ = coffee_model_instances
    replaced_relationships = await john_model.coffee.replace(latte_model, espresso_model)

    assert len(replaced_relationships) == 1
    assert not replaced_relationships[0].liked
    assert replaced_relationships[0].start_node_element_id == john_model.element_id
    assert replaced_relationships[0].end_node_element_id == espresso_model.element_id

    query_result = await session.run(
        cast(
            LiteralString,
            f"""
            MATCH (start)-[:{Consumed.model_settings().type}]->(end)
            WHERE elementId(start) = $start_element_id AND elementId(end) = $end_element_id
            RETURN count(end)
            """,
        ),
        {
            "start_element_id": john_model.element_id,
            "end_element_id": latte_model.element_id,
        },
    )
    result = await query_result.values()
    await query_result.consume()

    assert result[0][0] == 0

    query_result = await session.run(
        cast(
            LiteralString,
            f"""
            MATCH (start)-[:{Consumed.model_settings().type}]->(end)
            WHERE elementId(start) = $start_element_id AND elementId(end) = $end_element_id
            RETURN count(end)
            """,
        ),
        {
            "start_element_id": john_model.element_id,
            "end_element_id": espresso_model.element_id,
        },
    )
    result = await query_result.values()
    await query_result.consume()

    assert result[0][0] == 1


async def test_replace_with_existing_and_allow_multiple(
    client: Pyneo4jClient, session: AsyncSession, dev_model_instances
):
    john_model, sam_model, alice_model, *_ = dev_model_instances
    replaced_relationships = await john_model.colleagues.replace(alice_model, sam_model)

    assert len(replaced_relationships) == 1
    assert replaced_relationships[0].language == "Python"
    assert replaced_relationships[0].start_node_element_id == john_model.element_id
    assert replaced_relationships[0].end_node_element_id == sam_model.element_id

    query_result = await session.run(
        cast(
            LiteralString,
            f"""
            MATCH (start)-[r:{WorkedWith.model_settings().type}]->(end)
            WHERE elementId(start) = $start_element_id AND elementId(end) = $end_element_id
            RETURN count(r)
            """,
        ),
        {
            "start_element_id": john_model.element_id,
            "end_element_id": alice_model.element_id,
        },
    )
    result = await query_result.values()
    await query_result.consume()

    assert result[0][0] == 0

    query_result = await session.run(
        cast(
            LiteralString,
            f"""
            MATCH (start)-[r:{WorkedWith.model_settings().type}]->(end)
            WHERE elementId(start) = $start_element_id AND elementId(end) = $end_element_id
            RETURN count(r)
            """,
        ),
        {
            "start_element_id": john_model.element_id,
            "end_element_id": sam_model.element_id,
        },
    )
    result = await query_result.values()
    await query_result.consume()

    assert result[0][0] == 3


async def test_replace_multiple(client: Pyneo4jClient, session: AsyncSession, dev_model_instances):
    john_model, sam_model, alice_model, *_ = dev_model_instances
    replaced_relationships = await john_model.colleagues.replace(sam_model, alice_model)

    assert len(replaced_relationships) == 2
    assert all(isinstance(relationship, WorkedWith) for relationship in replaced_relationships)

    query_result = await session.run(
        cast(
            LiteralString,
            f"""
            MATCH (start)-[r:{WorkedWith.model_settings().type}]->(end)
            WHERE elementId(start) = $start_element_id AND elementId(end) = $end_element_id
            RETURN count(r)
            """,
        ),
        {
            "start_element_id": john_model.element_id,
            "end_element_id": sam_model.element_id,
        },
    )
    result = await query_result.values()
    await query_result.consume()

    assert result[0][0] == 0

    query_result = await session.run(
        cast(
            LiteralString,
            f"""
            MATCH (start)-[r:{WorkedWith.model_settings().type}]->(end)
            WHERE elementId(start) = $start_element_id AND elementId(end) = $end_element_id
            RETURN count(r)
            """,
        ),
        {
            "start_element_id": john_model.element_id,
            "end_element_id": alice_model.element_id,
        },
    )
    result = await query_result.values()
    await query_result.consume()

    assert result[0][0] == 3


async def test_replace_not_connected_exc(
    client: Pyneo4jClient, session: AsyncSession, dev_model_instances, coffee_model_instances
):
    john_model, *_ = dev_model_instances
    latte_model, mocha_model, *_ = coffee_model_instances

    with pytest.raises(NotConnectedToSourceNodeError):
        await john_model.coffee.replace(mocha_model, latte_model)


async def test_relationships(client: Pyneo4jClient, dev_model_instances):
    john_model, sam_model, alice_model, *_ = dev_model_instances
    multi_relationships = await john_model.colleagues.relationships(sam_model)

    assert len(multi_relationships) == 2
    assert all(isinstance(relationship, WorkedWith) for relationship in multi_relationships)
    assert any(relationship for relationship in multi_relationships if relationship.language == "Python")
    assert any(relationship for relationship in multi_relationships if relationship.language == "Java")

    single_relationship = await john_model.colleagues.relationships(alice_model)

    assert len(single_relationship) == 1
    assert isinstance(single_relationship[0], WorkedWith)
    assert single_relationship[0].language == "Python"


async def test_relationships_no_match(client: Pyneo4jClient, dev_model_instances):
    john_model, _, _, bob_model = dev_model_instances
    multi_relationships = await john_model.colleagues.relationships(bob_model)

    assert len(multi_relationships) == 0


async def test_relationships_raw_result(client: Pyneo4jClient, dev_model_instances):
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

        john_model, _, _, bob_model = dev_model_instances
        raw_relationship = await john_model.colleagues.relationships(bob_model)

        assert len(raw_relationship) == 1
        assert isinstance(raw_relationship[0], WorkedWith)
        assert raw_relationship[0].language == "Go"
        assert raw_relationship[0]._start_node_element_id == mock_start_node.element_id
        assert raw_relationship[0]._start_node_id == mock_start_node.id


async def test_relationships_projections(client: Pyneo4jClient, dev_model_instances):
    john_model, sam_model, alice_model, *_ = dev_model_instances
    multi_relationships = await john_model.colleagues.relationships(sam_model, projections={"lang": "language"})

    assert len(multi_relationships) == 2
    assert all(isinstance(relationship, dict) for relationship in multi_relationships)
    assert all("lang" in cast(dict, relationship) for relationship in multi_relationships)

    single_relationship = await john_model.colleagues.relationships(alice_model, projections={"lang": "language"})

    assert len(single_relationship) == 1
    assert isinstance(single_relationship[0], dict)
    assert "lang" in cast(dict, single_relationship[0])


async def test_relationships_options(client: Pyneo4jClient, dev_model_instances):
    john_model, sam_model, *_ = dev_model_instances
    multi_relationships = await john_model.colleagues.relationships(sam_model, options={"skip": 1})

    assert len(multi_relationships) == 1
    assert all(isinstance(relationship, WorkedWith) for relationship in multi_relationships)


async def test_relationships_filters(client: Pyneo4jClient, dev_model_instances):
    john_model, sam_model, *_ = dev_model_instances
    multi_relationships = await john_model.colleagues.relationships(sam_model, filters={"language": "Java"})

    assert len(multi_relationships) == 1
    assert all(isinstance(relationship, WorkedWith) for relationship in multi_relationships)


async def test_find_connected_nodes(client: Pyneo4jClient, session: AsyncSession, dev_model_instances):
    john_model, *_ = dev_model_instances
    colleagues = await john_model.colleagues.find_connected_nodes()

    assert len(colleagues) == 2
    assert all(isinstance(colleague, Developer) for colleague in colleagues)


async def test_find_connected_nodes_no_result(client: Pyneo4jClient, session: AsyncSession, dev_model_instances):
    bob_model = dev_model_instances[3]
    coffees = await bob_model.coffee.find_connected_nodes()

    assert len(coffees) == 0


async def test_find_connected_nodes_raw_result(client: Pyneo4jClient, session: AsyncSession, dev_model_instances):
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
    john_model, *_ = dev_model_instances
    colleagues = await john_model.colleagues.find_connected_nodes({"$relationship": {"language": "Java"}})

    assert len(colleagues) == 1
    assert all(isinstance(colleague, Developer) for colleague in colleagues)


async def test_find_connected_nodes_projections(client: Pyneo4jClient, session: AsyncSession, dev_model_instances):
    john_model, *_ = dev_model_instances
    colleagues = await john_model.colleagues.find_connected_nodes({}, projections={"dev_name": "name"})

    assert len(colleagues) == 2
    assert all(isinstance(colleague, dict) for colleague in colleagues)
    assert all("dev_name" in colleague for colleague in colleagues)


async def test_find_connected_nodes_options(client: Pyneo4jClient, session: AsyncSession, dev_model_instances):
    alice_model = dev_model_instances[2]
    coffees = await alice_model.coffee.find_connected_nodes(options={"skip": 1})

    assert len(coffees) == 2
    assert all(isinstance(coffee, Coffee) for coffee in coffees)


async def test_find_connected_nodes_options_and_projections(
    client: Pyneo4jClient, session: AsyncSession, dev_model_instances
):
    alice_model = dev_model_instances[2]
    coffees = await alice_model.coffee.find_connected_nodes(projections={"name": "flavor"}, options={"skip": 1})

    assert len(coffees) == 2
    assert all(isinstance(coffee, dict) for coffee in coffees)
    assert all("name" in coffee for coffee in coffees)


async def test_find_connected_nodes_options_and_projections_and_auto_fetch(
    client: Pyneo4jClient, session: AsyncSession, dev_model_instances
):
    alice_model = dev_model_instances[2]
    coffees = await alice_model.coffee.find_connected_nodes(
        projections={"name": "flavor"}, options={"skip": 1}, auto_fetch_nodes=True
    )

    assert len(coffees) == 2
    assert all(isinstance(coffee, dict) for coffee in coffees)
    assert all("name" in coffee for coffee in coffees)


async def test_find_connected_nodes_auto_fetch(client: Pyneo4jClient, session: AsyncSession, dev_model_instances):
    alice_model = dev_model_instances[2]
    coffees = await alice_model.coffee.find_connected_nodes(auto_fetch_nodes=True)

    assert len(coffees) == 3
    assert all(isinstance(coffee, Coffee) for coffee in coffees)
    assert any(len(coffee.bestseller_for.nodes) != 0 for coffee in coffees)
    assert any(len(coffee.developers.nodes) != 0 for coffee in coffees)


async def test_find_connected_nodes_auto_fetch_models(
    client: Pyneo4jClient, session: AsyncSession, dev_model_instances
):
    alice_model = dev_model_instances[2]
    coffees = await alice_model.coffee.find_connected_nodes(auto_fetch_nodes=True, auto_fetch_models=[Developer])

    assert len(coffees) == 3
    assert all(isinstance(coffee, Coffee) for coffee in coffees)
    assert all(len(coffee.bestseller_for.nodes) == 0 for coffee in coffees)
    assert any(len(coffee.developers.nodes) != 0 for coffee in coffees)


async def test_ensure_cardinality(client: Pyneo4jClient, coffee_shop_model_instances, coffee_model_instances):
    espresso_model = coffee_model_instances[2]
    rating_five_model, *_ = coffee_shop_model_instances

    with pytest.raises(CardinalityViolationError):
        await rating_five_model.bestseller.connect(espresso_model)


async def test_ensure_alive_not_hydrated(client: Pyneo4jClient, dev_model_instances):
    dev = Developer(name="Sindhu", age=23, uid=12)

    john_model, *_ = dev_model_instances

    with pytest.raises(InstanceNotHydratedError):
        await john_model.colleagues.connect(dev)


async def test_ensure_alive_destroyed(client: Pyneo4jClient, dev_model_instances):
    dev = Developer(name="Sindhu", age=23, uid=12)
    setattr(dev, "_element_id", "element-id")
    setattr(dev, "_id", 1)
    setattr(dev, "_destroyed", True)

    john_model, *_ = dev_model_instances

    with pytest.raises(InstanceDestroyedError):
        await john_model.colleagues.connect(dev)


async def test_ensure_alive_invalid_node(client: Pyneo4jClient, dev_model_instances, coffee_model_instances):
    john_model, *_ = dev_model_instances
    latte_model, *_ = coffee_model_instances

    with pytest.raises(InvalidTargetNodeModelError):
        await john_model.colleagues.connect(latte_model)


async def test_ensure_alive_source_not_hydrated(client: Pyneo4jClient, dev_model_instances):
    dev = Developer(name="Sindhu", age=23, uid=12)

    john_model, *_ = dev_model_instances

    with pytest.raises(InstanceNotHydratedError):
        await dev.colleagues.connect(john_model)


async def test_ensure_alive_source_destroyed(client: Pyneo4jClient, dev_model_instances):
    dev = Developer(name="Sindhu", age=23, uid=12)
    setattr(dev, "_element_id", "element-id")
    setattr(dev, "_id", 1)
    setattr(dev, "_destroyed", True)

    john_model, *_ = dev_model_instances

    with pytest.raises(InstanceDestroyedError):
        await dev.colleagues.connect(john_model)


async def test_disconnect(client: Pyneo4jClient, session: AsyncSession, dev_model_instances, coffee_model_instances):
    john_model, *_ = dev_model_instances
    latte_model, *_ = coffee_model_instances
    count = await john_model.coffee.disconnect(latte_model)

    assert count == 1

    query_result = await session.run(
        cast(
            LiteralString,
            f"""
            MATCH (start)-[r:{Consumed.model_settings().type}]->(end)
            WHERE elementId(start) = $start_element_id AND elementId(end) = $end_element_id
            RETURN count(r)
            """,
        ),
        {
            "start_element_id": john_model.element_id,
            "end_element_id": latte_model.element_id,
        },
    )
    result = await query_result.values()
    await query_result.consume()

    assert result[0][0] == 0


async def test_disconnect_multiple(client: Pyneo4jClient, session: AsyncSession, dev_model_instances):
    john_model, sam_model, *_ = dev_model_instances
    count = await john_model.colleagues.disconnect(sam_model)

    assert count == 2

    query_result = await session.run(
        cast(
            LiteralString,
            f"""
            MATCH (start)-[r:{Consumed.model_settings().type}]->(end)
            WHERE elementId(start) = $start_element_id AND elementId(end) = $end_element_id
            RETURN count(r)
            """,
        ),
        {
            "start_element_id": john_model.element_id,
            "end_element_id": sam_model.element_id,
        },
    )
    result = await query_result.values()
    await query_result.consume()

    assert result[0][0] == 0


async def test_disconnect_no_connections(
    client: Pyneo4jClient, session: AsyncSession, dev_model_instances, coffee_model_instances
):
    john_model, *_ = dev_model_instances
    _, mocha_model, *_ = coffee_model_instances
    count = await john_model.coffee.disconnect(mocha_model)

    assert count == 0

    with pytest.raises(NotConnectedToSourceNodeError):
        await john_model.coffee.disconnect(mocha_model, raise_on_empty=True)


async def test_disconnect_all(client: Pyneo4jClient, session: AsyncSession, dev_model_instances):
    john_model, *_ = dev_model_instances
    count = await john_model.coffee.disconnect_all()

    assert count == 2

    query_result = await session.run(
        cast(
            LiteralString,
            f"""
            MATCH (start)-[:{Consumed.model_settings().type}]->(end:{':'.join(Coffee.model_settings().labels)})
            WHERE elementId(start) = $start_element_id
            RETURN count(end)
            """,
        ),
        {
            "start_element_id": john_model.element_id,
        },
    )
    result = await query_result.values()
    await query_result.consume()

    assert result[0][0] == 0


async def test_connect_not_allow_multiple(
    client: Pyneo4jClient, session: AsyncSession, dev_model_instances, coffee_model_instances
):
    john_model, *_ = dev_model_instances
    latte_model, mocha_model, *_ = coffee_model_instances
    updated_relationship = await john_model.coffee.connect(latte_model, {"liked": True})

    assert isinstance(updated_relationship, Consumed)
    assert updated_relationship.liked

    query_result = await session.run(
        cast(
            LiteralString,
            f"MATCH ()-[r:{Consumed.model_settings().type}]->() WHERE elementId(r) = $element_id RETURN r",
        ),
        {
            "element_id": updated_relationship.element_id,
        },
    )
    result = await query_result.values()
    await query_result.consume()

    assert result[0][0]["liked"]

    new_relationship = await john_model.coffee.connect(mocha_model, {"liked": False})

    assert isinstance(new_relationship, Consumed)
    assert not new_relationship.liked

    query_result = await session.run(
        cast(
            LiteralString,
            f"MATCH ()-[r:{Consumed.model_settings().type}]->() WHERE elementId(r) = $element_id RETURN r",
        ),
        {
            "element_id": new_relationship.element_id,
        },
    )
    result = await query_result.values()
    await query_result.consume()

    assert len(result) == 1
    assert not result[0][0]["liked"]


async def test_connect_allow_multiple(
    client: Pyneo4jClient, session: AsyncSession, dev_model_instances, coffee_model_instances
):
    john_model, sam_model, *_ = dev_model_instances

    new_relationship = await john_model.colleagues.connect(sam_model, {"language": "PHP"})

    assert isinstance(new_relationship, WorkedWith)
    assert new_relationship.language == "PHP"

    query_result = await session.run(
        cast(
            LiteralString,
            f"MATCH ()-[r:{WorkedWith.model_settings().type}]->() WHERE elementId(r) = $element_id RETURN r",
        ),
        {
            "element_id": new_relationship.element_id,
        },
    )
    result = await query_result.values()
    await query_result.consume()

    assert len(result) == 1
    assert result[0][0]["language"] == "PHP"


async def test_connect_no_result(
    client: Pyneo4jClient, session: AsyncSession, dev_model_instances, coffee_model_instances
):
    john_model, sam_model, *_ = dev_model_instances

    with patch.object(john_model.colleagues._client, "cypher") as mock_cypher:
        mock_cypher.return_value = [[], []]

        with pytest.raises(UnexpectedEmptyResultError):
            await john_model.colleagues.connect(sam_model, {"language": "PHP"})
