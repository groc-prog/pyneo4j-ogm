# pylint: disable=unused-argument, unused-import, redefined-outer-name, protected-access, missing-module-docstring

from typing import cast
from unittest.mock import patch

import pytest
from neo4j import AsyncSession
from neo4j.graph import Node
from typing_extensions import LiteralString

from pyneo4j_ogm.core.client import Pyneo4jClient
from pyneo4j_ogm.exceptions import NoResultsFound
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
    await results.consume()

    assert len(query_result) == 1


async def test_delete_many_no_match(client: Pyneo4jClient, session: AsyncSession, setup_test_data):
    await client.register_models([CoffeeShop])

    count = await CoffeeShop.delete_many({"tags": {"$in": ["oh-no"]}})
    assert count == 0

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
    await results.consume()

    assert len(query_result) == 3


async def test_delete_many_no_results(client: Pyneo4jClient, session: AsyncSession, setup_test_data):
    await client.register_models([CoffeeShop])

    with patch.object(client, "cypher") as mock_cypher:
        mock_cypher.return_value = [[], []]

        with pytest.raises(NoResultsFound):
            await CoffeeShop.delete_many({"tags": {"$in": ["oh-no"]}})
