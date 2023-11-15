# pylint: disable=unused-argument, unused-import, redefined-outer-name, protected-access, missing-module-docstring

from unittest.mock import patch

import pytest

from pyneo4j_ogm.core.client import Pyneo4jClient
from pyneo4j_ogm.exceptions import NoResultsFound
from tests.fixtures.db_clients import pyneo4j_client
from tests.fixtures.models import SinglePropModel

pytest_plugins = ("pytest_asyncio",)


async def test_count(pyneo4j_client: Pyneo4jClient):
    await pyneo4j_client.register_models([SinglePropModel])

    node1 = SinglePropModel(my_prop="value1")
    node2 = SinglePropModel(my_prop="value2")
    node3 = SinglePropModel(my_prop="other")
    await node1.create()
    await node2.create()
    await node3.create()

    count = await SinglePropModel.count({"my_prop": {"$contains": "value"}})
    assert count == 2


async def test_count_no_match(pyneo4j_client: Pyneo4jClient):
    await pyneo4j_client.register_models([SinglePropModel])

    count = await SinglePropModel.count({"my_prop": "value1"})
    assert count == 0


async def test_count_no_query_result(pyneo4j_client: Pyneo4jClient):
    await pyneo4j_client.register_models([SinglePropModel])

    with patch.object(pyneo4j_client, "cypher") as mock_cypher:
        mock_cypher.return_value = [[], []]
        with pytest.raises(NoResultsFound):
            await SinglePropModel.count({"my_prop": "value1"})
