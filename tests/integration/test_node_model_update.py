# pylint: disable=unused-argument, unused-import, redefined-outer-name, protected-access, missing-module-docstring

from typing import List
from unittest.mock import patch

import pytest
from neo4j import AsyncSession
from neo4j.graph import Node

from pyneo4j_ogm.core.client import Pyneo4jClient
from pyneo4j_ogm.exceptions import NoResultsFound
from tests.fixtures.db_clients import neo4j_session, pyneo4j_client
from tests.fixtures.models import SinglePropModel

pytest_plugins = ("pytest_asyncio",)


async def test_update(pyneo4j_client: Pyneo4jClient, neo4j_session: AsyncSession):
    await pyneo4j_client.register_models([SinglePropModel])

    node = SinglePropModel()
    await node.create()
    assert node.my_prop == "default"

    node.my_prop = "new value"
    await node.update()
    assert node.my_prop == "new value"
    assert node._db_properties == {"my_prop": "new value"}

    results = await neo4j_session.run("MATCH (n:Test) RETURN n")
    query_result: List[List[Node]] = await results.values()

    assert len(query_result) == 1
    assert len(query_result[0]) == 1

    node_result = query_result[0][0]
    assert node_result["my_prop"] == "new value"


async def test_update_no_result(pyneo4j_client: Pyneo4jClient):
    await pyneo4j_client.register_models([SinglePropModel])

    node = SinglePropModel()
    await node.create()
    assert node.my_prop == "default"

    with patch.object(pyneo4j_client, "cypher") as mock_cypher:
        mock_cypher.return_value = ([], [])

        with pytest.raises(NoResultsFound):
            node.my_prop = "new value"
            await node.update()
