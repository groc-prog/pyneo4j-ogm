# pylint: disable=unused-argument, unused-import, redefined-outer-name, protected-access, missing-module-docstring

from neo4j import AsyncSession
from neo4j.graph import Node

from pyneo4j_ogm.core.client import Pyneo4jClient
from tests.fixtures.db_clients import neo4j_session, pyneo4j_client
from tests.fixtures.models import SinglePropModel

pytest_plugins = ("pytest_asyncio",)


async def test_delete_many(pyneo4j_client: Pyneo4jClient, neo4j_session: AsyncSession):
    await pyneo4j_client.register_models([SinglePropModel])

    node1 = SinglePropModel(my_prop="value1")
    node2 = SinglePropModel(my_prop="value2")
    node3 = SinglePropModel(my_prop="other")
    await node1.create()
    await node2.create()
    await node3.create()

    count = await SinglePropModel.delete_many({"my_prop": {"$contains": "value"}})
    assert count == 2

    results = await neo4j_session.run("MATCH (n:Test) WHERE n.my_prop CONTAINS $val RETURN n", {"val": "value"})
    query_result: list[list[Node]] = await results.values()

    assert len(query_result) == 0


async def test_delete_many_no_match(pyneo4j_client: Pyneo4jClient):
    await pyneo4j_client.register_models([SinglePropModel])

    count = await SinglePropModel.delete_many({"my_prop": "value1"})
    assert count == 0
