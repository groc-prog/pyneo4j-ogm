# pylint: disable=unused-argument, unused-import, redefined-outer-name, protected-access, missing-module-docstring

from typing import List, LiteralString, cast
from unittest.mock import patch

import pytest
from neo4j import AsyncSession
from neo4j.graph import Node

from pyneo4j_ogm.core.client import Pyneo4jClient
from pyneo4j_ogm.exceptions import NoResultsFound
from tests.fixtures.db_setup import Coffee, client, session

pytest_plugins = ("pytest_asyncio",)


async def test_create(client: Pyneo4jClient, session: AsyncSession):
    await client.register_models([Coffee])

    node = Coffee(flavor="Mocha", sugar=True, milk=True, note={"roast": "dark"})
    await node.create()

    assert node._element_id is not None
    assert node._id is not None
    assert node._db_properties == {
        "flavor": "Mocha",
        "sugar": True,
        "milk": True,
        "note": {"roast": "dark"},
    }

    results = await session.run(
        cast(
            LiteralString,
            f"""
            MATCH (n:{':'.join(Coffee.model_settings().labels)})
            WHERE elementId(n) = $element_id
            RETURN n
            """,
        ),
        {"element_id": node._element_id},
    )
    query_result: List[List[Node]] = await results.values()

    assert len(query_result) == 1
    assert len(query_result[0]) == 1

    node_result = query_result[0][0]
    assert isinstance(node_result, Node)
    assert node_result.element_id == node._element_id
    assert node_result.id == node._id

    assert node_result["flavor"] == "Mocha"
    assert node_result["sugar"]
    assert node_result["milk"]
    assert node_result["note"] == '{"roast": "dark"}'


async def test_create_no_result(client: Pyneo4jClient):
    with patch.object(client, "cypher") as mock_cypher:
        mock_cypher.return_value = ([], [])

        await client.register_models([Coffee])

        node = Coffee(flavor="Mocha", sugar=True, milk=True, note={"roast": "dark"})

        with pytest.raises(NoResultsFound):
            await node.create()
