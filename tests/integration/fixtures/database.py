"""
Fixture for setup/teardown of a Neo4j database for integration tests.
"""
import asyncio

import pytest

from pyneo4j_ogm.core.client import Neo4jClient


@pytest.fixture(scope="session")
def event_loop():
    """
    Create an instance of the default event loop for the test session.
    """
    loop = asyncio.get_event_loop()
    yield loop

    loop.close()


@pytest.fixture
async def database_client():
    """
    Create a Neo4jClient instance for the test session.
    """
    client = Neo4jClient().connect("bolt://localhost:7687", auth=("neo4j", "password"))

    # Drop all nodes, indexes, and constraints from the database.
    await client.drop_constraints()
    await client.drop_indexes()
    await client.drop_nodes()

    yield client

    await client.close()
