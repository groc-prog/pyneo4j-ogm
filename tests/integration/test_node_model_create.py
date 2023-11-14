# pylint: disable=unused-argument, unused-import, redefined-outer-name, protected-access, missing-module-docstring
# pyright: reportGeneralTypeIssues=false

import json
from typing import List
from unittest.mock import patch

import pytest
from neo4j import AsyncSession
from neo4j.graph import Node

from pyneo4j_ogm.core.client import Pyneo4jClient
from pyneo4j_ogm.exceptions import NoResultsFound
from tests.fixtures.db_clients import neo4j_session, pyneo4j_client
from tests.fixtures.models import MultiPropModel

pytest_plugins = ("pytest_asyncio",)


async def test_create(pyneo4j_client: Pyneo4jClient, neo4j_session: AsyncSession):
    dict_prop = {"key1": "value1", "key2": 2, "key3": [1, 2, 3]}

    await pyneo4j_client.register_models([MultiPropModel])

    node = MultiPropModel(str_prop="string", int_prop=1, bool_prop=True, dict_prop=dict_prop)
    await node.create()

    assert node._element_id is not None
    assert node._id is not None
    assert node._db_properties == {
        "str_prop": "string",
        "int_prop": 1,
        "bool_prop": True,
        "dict_prop": dict_prop,
    }

    results = await neo4j_session.run("MATCH (n:Test) RETURN n")
    query_result: List[List[Node]] = await results.values()

    assert len(query_result) == 1
    assert len(query_result[0]) == 1

    node_result = query_result[0][0]
    assert isinstance(node_result, Node)
    assert node_result.element_id == node._element_id
    assert node_result.id == node._id

    assert node_result["str_prop"] == "string"
    assert node_result["int_prop"] == 1
    assert node_result["bool_prop"]
    assert node_result["dict_prop"] == json.dumps(dict_prop)


async def test_create_no_result(pyneo4j_client: Pyneo4jClient):
    with patch.object(pyneo4j_client, "cypher") as mock_cypher:
        mock_cypher.return_value = ([], [])

        await pyneo4j_client.register_models([MultiPropModel])

        node = MultiPropModel(str_prop="string", int_prop=1, bool_prop=True, dict_prop={"key": "value"})

        with pytest.raises(NoResultsFound):
            await node.create()
