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


async def test_disconnect(client: Pyneo4jClient, session: AsyncSession, dev_model_instances, coffee_model_instances):
    await client.register_models([Developer, Coffee, Consumed])

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
    await client.register_models([Developer, WorkedWith])

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
    await client.register_models([Developer, WorkedWith])

    john_model, *_ = dev_model_instances
    _, mocha_model, *_ = coffee_model_instances
    count = await john_model.coffee.disconnect(mocha_model)

    assert count == 0

    with pytest.raises(NotConnectedToSourceNode):
        await john_model.coffee.disconnect(mocha_model, raise_on_empty=True)
