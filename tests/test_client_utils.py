# pylint: disable=unused-argument, unused-import, redefined-outer-name, protected-access, missing-module-docstring, missing-class-docstring
# pyright: reportGeneralTypeIssues=false

from neo4j import AsyncSession

from pyneo4j_ogm.core.client import Pyneo4jClient
from pyneo4j_ogm.core.node import NodeModel
from pyneo4j_ogm.core.relationship import RelationshipModel
from tests.fixtures.db_setup import client, session


async def test_drop_nodes(client: Pyneo4jClient, session: AsyncSession):
    print("BEFORE CREATE")
    result = await session.run("CREATE (n:Node) SET n.name = $name", {"name": "TestName"})
    await result.consume()

    await client.drop_nodes()
    print("DROPPED")

    query_results = await session.run("MATCH (n) RETURN n")
    results = await query_results.values()
    await query_results.consume()

    assert len(results) == 0


async def test_drop_constraints(client: Pyneo4jClient, session: AsyncSession):
    result = await session.run("CREATE CONSTRAINT test FOR (n:Node) REQUIRE n.name IS UNIQUE")
    await result.consume()

    await client.drop_constraints()

    query_results = await session.run("SHOW CONSTRAINTS")
    results = await query_results.values()
    await query_results.consume()

    assert len(results) == 0


async def test_drop_indexes(client: Pyneo4jClient, session: AsyncSession):
    result = await session.run("CREATE INDEX test FOR (n:Node) ON (n.name)")
    await result.consume()

    await client.drop_indexes()

    query_results = await session.run("SHOW INDEXES")
    results = await query_results.values()
    await query_results.consume()

    assert len(results) == 0
