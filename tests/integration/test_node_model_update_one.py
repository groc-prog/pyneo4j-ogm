# pylint: disable=unused-argument, unused-import, redefined-outer-name, protected-access, missing-module-docstring
# pyright: reportGeneralTypeIssues=false

from typing import List

import pytest
from neo4j import AsyncSession
from neo4j.graph import Node

from pyneo4j_ogm.core.client import Pyneo4jClient
from pyneo4j_ogm.exceptions import MissingFilters
from tests.fixtures.db_clients import neo4j_session, pyneo4j_client
from tests.fixtures.models import SinglePropModel

pytest_plugins = ("pytest_asyncio",)


async def test_update_one(pyneo4j_client: Pyneo4jClient, neo4j_session: AsyncSession):
    await pyneo4j_client.register_models([SinglePropModel])

    node1 = SinglePropModel(my_prop="value1")
    node2 = SinglePropModel(my_prop="value2")
    await node1.create()
    await node2.create()

    updated_node = await SinglePropModel.update_one({"my_prop": "updated"}, {"my_prop": "value1"})

    assert updated_node is not None
    assert isinstance(updated_node, SinglePropModel)
    assert updated_node._id == node1._id
    assert updated_node._element_id == node1._element_id
    assert updated_node.my_prop == "value1"

    results = await neo4j_session.run(
        "MATCH (n:Test) WHERE elementId(n) = $element_id RETURN n", {"element_id": node1._element_id}
    )
    query_result: List[List[Node]] = await results.values()

    assert len(query_result) == 1
    assert query_result[0][0]["my_prop"] == "updated"


async def test_update_one_return_updated(pyneo4j_client: Pyneo4jClient):
    await pyneo4j_client.register_models([SinglePropModel])

    node1 = SinglePropModel(my_prop="value1")
    node2 = SinglePropModel(my_prop="value2")
    await node1.create()
    await node2.create()

    updated_node = await SinglePropModel.update_one({"my_prop": "updated"}, {"my_prop": "value1"}, new=True)

    assert updated_node is not None
    assert isinstance(updated_node, SinglePropModel)
    assert updated_node._id == node1._id
    assert updated_node._element_id == node1._element_id
    assert updated_node.my_prop == "updated"


async def test_update_one_no_match(pyneo4j_client: Pyneo4jClient):
    await pyneo4j_client.register_models([SinglePropModel])

    updated_node = await SinglePropModel.update_one({"my_prop": "updated"}, {"my_prop": "value1"})

    assert updated_node is None


async def test_update_one_missing_filters(pyneo4j_client: Pyneo4jClient):
    await pyneo4j_client.register_models([SinglePropModel])

    with pytest.raises(MissingFilters):
        await SinglePropModel.update_one({"my_prop": "updated"}, {})
