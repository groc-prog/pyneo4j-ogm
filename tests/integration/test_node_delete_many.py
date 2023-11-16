# pylint: disable=unused-argument, unused-import, redefined-outer-name, protected-access, missing-module-docstring

from typing import LiteralString, cast

from neo4j import AsyncSession
from neo4j.graph import Node

from pyneo4j_ogm.core.client import Pyneo4jClient
from tests.fixtures.db_setup import CoffeeShop, client, session, setup_test_data

pytest_plugins = ("pytest_asyncio",)


async def test_delete_many(session: AsyncSession, setup_test_data):
    count = await CoffeeShop.delete_many({"tags": {"$in": ["hipster"]}})
    assert count == 2

    results = await session.run(
        cast(
            LiteralString,
            f"""
            MATCH (n:{':'.join(CoffeeShop.model_settings().labels)})
            RETURN DISTINCT n
            """,
        ),
    )
    query_result: list[list[Node]] = await results.values()

    assert len(query_result) == 1


async def test_delete_many_no_match(client: Pyneo4jClient):
    await client.register_models([CoffeeShop])

    count = await CoffeeShop.delete_many({"tags": {"$in": ["oh-no"]}})
    assert count == 0
