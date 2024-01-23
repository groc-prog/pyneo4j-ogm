# pylint: disable=unused-argument, unused-import, redefined-outer-name, protected-access, missing-module-docstring, missing-class-docstring
# pyright: reportGeneralTypeIssues=false

import pytest
from neo4j import AsyncSession

from pyneo4j_ogm.core.client import EntityType, Pyneo4jClient
from pyneo4j_ogm.exceptions import InvalidEntityType, InvalidLabelOrType
from tests.fixtures.db_setup import client, session


async def test_invalid_constraints(client: Pyneo4jClient):
    with pytest.raises(InvalidLabelOrType):
        await client.create_uniqueness_constraint(
            "invalid_node_constraint", EntityType.NODE, ["prop_a", "prop_b"], "Test"
        )

    with pytest.raises(InvalidLabelOrType):
        await client.create_uniqueness_constraint(
            "invalid_relationship_constraint", EntityType.RELATIONSHIP, ["prop_a", "prop_b"], ["Test", "Relationship"]
        )

    with pytest.raises(InvalidEntityType):
        await client.create_uniqueness_constraint(
            "invalid_constraint", "invalid entity", ["prop_a", "prop_b"], ["Test", "Relationship"]  # type: ignore
        )


async def test_create_node_constraints(client: Pyneo4jClient, session: AsyncSession):
    await client.create_uniqueness_constraint(
        "node_constraint", EntityType.NODE, ["prop_a", "prop_b"], ["Test", "Node"]
    )

    node_constraint_results = await session.run("SHOW CONSTRAINTS")
    node_constraints = await node_constraint_results.values()
    await node_constraint_results.consume()

    assert node_constraints[0][1] == "node_constraint_Node_prop_a_prop_b_unique_constraint"
    assert node_constraints[0][2] == "UNIQUENESS"
    assert node_constraints[0][3] == "NODE"
    assert node_constraints[0][4] == ["Node"]
    assert node_constraints[0][5] == ["prop_a", "prop_b"]

    assert node_constraints[1][1] == "node_constraint_Test_prop_a_prop_b_unique_constraint"
    assert node_constraints[1][2] == "UNIQUENESS"
    assert node_constraints[1][3] == "NODE"
    assert node_constraints[1][4] == ["Test"]
    assert node_constraints[1][5] == ["prop_a", "prop_b"]


async def test_create_relationship_constraints(client: Pyneo4jClient, session: AsyncSession):
    await client.create_uniqueness_constraint(
        "relationship_constraint", EntityType.RELATIONSHIP, ["prop_a", "prop_b"], "TEST_RELATIONSHIP"
    )

    node_constraint_results = await session.run("SHOW CONSTRAINTS")
    node_constraints = await node_constraint_results.values()
    await node_constraint_results.consume()

    assert node_constraints[0][1] == "relationship_constraint_TEST_RELATIONSHIP_prop_a_prop_b_unique_constraint"
    assert node_constraints[0][2] == "RELATIONSHIP_UNIQUENESS"
    assert node_constraints[0][3] == "RELATIONSHIP"
    assert node_constraints[0][4] == ["TEST_RELATIONSHIP"]
    assert node_constraints[0][5] == ["prop_a", "prop_b"]
