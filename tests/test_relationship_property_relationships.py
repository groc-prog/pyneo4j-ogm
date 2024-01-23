# pylint: disable=unused-argument, unused-import, redefined-outer-name, protected-access, missing-module-docstring, missing-class-docstring
# pyright: reportGeneralTypeIssues=false

from typing import cast
from unittest.mock import patch

from neo4j.graph import Graph, Node, Relationship

from pyneo4j_ogm.core.client import Pyneo4jClient
from tests.fixtures.db_setup import (
    Developer,
    WorkedWith,
    client,
    dev_model_instances,
    session,
    setup_test_data,
)


async def test_relationships(client: Pyneo4jClient, dev_model_instances):
    await client.register_models([Developer, WorkedWith])

    john_model, sam_model, alice_model, *_ = dev_model_instances
    multi_relationships = await john_model.colleagues.relationships(sam_model)

    assert len(multi_relationships) == 2
    assert all(isinstance(relationship, WorkedWith) for relationship in multi_relationships)
    assert any(relationship for relationship in multi_relationships if relationship.language == "Python")
    assert any(relationship for relationship in multi_relationships if relationship.language == "Java")

    single_relationship = await john_model.colleagues.relationships(alice_model)

    assert len(single_relationship) == 1
    assert isinstance(single_relationship[0], WorkedWith)
    assert single_relationship[0].language == "Python"


async def test_relationships_no_match(client: Pyneo4jClient, dev_model_instances):
    await client.register_models([Developer, WorkedWith])

    john_model, _, _, bob_model = dev_model_instances
    multi_relationships = await john_model.colleagues.relationships(bob_model)

    assert len(multi_relationships) == 0


async def test_relationships_raw_result(client: Pyneo4jClient, dev_model_instances):
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

        john_model, _, _, bob_model = dev_model_instances
        raw_relationship = await john_model.colleagues.relationships(bob_model)

        assert len(raw_relationship) == 1
        assert isinstance(raw_relationship[0], WorkedWith)
        assert raw_relationship[0].language == "Go"
        assert raw_relationship[0]._start_node_element_id == mock_start_node.element_id
        assert raw_relationship[0]._start_node_id == mock_start_node.id


async def test_relationships_projections(client: Pyneo4jClient, dev_model_instances):
    await client.register_models([Developer, WorkedWith])

    john_model, sam_model, alice_model, *_ = dev_model_instances
    multi_relationships = await john_model.colleagues.relationships(sam_model, projections={"lang": "language"})

    assert len(multi_relationships) == 2
    assert all(isinstance(relationship, dict) for relationship in multi_relationships)
    assert all("lang" in cast(dict, relationship) for relationship in multi_relationships)

    single_relationship = await john_model.colleagues.relationships(alice_model, projections={"lang": "language"})

    assert len(single_relationship) == 1
    assert isinstance(single_relationship[0], dict)
    assert "lang" in cast(dict, single_relationship[0])


async def test_relationships_options(client: Pyneo4jClient, dev_model_instances):
    await client.register_models([Developer, WorkedWith])

    john_model, sam_model, *_ = dev_model_instances
    multi_relationships = await john_model.colleagues.relationships(sam_model, options={"skip": 1})

    assert len(multi_relationships) == 1
    assert all(isinstance(relationship, WorkedWith) for relationship in multi_relationships)


async def test_relationships_filters(client: Pyneo4jClient, dev_model_instances):
    await client.register_models([Developer, WorkedWith])

    john_model, sam_model, *_ = dev_model_instances
    multi_relationships = await john_model.colleagues.relationships(sam_model, filters={"language": "Java"})

    assert len(multi_relationships) == 1
    assert all(isinstance(relationship, WorkedWith) for relationship in multi_relationships)
