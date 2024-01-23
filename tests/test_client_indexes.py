# pylint: disable=unused-argument, unused-import, redefined-outer-name, protected-access, missing-module-docstring, missing-class-docstring
# pyright: reportGeneralTypeIssues=false

import pytest
from neo4j import AsyncSession

from pyneo4j_ogm.core.client import EntityType, Pyneo4jClient
from pyneo4j_ogm.exceptions import InvalidEntityType, InvalidLabelOrType
from tests.fixtures.db_setup import client, session


async def test_invalid_indexes(client: Pyneo4jClient):
    with pytest.raises(InvalidEntityType):
        await client.create_range_index(
            "invalid_entity_index", "invalid entity", ["prop_a", "prop_b"], ["Test", "Node"]  # type: ignore
        )

    with pytest.raises(InvalidEntityType):
        await client.create_text_index(
            "invalid_entity_index", "invalid entity", ["prop_a", "prop_b"], ["Test", "Node"]  # type: ignore
        )

    with pytest.raises(InvalidEntityType):
        await client.create_point_index(
            "invalid_entity_index", "invalid entity", ["prop_a", "prop_b"], ["Test", "Node"]  # type: ignore
        )

    with pytest.raises(InvalidEntityType):
        await client.create_lookup_index("invalid_entity_index", "invalid entity")  # type: ignore

    with pytest.raises(InvalidLabelOrType):
        await client.create_range_index("invalid_node_index", EntityType.NODE, [], "Test")

    with pytest.raises(InvalidLabelOrType):
        await client.create_range_index(
            "invalid_relationship_index", EntityType.RELATIONSHIP, [], ["Test", "Relationship"]
        )

    with pytest.raises(InvalidLabelOrType):
        await client.create_text_index("invalid_node_index", EntityType.NODE, [], "Test")

    with pytest.raises(InvalidLabelOrType):
        await client.create_text_index(
            "invalid_relationship_index", EntityType.RELATIONSHIP, [], ["Test", "Relationship"]
        )

    with pytest.raises(InvalidLabelOrType):
        await client.create_point_index("invalid_node_index", EntityType.NODE, [], "Test")

    with pytest.raises(InvalidLabelOrType):
        await client.create_point_index(
            "invalid_relationship_index", EntityType.RELATIONSHIP, [], ["Test", "Relationship"]
        )


async def test_create_node_range_indexes(client: Pyneo4jClient, session: AsyncSession):
    await client.create_range_index("node_range_index", EntityType.NODE, ["prop_a", "prop_b"], ["Test", "Node"])

    query_results = await session.run("SHOW INDEXES")
    index_results = await query_results.values()
    await query_results.consume()

    assert index_results[0][1] == "node_range_index_Node_prop_a_prop_b_range_index"
    assert index_results[0][4] == "RANGE"
    assert index_results[0][5] == EntityType.NODE
    assert index_results[0][6] == ["Node"]
    assert index_results[0][7] == ["prop_a", "prop_b"]

    assert index_results[1][1] == "node_range_index_Test_prop_a_prop_b_range_index"
    assert index_results[1][4] == "RANGE"
    assert index_results[1][5] == EntityType.NODE
    assert index_results[1][6] == ["Test"]
    assert index_results[1][7] == ["prop_a", "prop_b"]


async def test_create_relationship_range_indexes(client: Pyneo4jClient, session: AsyncSession):
    with pytest.raises(InvalidLabelOrType):
        await client.create_range_index(
            "invalid_relationship_index",
            EntityType.RELATIONSHIP,
            ["prop_a", "prop_b"],
            ["NotA", "String"],
        )

    await client.create_range_index("relationship_range_index", EntityType.RELATIONSHIP, ["prop_a", "prop_b"], "REL")

    query_results = await session.run("SHOW INDEXES")
    index_results = await query_results.values()
    await query_results.consume()

    assert index_results[0][1] == "relationship_range_index_REL_prop_a_prop_b_range_index"
    assert index_results[0][4] == "RANGE"
    assert index_results[0][5] == EntityType.RELATIONSHIP
    assert index_results[0][6] == ["REL"]
    assert index_results[0][7] == ["prop_a", "prop_b"]


async def test_create_node_text_indexes(client: Pyneo4jClient, session: AsyncSession):
    await client.create_text_index("node_text_index", EntityType.NODE, ["prop_a", "prop_b"], ["Test", "Node"])

    query_results = await session.run("SHOW INDEXES")
    index_results = await query_results.values()
    await query_results.consume()

    assert index_results[0][1] == "node_text_index_Node_prop_a_text_index"
    assert index_results[0][4] == "TEXT"
    assert index_results[0][5] == EntityType.NODE
    assert index_results[0][6] == ["Node"]
    assert index_results[0][7] == ["prop_a"]

    assert index_results[1][1] == "node_text_index_Node_prop_b_text_index"
    assert index_results[1][4] == "TEXT"
    assert index_results[1][5] == EntityType.NODE
    assert index_results[1][6] == ["Node"]
    assert index_results[1][7] == ["prop_b"]

    assert index_results[2][1] == "node_text_index_Test_prop_a_text_index"
    assert index_results[2][4] == "TEXT"
    assert index_results[2][5] == EntityType.NODE
    assert index_results[2][6] == ["Test"]
    assert index_results[2][7] == ["prop_a"]

    assert index_results[3][1] == "node_text_index_Test_prop_b_text_index"
    assert index_results[3][4] == "TEXT"
    assert index_results[3][5] == EntityType.NODE
    assert index_results[3][6] == ["Test"]
    assert index_results[3][7] == ["prop_b"]


async def test_create_relationship_text_indexes(client: Pyneo4jClient, session: AsyncSession):
    await client.create_text_index("relationship_text_index", EntityType.RELATIONSHIP, ["prop_a", "prop_b"], "REL")

    query_results = await session.run("SHOW INDEXES")
    index_results = await query_results.values()
    await query_results.consume()

    assert index_results[0][1] == "relationship_text_index_REL_prop_a_text_index"
    assert index_results[0][4] == "TEXT"
    assert index_results[0][5] == EntityType.RELATIONSHIP
    assert index_results[0][6] == ["REL"]
    assert index_results[0][7] == ["prop_a"]

    assert index_results[1][1] == "relationship_text_index_REL_prop_b_text_index"
    assert index_results[1][4] == "TEXT"
    assert index_results[1][5] == EntityType.RELATIONSHIP
    assert index_results[1][6] == ["REL"]
    assert index_results[1][7] == ["prop_b"]


async def test_create_node_lookup_indexes(client: Pyneo4jClient, session: AsyncSession):
    await client.create_lookup_index("node_lookup_index", EntityType.NODE)

    query_results = await session.run("SHOW INDEXES")
    index_results = await query_results.values()
    await query_results.consume()

    assert index_results[0][1] == "node_lookup_index_lookup_index"
    assert index_results[0][4] == "LOOKUP"
    assert index_results[0][5] == EntityType.NODE


async def test_create_relationship_lookup_indexes(client: Pyneo4jClient, session: AsyncSession):
    await client.create_lookup_index("relationship_lookup_index", EntityType.RELATIONSHIP)

    query_results = await session.run("SHOW INDEXES")
    index_results = await query_results.values()
    await query_results.consume()

    assert index_results[0][1] == "relationship_lookup_index_lookup_index"
    assert index_results[0][4] == "LOOKUP"
    assert index_results[0][5] == EntityType.RELATIONSHIP


async def test_create_node_point_indexes(client: Pyneo4jClient, session: AsyncSession):
    await client.create_point_index("node_point_index", EntityType.NODE, ["prop_a", "prop_b"], ["Test", "Node"])

    query_results = await session.run("SHOW INDEXES")
    index_results = await query_results.values()
    await query_results.consume()

    assert index_results[0][1] == "node_point_index_Node_prop_a_point_index"
    assert index_results[0][4] == "POINT"
    assert index_results[0][5] == EntityType.NODE
    assert index_results[0][6] == ["Node"]
    assert index_results[0][7] == ["prop_a"]

    assert index_results[1][1] == "node_point_index_Node_prop_b_point_index"
    assert index_results[1][4] == "POINT"
    assert index_results[1][5] == EntityType.NODE
    assert index_results[1][6] == ["Node"]
    assert index_results[1][7] == ["prop_b"]

    assert index_results[2][1] == "node_point_index_Test_prop_a_point_index"
    assert index_results[2][4] == "POINT"
    assert index_results[2][5] == EntityType.NODE
    assert index_results[2][6] == ["Test"]
    assert index_results[2][7] == ["prop_a"]

    assert index_results[3][1] == "node_point_index_Test_prop_b_point_index"
    assert index_results[3][4] == "POINT"
    assert index_results[3][5] == EntityType.NODE
    assert index_results[3][6] == ["Test"]
    assert index_results[3][7] == ["prop_b"]


async def test_create_relationship_point_indexes(client: Pyneo4jClient, session: AsyncSession):
    await client.create_point_index("relationship_point_index", EntityType.RELATIONSHIP, ["prop_a", "prop_b"], "REL")

    query_results = await session.run("SHOW INDEXES")
    index_results = await query_results.values()
    await query_results.consume()

    assert index_results[0][1] == "relationship_point_index_REL_prop_a_point_index"
    assert index_results[0][4] == "POINT"
    assert index_results[0][5] == EntityType.RELATIONSHIP
    assert index_results[0][6] == ["REL"]
    assert index_results[0][7] == ["prop_a"]

    assert index_results[1][1] == "relationship_point_index_REL_prop_b_point_index"
    assert index_results[1][4] == "POINT"
    assert index_results[1][5] == EntityType.RELATIONSHIP
    assert index_results[1][6] == ["REL"]
    assert index_results[1][7] == ["prop_b"]
