# pylint: disable=unused-argument, unused-import, redefined-outer-name, protected-access, missing-module-docstring, missing-class-docstring
# pyright: reportGeneralTypeIssues=false

import pytest
from neo4j import AsyncSession

from pyneo4j_ogm.core.client import Pyneo4jClient
from pyneo4j_ogm.exceptions import TransactionInProgress
from tests.fixtures.db_setup import client, session


async def test_batch(client: Pyneo4jClient, session: AsyncSession):
    async with client.batch():
        await client.cypher("CREATE (n:Node) SET n.name = $name", parameters={"name": "TestName"})
        await client.cypher("CREATE (n:Node) SET n.name = $name", parameters={"name": "TestName2"})

    query_results = await session.run("MATCH (n) RETURN n")
    results = await query_results.values()
    await query_results.consume()

    assert len(results) == 2


async def test_batch_exception(client: Pyneo4jClient, session: AsyncSession):
    with pytest.raises(Exception):
        async with client.batch():
            await client.cypher("CREATE (n:Node) SET n.name = $name", parameters={"name": "TestName"})
            await client.cypher("CREATE (n:Node) SET n.name = $name", parameters={"name": "TestName2"})

            raise Exception("Test Exception")  # pylint: disable=broad-exception-raised

    query_results = await session.run("MATCH (n) RETURN n")
    results = await query_results.values()
    await query_results.consume()

    assert len(results) == 0


async def test_transaction_in_progress_exception(client: Pyneo4jClient):
    await client._begin_transaction()

    with pytest.raises(TransactionInProgress):
        await client._begin_transaction()
