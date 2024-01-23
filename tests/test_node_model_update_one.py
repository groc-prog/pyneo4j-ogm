# pylint: disable=unused-argument, unused-import, redefined-outer-name, protected-access, missing-module-docstring, missing-class-docstring
# pyright: reportGeneralTypeIssues=false

from typing import List, cast
from unittest.mock import patch

import pytest
from neo4j import AsyncSession
from neo4j.graph import Graph, Node
from typing_extensions import LiteralString

from pyneo4j_ogm.core.client import Pyneo4jClient
from pyneo4j_ogm.exceptions import InvalidFilters, NoResultFound
from tests.fixtures.db_setup import Developer, client, session, setup_test_data


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
    await results.consume()

    assert len(query_result) == 1
    assert query_result[0][0]["age"] == 50


async def test_update_one_raw_result(client: Pyneo4jClient):
    await client.register_models([Developer])

    with patch.object(client, "cypher") as mock_cypher:
        mock_node = Node(
            graph=Graph(),
            element_id="element-id",
            id_=1,
            properties={"age": 30, "uid": 1, "name": "John"},
        )
        mock_cypher.return_value = (
            [[mock_node]],
            [],
        )

        found_node = await Developer.find_one({"my_prop": "non-existent"})

        assert found_node is not None
        assert isinstance(found_node, Developer)
        assert found_node._id == mock_node.id
        assert found_node._element_id == mock_node.element_id
        assert found_node.age == mock_node["age"]
        assert found_node.uid == mock_node["uid"]
        assert found_node.name == mock_node["name"]


async def test_update_one_return_updated(setup_test_data):
    updated_node = await Developer.update_one({"age": 50}, {"uid": 1}, new=True)

    assert updated_node is not None
    assert isinstance(updated_node, Developer)
    assert updated_node.age == 50


async def test_update_one_no_match(setup_test_data):
    updated_node = await Developer.update_one({"age": 50}, {"uid": 99999})

    assert updated_node is None

    with pytest.raises(NoResultFound):
        await Developer.update_one({"age": 50}, {"uid": 99999}, raise_on_empty=True)


async def test_update_one_missing_filters(client: Pyneo4jClient):
    await client.register_models([Developer])

    with pytest.raises(InvalidFilters):
        await Developer.update_one({"my_prop": "updated"}, {})
