# pylint: disable=unused-argument, unused-import, redefined-outer-name, protected-access, missing-module-docstring

from typing import cast

import pytest
from neo4j import AsyncSession
from neo4j.exceptions import CypherSyntaxError
from neo4j.graph import Node, Path, Relationship

from pyneo4j_ogm.core.client import EntityType, IndexType, Neo4jClient
from pyneo4j_ogm.exceptions import (
    InvalidEntityType,
    InvalidIndexType,
    InvalidLabelOrType,
    NotConnectedToDatabase,
)
from tests.integration.fixtures.database import neo4j_session, pyneo4j_client
from tests.integration.fixtures.models import (
    ClientNodeModel,
    ClientRelationshipModel,
    CypherResolvingNode,
    CypherResolvingRelationship,
)

pytest_plugins = ("pytest_asyncio",)


async def test_ensure_connection(pyneo4j_client: Neo4jClient):
    with pytest.raises(NotConnectedToDatabase):
        pyneo4j_client = Neo4jClient()
        await pyneo4j_client.cypher("MATCH (n) RETURN n")

    with pytest.raises(NotConnectedToDatabase):
        await pyneo4j_client.close()
        await pyneo4j_client.cypher("MATCH (n) RETURN n")

    await pyneo4j_client.connect("bolt://localhost:7687", auth=("neo4j", "password"))
    results, _ = await pyneo4j_client.cypher("MATCH (n) RETURN n")
    assert results == []


async def test_register_models(pyneo4j_client: Neo4jClient, neo4j_session: AsyncSession):
    await pyneo4j_client.register_models([ClientNodeModel, ClientRelationshipModel])

    assert ClientNodeModel in pyneo4j_client.models
    assert ClientRelationshipModel in pyneo4j_client.models

    query_results = await neo4j_session.run("SHOW CONSTRAINTS")
    constraint_results = [result.values() async for result in query_results]

    assert len(constraint_results) == 3

    query_results = await neo4j_session.run("SHOW INDEXES")
    index_results = [result.values() async for result in query_results]

    assert len(index_results) == 12

    # Indexes for 'TEST_RELATIONSHIP' type
    assert index_results[8][1] == "ClientRelationshipModel_TEST_RELATIONSHIP_a_unique_constraint"
    assert index_results[8][4] == IndexType.RANGE
    assert index_results[8][5] == EntityType.RELATIONSHIP
    assert index_results[8][6] == ["TEST_RELATIONSHIP"]
    assert index_results[8][7] == ["a"]

    assert index_results[9][1] == "ClientRelationshipModel_TEST_RELATIONSHIP_b_range_index"
    assert index_results[9][4] == IndexType.RANGE
    assert index_results[9][5] == EntityType.RELATIONSHIP
    assert index_results[9][6] == ["TEST_RELATIONSHIP"]
    assert index_results[9][7] == ["b"]

    assert index_results[10][1] == "ClientRelationshipModel_TEST_RELATIONSHIP_c_text_index"
    assert index_results[10][4] == IndexType.TEXT
    assert index_results[10][5] == EntityType.RELATIONSHIP
    assert index_results[10][6] == ["TEST_RELATIONSHIP"]
    assert index_results[10][7] == ["c"]

    assert index_results[11][1] == "ClientRelationshipModel_TEST_RELATIONSHIP_d_point_index"
    assert index_results[11][4] == IndexType.POINT
    assert index_results[11][5] == EntityType.RELATIONSHIP
    assert index_results[11][6] == ["TEST_RELATIONSHIP"]
    assert index_results[11][7] == ["d"]


async def test_cypher_query(pyneo4j_client: Neo4jClient, neo4j_session: AsyncSession):
    results, meta = await pyneo4j_client.cypher(
        "CREATE (n:Node) SET n.name = $name RETURN n", parameters={"name": "TestName"}
    )

    assert len(results) == 1
    assert len(results[0]) == 1
    assert isinstance(results[0][0], Node)
    assert meta == ["n"]

    query_results = await neo4j_session.run("MATCH (n:Node) RETURN n")
    result = await query_results.single()

    assert result is not None
    assert result["n"]["name"] == "TestName"


async def test_cypher_resolve_model_query(pyneo4j_client: Neo4jClient, neo4j_session: AsyncSession):
    await pyneo4j_client.register_models([CypherResolvingNode])

    result = await neo4j_session.run("CREATE (n:TestNode) SET n.name = $name", {"name": "TestName"})
    await result.consume()

    unresolved_results, _ = await pyneo4j_client.cypher(
        "MATCH (n:TestNode) WHERE n.name = $name RETURN n", {"name": "TestName"}, resolve_models=False
    )

    assert len(unresolved_results) == 1
    assert len(unresolved_results[0]) == 1
    assert isinstance(unresolved_results[0][0], Node)

    resolved_results, _ = await pyneo4j_client.cypher(
        "MATCH (n:TestNode) WHERE n.name = $name RETURN n", {"name": "TestName"}, resolve_models=True
    )

    assert len(resolved_results) == 1
    assert len(resolved_results[0]) == 1
    assert isinstance(resolved_results[0][0], CypherResolvingNode)


async def test_cypher_resolve_relationship_model_query(pyneo4j_client: Neo4jClient, neo4j_session: AsyncSession):
    await pyneo4j_client.register_models([CypherResolvingRelationship])

    result = await neo4j_session.run(
        "CREATE (:TestNode {name: $start})-[:TEST_RELATIONSHIP {kind: 'awesome'}]->(:TestNode {end: $end}) ",
        {"start": "start", "end": "end"},
    )
    await result.consume()

    unresolved_results, _ = await pyneo4j_client.cypher(
        "MATCH ()-[r:TEST_RELATIONSHIP]->() WHERE r.kind = $kind RETURN r", {"kind": "awesome"}, resolve_models=False
    )

    assert len(unresolved_results) == 1
    assert len(unresolved_results[0]) == 1
    assert isinstance(unresolved_results[0][0], Relationship)

    resolved_results, _ = await pyneo4j_client.cypher(
        "MATCH ()-[r:TEST_RELATIONSHIP]->() WHERE r.kind = $kind RETURN r", {"kind": "awesome"}, resolve_models=True
    )

    assert len(resolved_results) == 1
    assert len(resolved_results[0]) == 1
    assert isinstance(resolved_results[0][0], CypherResolvingRelationship)


async def test_cypher_resolve_path_query(pyneo4j_client: Neo4jClient, neo4j_session: AsyncSession):
    await pyneo4j_client.register_models([CypherResolvingNode, CypherResolvingRelationship])

    result = await neo4j_session.run(
        "CREATE (:TestNode {name: $start})-[:TEST_RELATIONSHIP {kind: 'awesome'}]->(:TestNode {name: $end}) ",
        {"start": "start", "end": "end"},
    )
    await result.consume()

    unresolved_results, _ = await pyneo4j_client.cypher(
        "MATCH path = (:TestNode)-[:TEST_RELATIONSHIP]->(:TestNode) RETURN path", resolve_models=False
    )

    assert len(unresolved_results) == 1
    assert len(unresolved_results[0]) == 1
    assert isinstance(unresolved_results[0][0], Path)
    assert isinstance(cast(Path, unresolved_results[0][0]).start_node, Node)
    assert isinstance(cast(Path, unresolved_results[0][0]).end_node, Node)
    assert isinstance(cast(Path, unresolved_results[0][0]).relationships[0], Relationship)

    resolved_results, _ = await pyneo4j_client.cypher(
        "MATCH path = (:TestNode)-[:TEST_RELATIONSHIP]->(:TestNode) RETURN path", resolve_models=True
    )

    assert len(resolved_results) == 1
    assert len(resolved_results[0]) == 1
    assert isinstance(resolved_results[0][0], Path)
    assert isinstance(cast(Path, resolved_results[0][0]).start_node, CypherResolvingNode)
    assert isinstance(cast(Path, resolved_results[0][0]).end_node, CypherResolvingNode)
    assert isinstance(cast(Path, resolved_results[0][0]).relationships[0], CypherResolvingRelationship)


async def test_cypher_query_exception(pyneo4j_client: Neo4jClient):
    with pytest.raises(CypherSyntaxError):
        await pyneo4j_client.cypher("MATCH n RETURN n", parameters={"a": 1})


async def test_invalid_constraints(pyneo4j_client: Neo4jClient):
    with pytest.raises(InvalidLabelOrType):
        await pyneo4j_client.create_constraint("invalid_node_constraint", EntityType.NODE, ["prop_a", "prop_b"], "Test")

    with pytest.raises(InvalidLabelOrType):
        await pyneo4j_client.create_constraint(
            "invalid_relationship_constraint", EntityType.RELATIONSHIP, ["prop_a", "prop_b"], ["Test", "Relationship"]
        )

    with pytest.raises(InvalidEntityType):
        await pyneo4j_client.create_constraint(
            "invalid_constraint", "invalid entity", ["prop_a", "prop_b"], ["Test", "Relationship"]  # type: ignore
        )


async def test_create_node_constraints(pyneo4j_client: Neo4jClient, neo4j_session: AsyncSession):
    await pyneo4j_client.create_constraint("node_constraint", EntityType.NODE, ["prop_a", "prop_b"], ["Test", "Node"])

    node_constraint_results = await neo4j_session.run("SHOW CONSTRAINTS")
    node_constraints = await node_constraint_results.values()

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


async def test_create_relationship_constraints(pyneo4j_client: Neo4jClient, neo4j_session: AsyncSession):
    await pyneo4j_client.create_constraint(
        "relationship_constraint", EntityType.RELATIONSHIP, ["prop_a", "prop_b"], "TEST_RELATIONSHIP"
    )

    node_constraint_results = await neo4j_session.run("SHOW CONSTRAINTS")
    node_constraints = await node_constraint_results.values()

    assert node_constraints[0][1] == "relationship_constraint_TEST_RELATIONSHIP_prop_a_prop_b_unique_constraint"
    assert node_constraints[0][2] == "RELATIONSHIP_UNIQUENESS"
    assert node_constraints[0][3] == "RELATIONSHIP"
    assert node_constraints[0][4] == ["TEST_RELATIONSHIP"]
    assert node_constraints[0][5] == ["prop_a", "prop_b"]


async def test_invalid_indexes(pyneo4j_client: Neo4jClient):
    with pytest.raises(InvalidIndexType):
        await pyneo4j_client.create_index(
            "invalid_node_index", EntityType.NODE, "Not valid", ["prop_a", "prop_b"], ["Test", "Node"]  # type: ignore
        )

    with pytest.raises(InvalidLabelOrType):
        await pyneo4j_client.create_index(
            "invalid_node_index", EntityType.NODE, IndexType.RANGE, "prop_a", "NotAList"  # type: ignore
        )

    with pytest.raises(InvalidIndexType):
        await pyneo4j_client.create_index(
            "invalid_relationship_index",
            EntityType.RELATIONSHIP,
            "Not valid",  # type: ignore
            ["prop_a", "prop_b"],
            "REL",
        )

    with pytest.raises(InvalidEntityType):
        await pyneo4j_client.create_index(
            "invalid_index", "invalid entity", IndexType.RANGE, ["prop_a", "prop_b"], "REL"  # type: ignore
        )


async def test_create_node_range_indexes(pyneo4j_client: Neo4jClient, neo4j_session: AsyncSession):
    await pyneo4j_client.create_index(
        "node_range_index", EntityType.NODE, IndexType.RANGE, ["prop_a", "prop_b"], ["Test", "Node"]
    )

    query_results = await neo4j_session.run("SHOW INDEXES")
    index_results = await query_results.values()

    assert index_results[0][1] == "node_range_index_Node_prop_a_prop_b_range_index"
    assert index_results[0][4] == IndexType.RANGE
    assert index_results[0][5] == EntityType.NODE
    assert index_results[0][6] == ["Node"]
    assert index_results[0][7] == ["prop_a", "prop_b"]

    assert index_results[1][1] == "node_range_index_Test_prop_a_prop_b_range_index"
    assert index_results[1][4] == IndexType.RANGE
    assert index_results[1][5] == EntityType.NODE
    assert index_results[1][6] == ["Test"]
    assert index_results[1][7] == ["prop_a", "prop_b"]


async def test_create_relationship_range_indexes(pyneo4j_client: Neo4jClient, neo4j_session: AsyncSession):
    with pytest.raises(InvalidLabelOrType):
        await pyneo4j_client.create_index(
            "invalid_relationship_index",
            EntityType.RELATIONSHIP,
            IndexType.RANGE,
            ["prop_a", "prop_b"],
            ["NotA", "String"],
        )

    await pyneo4j_client.create_index(
        "relationship_range_index", EntityType.RELATIONSHIP, IndexType.RANGE, ["prop_a", "prop_b"], "REL"
    )

    query_results = await neo4j_session.run("SHOW INDEXES")
    index_results = await query_results.values()

    assert index_results[0][1] == "relationship_range_index_REL_prop_a_prop_b_range_index"
    assert index_results[0][4] == IndexType.RANGE
    assert index_results[0][5] == EntityType.RELATIONSHIP
    assert index_results[0][6] == ["REL"]
    assert index_results[0][7] == ["prop_a", "prop_b"]


async def test_create_node_text_indexes(pyneo4j_client: Neo4jClient, neo4j_session: AsyncSession):
    await pyneo4j_client.create_index(
        "node_text_index", EntityType.NODE, IndexType.TEXT, ["prop_a", "prop_b"], ["Test", "Node"]
    )

    query_results = await neo4j_session.run("SHOW INDEXES")
    index_results = await query_results.values()

    assert index_results[0][1] == "node_text_index_Node_prop_a_text_index"
    assert index_results[0][4] == IndexType.TEXT
    assert index_results[0][5] == EntityType.NODE
    assert index_results[0][6] == ["Node"]
    assert index_results[0][7] == ["prop_a"]

    assert index_results[1][1] == "node_text_index_Node_prop_b_text_index"
    assert index_results[1][4] == IndexType.TEXT
    assert index_results[1][5] == EntityType.NODE
    assert index_results[1][6] == ["Node"]
    assert index_results[1][7] == ["prop_b"]

    assert index_results[2][1] == "node_text_index_Test_prop_a_text_index"
    assert index_results[2][4] == IndexType.TEXT
    assert index_results[2][5] == EntityType.NODE
    assert index_results[2][6] == ["Test"]
    assert index_results[2][7] == ["prop_a"]

    assert index_results[3][1] == "node_text_index_Test_prop_b_text_index"
    assert index_results[3][4] == IndexType.TEXT
    assert index_results[3][5] == EntityType.NODE
    assert index_results[3][6] == ["Test"]
    assert index_results[3][7] == ["prop_b"]


async def test_create_relationship_text_indexes(pyneo4j_client: Neo4jClient, neo4j_session: AsyncSession):
    await pyneo4j_client.create_index(
        "relationship_text_index", EntityType.RELATIONSHIP, IndexType.TEXT, ["prop_a", "prop_b"], "REL"
    )

    query_results = await neo4j_session.run("SHOW INDEXES")
    index_results = await query_results.values()

    assert index_results[0][1] == "relationship_text_index_REL_prop_a_text_index"
    assert index_results[0][4] == IndexType.TEXT
    assert index_results[0][5] == EntityType.RELATIONSHIP
    assert index_results[0][6] == ["REL"]
    assert index_results[0][7] == ["prop_a"]

    assert index_results[1][1] == "relationship_text_index_REL_prop_b_text_index"
    assert index_results[1][4] == IndexType.TEXT
    assert index_results[1][5] == EntityType.RELATIONSHIP
    assert index_results[1][6] == ["REL"]
    assert index_results[1][7] == ["prop_b"]


async def test_create_node_lookup_indexes(pyneo4j_client: Neo4jClient, neo4j_session: AsyncSession):
    await pyneo4j_client.create_index(
        "node_lookup_index", EntityType.NODE, IndexType.LOOKUP, ["prop_a", "prop_b"], ["Test", "Node"]
    )

    query_results = await neo4j_session.run("SHOW INDEXES")
    index_results = await query_results.values()

    assert index_results[0][1] == "node_lookup_index_Test_Node_prop_a_prop_b_lookup_index"
    assert index_results[0][4] == IndexType.LOOKUP
    assert index_results[0][5] == EntityType.NODE


async def test_create_relationship_lookup_indexes(pyneo4j_client: Neo4jClient, neo4j_session: AsyncSession):
    await pyneo4j_client.create_index(
        "relationship_lookup_index", EntityType.RELATIONSHIP, IndexType.LOOKUP, ["prop_a", "prop_b"], "REL"
    )

    query_results = await neo4j_session.run("SHOW INDEXES")
    index_results = await query_results.values()

    assert index_results[0][1] == "relationship_lookup_index_REL_prop_a_prop_b_lookup_index"
    assert index_results[0][4] == IndexType.LOOKUP
    assert index_results[0][5] == EntityType.RELATIONSHIP


async def test_create_node_point_indexes(pyneo4j_client: Neo4jClient, neo4j_session: AsyncSession):
    await pyneo4j_client.create_index(
        "node_point_index", EntityType.NODE, IndexType.POINT, ["prop_a", "prop_b"], ["Test", "Node"]
    )

    query_results = await neo4j_session.run("SHOW INDEXES")
    index_results = await query_results.values()

    assert index_results[0][1] == "node_point_index_Node_prop_a_point_index"
    assert index_results[0][4] == IndexType.POINT
    assert index_results[0][5] == EntityType.NODE
    assert index_results[0][6] == ["Node"]
    assert index_results[0][7] == ["prop_a"]

    assert index_results[1][1] == "node_point_index_Node_prop_b_point_index"
    assert index_results[1][4] == IndexType.POINT
    assert index_results[1][5] == EntityType.NODE
    assert index_results[1][6] == ["Node"]
    assert index_results[1][7] == ["prop_b"]

    assert index_results[2][1] == "node_point_index_Test_prop_a_point_index"
    assert index_results[2][4] == IndexType.POINT
    assert index_results[2][5] == EntityType.NODE
    assert index_results[2][6] == ["Test"]
    assert index_results[2][7] == ["prop_a"]

    assert index_results[3][1] == "node_point_index_Test_prop_b_point_index"
    assert index_results[3][4] == IndexType.POINT
    assert index_results[3][5] == EntityType.NODE
    assert index_results[3][6] == ["Test"]
    assert index_results[3][7] == ["prop_b"]


async def test_create_relationship_point_indexes(pyneo4j_client: Neo4jClient, neo4j_session: AsyncSession):
    await pyneo4j_client.create_index(
        "relationship_point_index", EntityType.RELATIONSHIP, IndexType.POINT, ["prop_a", "prop_b"], "REL"
    )

    query_results = await neo4j_session.run("SHOW INDEXES")
    index_results = await query_results.values()

    assert index_results[0][1] == "relationship_point_index_REL_prop_a_point_index"
    assert index_results[0][4] == IndexType.POINT
    assert index_results[0][5] == EntityType.RELATIONSHIP
    assert index_results[0][6] == ["REL"]
    assert index_results[0][7] == ["prop_a"]

    assert index_results[1][1] == "relationship_point_index_REL_prop_b_point_index"
    assert index_results[1][4] == IndexType.POINT
    assert index_results[1][5] == EntityType.RELATIONSHIP
    assert index_results[1][6] == ["REL"]
    assert index_results[1][7] == ["prop_b"]


async def test_drop_nodes(pyneo4j_client: Neo4jClient, neo4j_session: AsyncSession):
    print("BEFORE CREATE")
    result = await neo4j_session.run("CREATE (n:Node) SET n.name = $name", {"name": "TestName"})
    await result.consume()

    await pyneo4j_client.drop_nodes()
    print("DROPPED")

    query_results = await neo4j_session.run("MATCH (n) RETURN n")
    results = await query_results.values()

    assert len(results) == 0


async def test_drop_constraints(pyneo4j_client: Neo4jClient, neo4j_session: AsyncSession):
    result = await neo4j_session.run("CREATE CONSTRAINT test FOR (n:Node) REQUIRE n.name IS UNIQUE")
    await result.consume()

    await pyneo4j_client.drop_constraints()

    query_results = await neo4j_session.run("SHOW CONSTRAINTS")
    results = await query_results.values()

    assert len(results) == 0


async def test_drop_indexes(pyneo4j_client: Neo4jClient, neo4j_session: AsyncSession):
    result = await neo4j_session.run("CREATE INDEX test FOR (n:Node) ON (n.name)")
    await result.consume()

    await pyneo4j_client.drop_indexes()

    query_results = await neo4j_session.run("SHOW INDEXES")
    results = await query_results.values()

    assert len(results) == 0


async def test_batch_exception(pyneo4j_client: Neo4jClient, neo4j_session: AsyncSession):
    with pytest.raises(Exception):
        async with pyneo4j_client.batch():
            await pyneo4j_client.cypher("CREATE (n:Node) SET n.name = $name", parameters={"name": "TestName"})
            await pyneo4j_client.cypher("CREATE (n:Node) SET n.name = $name", parameters={"name": "TestName2"})

            raise Exception("Test Exception")  # pylint: disable=broad-exception-raised

    query_results = await neo4j_session.run("MATCH (n) RETURN n")
    results = await query_results.values()

    assert len(results) == 0
