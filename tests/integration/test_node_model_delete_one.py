# pylint: disable=unused-argument, unused-import, redefined-outer-name, protected-access, missing-module-docstring

from typing import LiteralString, cast

import pytest
from neo4j import AsyncSession
from neo4j.graph import Node

from pyneo4j_ogm.exceptions import MissingFilters, NoResultsFound
from tests.fixtures.db_setup import CoffeeShop, client, session, setup_test_data

pytest_plugins = ("pytest_asyncio",)


async def test_delete_one(session: AsyncSession, setup_test_data):
    count = await CoffeeShop.delete_one({"tags": {"$in": ["cozy"]}})
    assert count == 1

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

    assert len(query_result) == 2


async def test_delete_one_no_match(setup_test_data):
    with pytest.raises(NoResultsFound):
        await CoffeeShop.delete_one({"tags": {"$in": ["oh-no"]}})


async def test_delete_one_invalid_filter(setup_test_data):
    with pytest.raises(MissingFilters):
        await CoffeeShop.delete_one({})
