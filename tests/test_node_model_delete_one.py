# pylint: disable=unused-argument, unused-import, redefined-outer-name, protected-access, missing-module-docstring, missing-class-docstring
# pyright: reportGeneralTypeIssues=false

from typing import cast
from unittest.mock import patch

import pytest
from neo4j import AsyncSession
from neo4j.graph import Node
from typing_extensions import LiteralString

from pyneo4j_ogm.core.client import Pyneo4jClient
from pyneo4j_ogm.exceptions import InvalidFilters, NoResultFound, UnexpectedEmptyResult
from tests.fixtures.db_setup import CoffeeShop, client, session, setup_test_data


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
    await results.consume()

    assert len(query_result) == 2


async def test_delete_one_no_match(session: AsyncSession, setup_test_data):
    results = await CoffeeShop.delete_one({"tags": {"$in": ["oh-no"]}})
    assert results == 0

    with pytest.raises(NoResultFound):
        await CoffeeShop.delete_one({"tags": {"$in": ["oh-no"]}}, raise_on_empty=True)

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


async def test_delete_one_invalid_filter(setup_test_data):
    with pytest.raises(InvalidFilters):
        await CoffeeShop.delete_one({})


async def test_delete_one_no_results(client: Pyneo4jClient, session: AsyncSession, setup_test_data):
    await client.register_models([CoffeeShop])

    with patch.object(client, "cypher") as mock_cypher:
        mock_cypher.return_value = [[], []]

        with pytest.raises(UnexpectedEmptyResult):
            await CoffeeShop.delete_one({"tags": {"$in": ["oh-no"]}})
