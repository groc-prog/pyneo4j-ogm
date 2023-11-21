# pylint: disable=unused-argument, unused-import, redefined-outer-name, protected-access, missing-module-docstring

from typing import cast
from unittest.mock import patch

import pytest
from neo4j.graph import Graph, Node, Relationship

from pyneo4j_ogm.core.client import Pyneo4jClient
from tests.fixtures.db_setup import (
    Developer,
    WorkedWith,
    client,
    session,
    setup_test_data,
)

pytest_plugins = ("pytest_asyncio",)


@pytest.fixture
def use_node_models(setup_test_data):
    start_node: Node = [
        result for result in setup_test_data[0][0] if result.labels == {"Developer"} and result["uid"] == 1
    ][0]
    multi_connection_node: Node = [
        result for result in setup_test_data[0][0] if result.labels == {"Developer"} and result["uid"] == 2
    ][0]
    single_connection_node: Node = [
        result for result in setup_test_data[0][0] if result.labels == {"Developer"} and result["uid"] == 3
    ][0]
    no_connection_node: Node = [
        result for result in setup_test_data[0][0] if result.labels == {"Developer"} and result["uid"] == 4
    ][0]

    start_node_model = Developer(**start_node)
    start_node_model._element_id = start_node.element_id
    start_node_model._id = start_node.id

    multi_connection_node_model = Developer(**multi_connection_node)
    multi_connection_node_model._element_id = multi_connection_node.element_id
    multi_connection_node_model._id = multi_connection_node.id

    single_connection_node_model = Developer(**single_connection_node)
    single_connection_node_model._element_id = single_connection_node.element_id
    single_connection_node_model._id = single_connection_node.id

    no_connection_model = Developer(**no_connection_node)
    no_connection_model._element_id = no_connection_node.element_id
    no_connection_model._id = no_connection_node.id

    return start_node_model, multi_connection_node_model, single_connection_node_model, no_connection_model


async def test_relationships(client: Pyneo4jClient, use_node_models):
    await client.register_models([Developer, WorkedWith])

    start_node_model, multi_connection_node_model, single_connection_node_model, *_ = use_node_models
    multi_relationships = await start_node_model.colleagues.relationships(multi_connection_node_model)

    assert len(multi_relationships) == 2
    assert all(isinstance(relationship, WorkedWith) for relationship in multi_relationships)
    assert any(relationship for relationship in multi_relationships if relationship.language == "Python")
    assert any(relationship for relationship in multi_relationships if relationship.language == "Java")

    single_relationship = await start_node_model.colleagues.relationships(single_connection_node_model)

    assert len(single_relationship) == 1
    assert isinstance(single_relationship[0], WorkedWith)
    assert single_relationship[0].language == "Python"


async def test_relationships_no_match(client: Pyneo4jClient, use_node_models):
    await client.register_models([Developer, WorkedWith])

    start_node_model, _, _, no_connection_model = use_node_models
    multi_relationships = await start_node_model.colleagues.relationships(no_connection_model)

    assert len(multi_relationships) == 0


async def test_relationships_raw_result(client: Pyneo4jClient, use_node_models):
    await client.register_models([Developer, WorkedWith])

    with patch.object(client, "cypher") as mock_cypher:
        mock_start_node = Node(
            graph=Graph(),
            element_id="start-element-id",
            id_=2,
            properties={},
        )
        mock_end_node = Node(
            graph=Graph(),
            element_id="end-element-id",
            id_=3,
            properties={},
        )

        mock_relationship = Relationship(
            graph=Graph(),
            element_id="element-id",
            id_=1,
            properties={"language": "Go"},
        )
        setattr(mock_relationship, "_start_node", mock_start_node)
        setattr(mock_relationship, "_end_node", mock_end_node)

        mock_cypher.return_value = (
            [[mock_relationship, None]],
            [],
        )

        start_node_model, _, _, no_connection_model = use_node_models
        raw_relationship = await start_node_model.colleagues.relationships(no_connection_model)

        assert len(raw_relationship) == 1
        assert isinstance(raw_relationship[0], WorkedWith)
        assert raw_relationship[0].language == "Go"
        assert raw_relationship[0]._start_node_element_id == mock_start_node.element_id
        assert raw_relationship[0]._start_node_id == mock_start_node.id


async def test_relationships_projections(client: Pyneo4jClient, use_node_models):
    await client.register_models([Developer, WorkedWith])

    start_node_model, multi_connection_node_model, single_connection_node_model, *_ = use_node_models
    multi_relationships = await start_node_model.colleagues.relationships(
        multi_connection_node_model, projections={"lang": "language"}
    )

    assert len(multi_relationships) == 2
    assert all(isinstance(relationship, dict) for relationship in multi_relationships)
    assert all("lang" in cast(dict, relationship) for relationship in multi_relationships)

    single_relationship = await start_node_model.colleagues.relationships(
        single_connection_node_model, projections={"lang": "language"}
    )

    assert len(single_relationship) == 1
    assert isinstance(single_relationship[0], dict)
    assert "lang" in cast(dict, single_relationship[0])


async def test_relationships_options(client: Pyneo4jClient, use_node_models):
    await client.register_models([Developer, WorkedWith])

    start_node_model, multi_connection_node_model, *_ = use_node_models
    multi_relationships = await start_node_model.colleagues.relationships(
        multi_connection_node_model, options={"skip": 1}
    )

    assert len(multi_relationships) == 1
    assert all(isinstance(relationship, WorkedWith) for relationship in multi_relationships)


async def test_relationships_filters(client: Pyneo4jClient, use_node_models):
    await client.register_models([Developer, WorkedWith])

    start_node_model, multi_connection_node_model, *_ = use_node_models
    multi_relationships = await start_node_model.colleagues.relationships(
        multi_connection_node_model, filters={"language": "Java"}
    )

    assert len(multi_relationships) == 1
    assert all(isinstance(relationship, WorkedWith) for relationship in multi_relationships)
