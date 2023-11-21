# pylint: disable=unused-argument, unused-import, redefined-outer-name, protected-access, missing-module-docstring

from typing import cast

import pytest
from neo4j import AsyncSession
from typing_extensions import LiteralString

from pyneo4j_ogm.core.client import Pyneo4jClient
from pyneo4j_ogm.exceptions import NotConnectedToSourceNode
from tests.fixtures.db_setup import (
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


async def test_replace(client: Pyneo4jClient, session: AsyncSession, dev_model_instances, coffee_model_instances):
    await client.register_models([Developer, Coffee, Consumed])

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
    await client.register_models([Developer, Coffee, Consumed])

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
    await client.register_models([Developer, WorkedWith])

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
    await client.register_models([Developer, WorkedWith])

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
    await client.register_models([Developer, WorkedWith])

    john_model, *_ = dev_model_instances
    latte_model, mocha_model, *_ = coffee_model_instances

    with pytest.raises(NotConnectedToSourceNode):
        await john_model.coffee.replace(mocha_model, latte_model)
