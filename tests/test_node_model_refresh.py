# pylint: disable=unused-argument, unused-import, redefined-outer-name, protected-access, missing-module-docstring, missing-class-docstring
# pyright: reportGeneralTypeIssues=false

from typing import List, cast
from unittest.mock import patch

import pytest
from neo4j import AsyncSession
from neo4j.graph import Node
from typing_extensions import LiteralString

from pyneo4j_ogm.core.client import Pyneo4jClient
from pyneo4j_ogm.exceptions import UnexpectedEmptyResult
from tests.fixtures.db_setup import CoffeeShop, client, session


async def test_refresh(client: Pyneo4jClient, session: AsyncSession):
    await client.register_models([CoffeeShop])

    node = CoffeeShop(rating=5, tags=["modern", "trendy"])
    await node.create()

    node.tags.append("neighborhood")

    await node.refresh()
    assert node.tags == ["modern", "trendy"]

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

    assert len(query_result) == 1
    assert len(query_result[0]) == 1

    node_result = query_result[0][0]
    assert node_result["tags"] == ["modern", "trendy"]


async def test_refresh_no_result(client: Pyneo4jClient):
    await client.register_models([CoffeeShop])

    node = CoffeeShop(rating=5, tags=["modern", "trendy"])
    await node.create()

    with patch.object(client, "cypher") as mock_cypher:
        mock_cypher.return_value = ([], [])

        with pytest.raises(UnexpectedEmptyResult):
            await node.refresh()
