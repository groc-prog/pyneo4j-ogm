# pylint: disable=unused-argument, unused-import, redefined-outer-name, protected-access, missing-module-docstring

from typing import LiteralString, cast

from neo4j import AsyncSession

from pyneo4j_ogm.core.client import Pyneo4jClient
from tests.fixtures.db_setup import (
    Coffee,
    Consumed,
    Developer,
    WorkedWith,
    client,
    dev_model_instances,
    session,
    setup_test_data,
)

pytest_plugins = ("pytest_asyncio",)


async def test_disconnect_all(client: Pyneo4jClient, session: AsyncSession, dev_model_instances):
    await client.register_models([Developer, Coffee, Consumed])

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


async def test_disconnect_no_connections(client: Pyneo4jClient, session: AsyncSession, dev_model_instances):
    await client.register_models([Developer, WorkedWith])

    bob_model = dev_model_instances[3]
    count = await bob_model.coffee.disconnect_all()

    assert count == 0
