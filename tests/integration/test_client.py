# pylint: disable=unused-argument, unused-import, redefined-outer-name, protected-access, missing-module-docstring

import os
from typing import Any, AsyncGenerator, cast

import pytest
from neo4j import AsyncDriver
from neo4j.exceptions import CypherSyntaxError
from neo4j.graph import Node, Path, Relationship

from pyneo4j_ogm.core.client import EntityType, IndexType, Neo4jClient
from pyneo4j_ogm.exceptions import (
    InvalidEntityType,
    InvalidIndexType,
    InvalidLabelOrType,
    MissingDatabaseURI,
    NotConnectedToDatabase,
)
from tests.integration.fixtures.database import neo4j_driver, package_client
from tests.integration.fixtures.models import (
    ClientNodeModel,
    ClientRelationshipModel,
    CypherResolvingNode,
    CypherResolvingRelationship,
)

pytest_plugins = ("pytest_asyncio",)


@pytest.mark.asyncio
async def test_connection():
    client = Neo4jClient().connect("bolt://localhost:7687", auth=("neo4j", "password"))
    assert client.is_connected
    assert client._driver is not None

    await client.close()
    assert not client.is_connected
    assert client._driver is None

    # Test that the Neo4jClient can connect to a database using ENV variables.
    os.environ["NEO4J_OGM_URI"] = "bolt://localhost:7687"

    client = Neo4jClient().connect(auth=("neo4j", "password"))
    assert client.is_connected
    assert client._driver is not None

    await client.close()
    assert not client.is_connected
    assert client._driver is None

    os.environ.pop("NEO4J_OGM_URI")

    with pytest.raises(MissingDatabaseURI):
        # Test raised exception when no URI is provided.
        client = Neo4jClient().connect()


@pytest.mark.asyncio
async def test_ensure_connection(package_client: AsyncGenerator[Neo4jClient, Any]):
    with pytest.raises(NotConnectedToDatabase):
        client = Neo4jClient()
        await client.cypher("MATCH (n) RETURN n")

    client = await anext(package_client)
    with pytest.raises(NotConnectedToDatabase):
        await client.close()
        await client.cypher("MATCH (n) RETURN n")

    client.connect("bolt://localhost:7687", auth=("neo4j", "password"))
    results, _ = await client.cypher("MATCH (n) RETURN n")
    assert results == []


@pytest.mark.asyncio
async def test_register_models(
    package_client: AsyncGenerator[Neo4jClient, Any], neo4j_driver: AsyncGenerator[AsyncDriver, Any]
):
    driver = await anext(neo4j_driver)
    client = await anext(package_client)
    await client.register_models([ClientNodeModel, ClientRelationshipModel])

    assert ClientNodeModel in client.models
    assert ClientRelationshipModel in client.models

    async with driver.session() as session:
        query_results = await session.run("SHOW CONSTRAINTS")
        constraint_results = [result.values() async for result in query_results]

        assert len(constraint_results) == 3

    async with driver.session() as session:
        query_results = await session.run("SHOW INDEXES")
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


@pytest.mark.asyncio
async def test_cypher_query(
    package_client: AsyncGenerator[Neo4jClient, Any], neo4j_driver: AsyncGenerator[AsyncDriver, Any]
):
    driver = await anext(neo4j_driver)
    client = await anext(package_client)

    results, meta = await client.cypher("CREATE (n:Node) SET n.name = $name RETURN n", parameters={"name": "TestName"})

    assert len(results) == 1
    assert len(results[0]) == 1
    assert isinstance(results[0][0], Node)
    assert meta == ["n"]

    async with driver.session() as session:
        query_results = await session.run("MATCH (n:Node) RETURN n")
        result = await query_results.single()

        assert result is not None
        assert result["n"]["name"] == "TestName"


@pytest.mark.asyncio
async def test_cypher_resolve_model_query(
    package_client: AsyncGenerator[Neo4jClient, Any], neo4j_driver: AsyncGenerator[AsyncDriver, Any]
):
    driver = await anext(neo4j_driver)
    client = await anext(package_client)
    await client.register_models([CypherResolvingNode])

    async with driver.session() as session:
        await session.run("CREATE (n:TestNode) SET n.name = $name", {"name": "TestName"})

    unresolved_results, _ = await client.cypher(
        "MATCH (n:TestNode) WHERE n.name = $name RETURN n", {"name": "TestName"}, resolve_models=False
    )

    assert len(unresolved_results) == 1
    assert len(unresolved_results[0]) == 1
    assert isinstance(unresolved_results[0][0], Node)

    resolved_results, _ = await client.cypher(
        "MATCH (n:TestNode) WHERE n.name = $name RETURN n", {"name": "TestName"}, resolve_models=True
    )

    assert len(resolved_results) == 1
    assert len(resolved_results[0]) == 1
    assert isinstance(resolved_results[0][0], CypherResolvingNode)


@pytest.mark.asyncio
async def test_cypher_resolve_relationship_model_query(
    package_client: AsyncGenerator[Neo4jClient, Any], neo4j_driver: AsyncGenerator[AsyncDriver, Any]
):
    driver = await anext(neo4j_driver)
    client = await anext(package_client)
    await client.register_models([CypherResolvingRelationship])

    async with driver.session() as session:
        await session.run(
            "CREATE (:TestNode {name: $start})-[:TEST_RELATIONSHIP {kind: 'awesome'}]->(:TestNode {end: $end}) ",
            {"start": "start", "end": "end"},
        )

    unresolved_results, _ = await client.cypher(
        "MATCH ()-[r:TEST_RELATIONSHIP]->() WHERE r.kind = $kind RETURN r", {"kind": "awesome"}, resolve_models=False
    )

    assert len(unresolved_results) == 1
    assert len(unresolved_results[0]) == 1
    assert isinstance(unresolved_results[0][0], Relationship)

    resolved_results, _ = await client.cypher(
        "MATCH ()-[r:TEST_RELATIONSHIP]->() WHERE r.kind = $kind RETURN r", {"kind": "awesome"}, resolve_models=True
    )

    assert len(resolved_results) == 1
    assert len(resolved_results[0]) == 1
    assert isinstance(resolved_results[0][0], CypherResolvingRelationship)


@pytest.mark.asyncio
async def test_cypher_resolve_path_query(
    package_client: AsyncGenerator[Neo4jClient, Any], neo4j_driver: AsyncGenerator[AsyncDriver, Any]
):
    driver = await anext(neo4j_driver)
    client = await anext(package_client)
    await client.register_models([CypherResolvingNode, CypherResolvingRelationship])

    async with driver.session() as session:
        await session.run(
            "CREATE (:TestNode {name: $start})-[:TEST_RELATIONSHIP {kind: 'awesome'}]->(:TestNode {name: $end}) ",
            {"start": "start", "end": "end"},
        )

    unresolved_results, _ = await client.cypher(
        "MATCH path = (:TestNode)-[:TEST_RELATIONSHIP]->(:TestNode) RETURN path", resolve_models=False
    )

    assert len(unresolved_results) == 1
    assert len(unresolved_results[0]) == 1
    assert isinstance(unresolved_results[0][0], Path)
    assert isinstance(cast(Path, unresolved_results[0][0]).start_node, Node)
    assert isinstance(cast(Path, unresolved_results[0][0]).end_node, Node)
    assert isinstance(cast(Path, unresolved_results[0][0]).relationships[0], Relationship)

    resolved_results, _ = await client.cypher(
        "MATCH path = (:TestNode)-[:TEST_RELATIONSHIP]->(:TestNode) RETURN path", resolve_models=True
    )

    assert len(resolved_results) == 1
    assert len(resolved_results[0]) == 1
    assert isinstance(resolved_results[0][0], Path)
    assert isinstance(cast(Path, resolved_results[0][0]).start_node, CypherResolvingNode)
    assert isinstance(cast(Path, resolved_results[0][0]).end_node, CypherResolvingNode)
    assert isinstance(cast(Path, resolved_results[0][0]).relationships[0], CypherResolvingRelationship)


@pytest.mark.asyncio
async def test_cypher_query_exception(package_client: AsyncGenerator[Neo4jClient, Any]):
    client = await anext(package_client)

    with pytest.raises(CypherSyntaxError):
        await client.cypher("MATCH n RETURN n", parameters={"a": 1})


@pytest.mark.asyncio
async def test_invalid_constraints(package_client: AsyncGenerator[Neo4jClient, Any]):
    client = await anext(package_client)

    with pytest.raises(InvalidLabelOrType):
        await client.create_constraint("invalid_node_constraint", EntityType.NODE, ["prop_a", "prop_b"], "Test")

    with pytest.raises(InvalidLabelOrType):
        await client.create_constraint(
            "invalid_relationship_constraint", EntityType.RELATIONSHIP, ["prop_a", "prop_b"], ["Test", "Relationship"]
        )

    with pytest.raises(InvalidEntityType):
        await client.create_constraint(
            "invalid_constraint", "invalid entity", ["prop_a", "prop_b"], ["Test", "Relationship"]  # type: ignore
        )


@pytest.mark.asyncio
async def test_create_node_constraints(
    package_client: AsyncGenerator[Neo4jClient, Any], neo4j_driver: AsyncGenerator[AsyncDriver, Any]
):
    driver = await anext(neo4j_driver)
    client = await anext(package_client)

    await client.create_constraint("node_constraint", EntityType.NODE, ["prop_a", "prop_b"], ["Test", "Node"])

    async with driver.session() as session:
        node_constraint_results = await session.run("SHOW CONSTRAINTS")
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


@pytest.mark.asyncio
async def test_create_relationship_constraints(
    package_client: AsyncGenerator[Neo4jClient, Any], neo4j_driver: AsyncGenerator[AsyncDriver, Any]
):
    driver = await anext(neo4j_driver)
    client = await anext(package_client)

    await client.create_constraint(
        "relationship_constraint", EntityType.RELATIONSHIP, ["prop_a", "prop_b"], "TEST_RELATIONSHIP"
    )

    async with driver.session() as session:
        node_constraint_results = await session.run("SHOW CONSTRAINTS")
        node_constraints = await node_constraint_results.values()

        assert node_constraints[0][1] == "relationship_constraint_TEST_RELATIONSHIP_prop_a_prop_b_unique_constraint"
        assert node_constraints[0][2] == "RELATIONSHIP_UNIQUENESS"
        assert node_constraints[0][3] == "RELATIONSHIP"
        assert node_constraints[0][4] == ["TEST_RELATIONSHIP"]
        assert node_constraints[0][5] == ["prop_a", "prop_b"]


@pytest.mark.asyncio
async def test_invalid_indexes(package_client: AsyncGenerator[Neo4jClient, Any]):
    client = await anext(package_client)

    with pytest.raises(InvalidIndexType):
        await client.create_index(
            "invalid_node_index", EntityType.NODE, "Not valid", ["prop_a", "prop_b"], ["Test", "Node"]  # type: ignore
        )

    with pytest.raises(InvalidLabelOrType):
        await client.create_index(
            "invalid_node_index", EntityType.NODE, IndexType.RANGE, "prop_a", "NotAList"  # type: ignore
        )

    with pytest.raises(InvalidIndexType):
        await client.create_index(
            "invalid_relationship_index",
            EntityType.RELATIONSHIP,
            "Not valid",  # type: ignore
            ["prop_a", "prop_b"],
            "REL",
        )

    with pytest.raises(InvalidEntityType):
        await client.create_index(
            "invalid_index", "invalid entity", IndexType.RANGE, ["prop_a", "prop_b"], "REL"  # type: ignore
        )


@pytest.mark.asyncio
async def test_create_node_range_indexes(
    package_client: AsyncGenerator[Neo4jClient, Any], neo4j_driver: AsyncGenerator[AsyncDriver, Any]
):
    driver = await anext(neo4j_driver)
    client = await anext(package_client)

    await client.create_index(
        "node_range_index", EntityType.NODE, IndexType.RANGE, ["prop_a", "prop_b"], ["Test", "Node"]
    )

    async with driver.session() as session:
        query_results = await session.run("SHOW INDEXES")
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


@pytest.mark.asyncio
async def test_create_relationship_range_indexes(
    package_client: AsyncGenerator[Neo4jClient, Any], neo4j_driver: AsyncGenerator[AsyncDriver, Any]
):
    driver = await anext(neo4j_driver)
    client = await anext(package_client)

    with pytest.raises(InvalidLabelOrType):
        await client.create_index(
            "invalid_relationship_index",
            EntityType.RELATIONSHIP,
            IndexType.RANGE,
            ["prop_a", "prop_b"],
            ["NotA", "String"],
        )

    await client.create_index(
        "relationship_range_index", EntityType.RELATIONSHIP, IndexType.RANGE, ["prop_a", "prop_b"], "REL"
    )

    async with driver.session() as session:
        query_results = await session.run("SHOW INDEXES")
        index_results = await query_results.values()

        assert index_results[0][1] == "relationship_range_index_REL_prop_a_prop_b_range_index"
        assert index_results[0][4] == IndexType.RANGE
        assert index_results[0][5] == EntityType.RELATIONSHIP
        assert index_results[0][6] == ["REL"]
        assert index_results[0][7] == ["prop_a", "prop_b"]


@pytest.mark.asyncio
async def test_create_node_text_indexes(
    package_client: AsyncGenerator[Neo4jClient, Any], neo4j_driver: AsyncGenerator[AsyncDriver, Any]
):
    driver = await anext(neo4j_driver)
    client = await anext(package_client)

    await client.create_index(
        "node_text_index", EntityType.NODE, IndexType.TEXT, ["prop_a", "prop_b"], ["Test", "Node"]
    )

    async with driver.session() as session:
        query_results = await session.run("SHOW INDEXES")
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


@pytest.mark.asyncio
async def test_create_relationship_text_indexes(
    package_client: AsyncGenerator[Neo4jClient, Any], neo4j_driver: AsyncGenerator[AsyncDriver, Any]
):
    driver = await anext(neo4j_driver)
    client = await anext(package_client)

    await client.create_index(
        "relationship_text_index", EntityType.RELATIONSHIP, IndexType.TEXT, ["prop_a", "prop_b"], "REL"
    )

    async with driver.session() as session:
        query_results = await session.run("SHOW INDEXES")
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


@pytest.mark.asyncio
async def test_create_node_lookup_indexes(
    package_client: AsyncGenerator[Neo4jClient, Any], neo4j_driver: AsyncGenerator[AsyncDriver, Any]
):
    driver = await anext(neo4j_driver)
    client = await anext(package_client)

    await client.create_index(
        "node_lookup_index", EntityType.NODE, IndexType.LOOKUP, ["prop_a", "prop_b"], ["Test", "Node"]
    )

    async with driver.session() as session:
        query_results = await session.run("SHOW INDEXES")
        index_results = await query_results.values()

        assert index_results[0][1] == "node_lookup_index_Test_Node_prop_a_prop_b_lookup_index"
        assert index_results[0][4] == IndexType.LOOKUP
        assert index_results[0][5] == EntityType.NODE


@pytest.mark.asyncio
async def test_create_relationship_lookup_indexes(
    package_client: AsyncGenerator[Neo4jClient, Any], neo4j_driver: AsyncGenerator[AsyncDriver, Any]
):
    driver = await anext(neo4j_driver)
    client = await anext(package_client)

    await client.create_index(
        "relationship_lookup_index", EntityType.RELATIONSHIP, IndexType.LOOKUP, ["prop_a", "prop_b"], "REL"
    )

    async with driver.session() as session:
        query_results = await session.run("SHOW INDEXES")
        index_results = await query_results.values()

        assert index_results[0][1] == "relationship_lookup_index_REL_prop_a_prop_b_lookup_index"
        assert index_results[0][4] == IndexType.LOOKUP
        assert index_results[0][5] == EntityType.RELATIONSHIP


@pytest.mark.asyncio
async def test_create_node_point_indexes(
    package_client: AsyncGenerator[Neo4jClient, Any], neo4j_driver: AsyncGenerator[AsyncDriver, Any]
):
    driver = await anext(neo4j_driver)
    client = await anext(package_client)

    await client.create_index(
        "node_point_index", EntityType.NODE, IndexType.POINT, ["prop_a", "prop_b"], ["Test", "Node"]
    )

    async with driver.session() as session:
        query_results = await session.run("SHOW INDEXES")
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


@pytest.mark.asyncio
async def test_create_relationship_point_indexes(
    package_client: AsyncGenerator[Neo4jClient, Any], neo4j_driver: AsyncGenerator[AsyncDriver, Any]
):
    driver = await anext(neo4j_driver)
    client = await anext(package_client)

    await client.create_index(
        "relationship_point_index", EntityType.RELATIONSHIP, IndexType.POINT, ["prop_a", "prop_b"], "REL"
    )

    async with driver.session() as session:
        query_results = await session.run("SHOW INDEXES")
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


@pytest.mark.asyncio
async def test_drop_nodes(
    package_client: AsyncGenerator[Neo4jClient, Any], neo4j_driver: AsyncGenerator[AsyncDriver, Any]
):
    driver = await anext(neo4j_driver)
    client = await anext(package_client)

    async with driver.session() as session:
        await session.run("CREATE (n:Node) SET n.name = $name", {"name": "TestName"})

    await client.drop_nodes()

    async with driver.session() as session:
        query_results = await session.run("MATCH (n) RETURN n")
        results = await query_results.values()

        assert len(results) == 0


@pytest.mark.asyncio
async def test_drop_constraints(
    package_client: AsyncGenerator[Neo4jClient, Any], neo4j_driver: AsyncGenerator[AsyncDriver, Any]
):
    driver = await anext(neo4j_driver)
    client = await anext(package_client)

    async with driver.session() as session:
        await session.run("CREATE CONSTRAINT test FOR (n:Node) REQUIRE n.name IS UNIQUE")

    await client.drop_constraints()

    async with driver.session() as session:
        query_results = await session.run("SHOW CONSTRAINTS")
        results = await query_results.values()

        assert len(results) == 0


@pytest.mark.asyncio
async def test_drop_indexes(
    package_client: AsyncGenerator[Neo4jClient, Any], neo4j_driver: AsyncGenerator[AsyncDriver, Any]
):
    driver = await anext(neo4j_driver)
    client = await anext(package_client)

    async with driver.session() as session:
        await session.run("CREATE INDEX test FOR (n:Node) ON (n.name)")

    await client.drop_indexes()

    async with driver.session() as session:
        query_results = await session.run("SHOW INDEXES")
        results = await query_results.values()

        assert len(results) == 0


@pytest.mark.asyncio
async def test_batch_exception(
    package_client: AsyncGenerator[Neo4jClient, Any], neo4j_driver: AsyncGenerator[AsyncDriver, Any]
):
    driver = await anext(neo4j_driver)
    client = await anext(package_client)

    with pytest.raises(Exception):
        async with client.batch():
            await client.cypher("CREATE (n:Node) SET n.name = $name", parameters={"name": "TestName"})
            await client.cypher("CREATE (n:Node) SET n.name = $name", parameters={"name": "TestName2"})

            raise Exception("Test Exception")  # pylint: disable=broad-exception-raised

    async with driver.session() as session:
        query_results = await session.run("MATCH (n) RETURN n")
        results = await query_results.values()

        assert len(results) == 0


@pytest.mark.asyncio
async def test_batch_commit(
    package_client: AsyncGenerator[Neo4jClient, Any], neo4j_driver: AsyncGenerator[AsyncDriver, Any]
):
    driver = await anext(neo4j_driver)
    client = await anext(package_client)

    async with client.batch():
        await client.cypher("CREATE (n:Node) SET n.name = $name", parameters={"name": "TestName"})
        await client.cypher("CREATE (n:Node) SET n.name = $name", parameters={"name": "TestName2"})

    async with driver.session() as session:
        query_results = await session.run("MATCH (n) RETURN n")
        results = await query_results.values()

        assert len(results) == 2
