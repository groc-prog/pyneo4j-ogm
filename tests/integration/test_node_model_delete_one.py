# pylint: disable=unused-argument, unused-import, redefined-outer-name, protected-access, missing-module-docstring

import pytest
from neo4j import AsyncSession
from neo4j.graph import Node

from pyneo4j_ogm.core.client import Pyneo4jClient
from pyneo4j_ogm.exceptions import MissingFilters, NoResultsFound
from tests.fixtures.db_clients import neo4j_session, pyneo4j_client
from tests.fixtures.models import SinglePropModel

pytest_plugins = ("pytest_asyncio",)


async def test_delete_one(pyneo4j_client: Pyneo4jClient, neo4j_session: AsyncSession):
    await pyneo4j_client.register_models([SinglePropModel])

    node1 = SinglePropModel(my_prop="value1")
    node2 = SinglePropModel(my_prop="value2")
    await node1.create()
    await node2.create()

    count = await SinglePropModel.delete_one({"my_prop": "value1"})
    assert count == 1

    results = await neo4j_session.run(
        "MATCH (n:Test) WHERE elementId(n) = $element_id RETURN n", {"element_id": node1._element_id}
    )
    query_result: list[list[Node]] = await results.values()

    assert len(query_result) == 0


async def test_delete_one_no_match(pyneo4j_client: Pyneo4jClient):
    await pyneo4j_client.register_models([SinglePropModel])

    with pytest.raises(NoResultsFound):
        await SinglePropModel.delete_one({"my_prop": "value1"})


async def test_delete_one_invalid_filter(pyneo4j_client: Pyneo4jClient):
    await pyneo4j_client.register_models([SinglePropModel])

    with pytest.raises(MissingFilters):
        await SinglePropModel.delete_one({})
