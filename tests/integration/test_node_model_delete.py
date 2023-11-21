# pylint: disable=unused-argument, unused-import, redefined-outer-name, protected-access, missing-module-docstring

from typing import List, LiteralString, cast
from unittest.mock import patch

import pytest
from neo4j import AsyncSession
from neo4j.graph import Node

from pyneo4j_ogm.core.client import Pyneo4jClient
from pyneo4j_ogm.exceptions import NoResultsFound
from tests.fixtures.db_setup import CoffeeShop, client, session

pytest_plugins = ("pytest_asyncio",)


async def test_delete(client: Pyneo4jClient, session: AsyncSession):
    await client.register_models([CoffeeShop])

    node = CoffeeShop(rating=5, tags=["modern", "trendy"])
    await node.create()
    assert node._destroyed is False

    await node.delete()
    assert node._destroyed

    results = await session.run(
        cast(
            LiteralString,
            f"""
            MATCH (n:{':'.join(CoffeeShop.model_settings().labels)})
            WHERE elementId(n) = $element_id
            RETURN n
            """,
        ),
        {"element_id": node._element_id},
    )
    query_result: List[List[Node]] = await results.values()
    await results.consume()

    assert len(query_result) == 0


async def test_delete_no_result(client: Pyneo4jClient):
    await client.register_models([CoffeeShop])

    node = CoffeeShop(rating=5, tags=["modern", "trendy"])
    await node.create()

    with patch.object(client, "cypher") as mock_cypher:
        mock_cypher.return_value = ([], [])

        with pytest.raises(NoResultsFound):
            await node.delete()
