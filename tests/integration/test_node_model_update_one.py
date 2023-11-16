# pylint: disable=unused-argument, unused-import, redefined-outer-name, protected-access, missing-module-docstring

from typing import List, LiteralString, cast

import pytest
from neo4j import AsyncSession
from neo4j.graph import Node

from pyneo4j_ogm.core.client import Pyneo4jClient
from pyneo4j_ogm.exceptions import MissingFilters
from tests.fixtures.db_setup import Developer, client, session, setup_test_data

pytest_plugins = ("pytest_asyncio",)


async def test_update_one(session: AsyncSession, setup_test_data):
    updated_node = await Developer.update_one({"age": 50}, {"uid": 1})

    assert updated_node is not None
    assert isinstance(updated_node, Developer)
    assert updated_node.age == 30

    results = await session.run(
        cast(
            LiteralString,
            f"""
            MATCH (n:{':'.join(Developer.model_settings().labels)})
            WHERE n.uid = $uid
            RETURN n
            """,
        ),
        {"uid": 1},
    )
    query_result: List[List[Node]] = await results.values()

    assert len(query_result) == 1
    assert query_result[0][0]["age"] == 50


async def test_update_one_return_updated(setup_test_data):
    updated_node = await Developer.update_one({"age": 50}, {"uid": 1}, new=True)

    assert updated_node is not None
    assert isinstance(updated_node, Developer)
    assert updated_node.age == 50


async def test_update_one_no_match(setup_test_data):
    updated_node = await Developer.update_one({"age": 50}, {"uid": 99999})

    assert updated_node is None


async def test_update_one_missing_filters(client: Pyneo4jClient):
    await client.register_models([Developer])

    with pytest.raises(MissingFilters):
        await Developer.update_one({"my_prop": "updated"}, {})
