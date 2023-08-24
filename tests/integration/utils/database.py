"""
Fixture for setup/teardown of a Neo4j database for integration tests.
"""
import asyncio

import pytest

from neo4j_ogm.core.client import Neo4jClient


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
    client = Neo4jClient().connect()
    yield client

    await client.close()
