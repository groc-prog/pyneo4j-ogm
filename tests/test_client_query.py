# pylint: disable=unused-argument, unused-import, redefined-outer-name, protected-access, missing-module-docstring, missing-class-docstring
# pyright: reportGeneralTypeIssues=false

from typing import cast

import pytest
from neo4j import AsyncSession
from neo4j.exceptions import CypherSyntaxError
from neo4j.graph import Node, Path, Relationship

from pyneo4j_ogm.core.client import Pyneo4jClient
from pyneo4j_ogm.core.node import NodeModel
from pyneo4j_ogm.core.relationship import RelationshipModel
from tests.fixtures.db_setup import client, session


class CypherResolvingNode(NodeModel):
    name: str

    class Settings:
        labels = {"TestNode"}


class CypherResolvingRelationship(RelationshipModel):
    kind: str

    class Settings:
        type = "TEST_RELATIONSHIP"


async def test_cypher_query(client: Pyneo4jClient, session: AsyncSession):
    results, meta = await client.cypher("CREATE (n:Node) SET n.name = $name RETURN n", parameters={"name": "TestName"})

    assert len(results) == 1
    assert len(results[0]) == 1
    assert isinstance(results[0][0], Node)
    assert meta == ["n"]

    query_results = await session.run("MATCH (n:Node) RETURN n")
    result = await query_results.single()

    assert result is not None
    assert result["n"]["name"] == "TestName"


async def test_cypher_resolve_model_query(client: Pyneo4jClient, session: AsyncSession):
    await client.register_models([CypherResolvingNode])

    result = await session.run("CREATE (n:TestNode) SET n.name = $name", {"name": "TestName"})
    await result.consume()

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


async def test_cypher_resolve_relationship_model_query(client: Pyneo4jClient, session: AsyncSession):
    await client.register_models([CypherResolvingRelationship])

    result = await session.run(
        "CREATE (:TestNode {name: $start})-[:TEST_RELATIONSHIP {kind: 'awesome'}]->(:TestNode {end: $end}) ",
        {"start": "start", "end": "end"},
    )
    await result.consume()

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


async def test_cypher_resolve_path_query(client: Pyneo4jClient, session: AsyncSession):
    await client.register_models([CypherResolvingNode, CypherResolvingRelationship])

    result = await session.run(
        "CREATE (:TestNode {name: $start})-[:TEST_RELATIONSHIP {kind: 'awesome'}]->(:TestNode {name: $end}) ",
        {"start": "start", "end": "end"},
    )
    await result.consume()

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


async def test_cypher_query_exception(client: Pyneo4jClient):
    with pytest.raises(CypherSyntaxError):
        await client.cypher("MATCH n RETURN n", parameters={"a": 1})
