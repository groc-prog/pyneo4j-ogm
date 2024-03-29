# pylint: disable=unused-argument, unused-import, redefined-outer-name, protected-access, missing-module-docstring, missing-class-docstring
# pyright: reportGeneralTypeIssues=false

from typing import cast
from unittest.mock import patch

import pytest
from neo4j.graph import Node, Relationship

from pyneo4j_ogm.core.client import Pyneo4jClient
from pyneo4j_ogm.exceptions import UnexpectedEmptyResult
from tests.fixtures.db_setup import (
    Developer,
    WorkedWith,
    client,
    session,
    setup_test_data,
)


async def test_start_node(client: Pyneo4jClient, setup_test_data):
    await client.register_models([WorkedWith])

    relationship: Relationship = [
        result
        for result in setup_test_data[0][1]
        if result.type == "WAS_WORK_BUDDY_WITH" and result["language"] == "Go"
    ][0]
    node = cast(Node, relationship.start_node)

    relationship_model = WorkedWith(**relationship)
    relationship_model._element_id = relationship.element_id
    relationship_model._id = relationship.id
    relationship_model._start_node_element_id = cast(Node, relationship.start_node).element_id
    relationship_model._start_node_id = cast(Node, relationship.start_node).id
    relationship_model._end_node_element_id = cast(Node, relationship.end_node).element_id
    relationship_model._end_node_id = cast(Node, relationship.end_node).id

    relationship_model.language = "TypeScript"
    start_node = cast(Developer, await relationship_model.start_node())
    assert isinstance(start_node, Developer)
    assert start_node._element_id == node.element_id
    assert start_node._id == node.id


async def test_start_node_no_result(client: Pyneo4jClient, setup_test_data):
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

        with pytest.raises(UnexpectedEmptyResult):
            await relationship_model.start_node()
