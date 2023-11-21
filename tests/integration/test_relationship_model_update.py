# pylint: disable=unused-argument, unused-import, redefined-outer-name, protected-access, missing-module-docstring

from typing import List, cast
from unittest.mock import patch

import pytest
from neo4j import AsyncSession
from neo4j.graph import Node, Relationship
from typing_extensions import LiteralString

from pyneo4j_ogm.core.client import Pyneo4jClient
from pyneo4j_ogm.exceptions import NoResultsFound
from tests.fixtures.db_setup import WorkedWith, client, session, setup_test_data

pytest_plugins = ("pytest_asyncio",)


async def test_update(client: Pyneo4jClient, session: AsyncSession, setup_test_data):
    await client.register_models([WorkedWith])

    relationship: Relationship = [
        result
        for result in setup_test_data[0][1]
        if result.type == "WAS_WORK_BUDDY_WITH" and result["language"] == "Go"
    ][0]

    relationship_model = WorkedWith(**relationship)
    relationship_model._element_id = relationship.element_id
    relationship_model._id = relationship.id
    relationship_model._start_node_element_id = cast(Node, relationship.start_node).element_id
    relationship_model._start_node_id = cast(Node, relationship.start_node).id
    relationship_model._end_node_element_id = cast(Node, relationship.end_node).element_id
    relationship_model._end_node_id = cast(Node, relationship.end_node).id

    relationship_model.language = "TypeScript"
    await relationship_model.update()
    assert relationship_model.language == "TypeScript"
    assert relationship_model._db_properties == {"language": "TypeScript"}

    results = await session.run(
        cast(
            LiteralString,
            f"""
            MATCH ()-[r:{WorkedWith.model_settings().type}]->()
            WHERE elementId(r) = $element_id
            RETURN r
            """,
        ),
        {"element_id": relationship_model._element_id},
    )
    query_result: List[List[Relationship]] = await results.values()
    await results.consume()

    assert len(query_result) == 1
    assert len(query_result[0]) == 1

    relationship_result = query_result[0][0]
    assert relationship_result["language"] == "TypeScript"


async def test_update_no_result(client: Pyneo4jClient, setup_test_data):
    await client.register_models([WorkedWith])

    relationship: Relationship = [
        result
        for result in setup_test_data[0][1]
        if result.type == "WAS_WORK_BUDDY_WITH" and result["language"] == "Go"
    ][0]

    relationship_model = WorkedWith(**relationship)
    relationship_model._element_id = relationship.element_id
    relationship_model._id = relationship.id
    relationship_model._start_node_element_id = cast(Node, relationship.start_node).element_id
    relationship_model._start_node_id = cast(Node, relationship.start_node).id
    relationship_model._end_node_element_id = cast(Node, relationship.end_node).element_id
    relationship_model._end_node_id = cast(Node, relationship.end_node).id

    with patch.object(client, "cypher") as mock_cypher:
        mock_cypher.return_value = ([], [])

        with pytest.raises(NoResultsFound):
            relationship_model.language = "TypeScript"
            await relationship_model.update()
