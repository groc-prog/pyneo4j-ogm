"""
Fixture for setup/teardown of a Neo4j database for integration tests.
"""
import pytest
from neo4j import AsyncGraphDatabase

from pyneo4j_ogm.core.client import Pyneo4jClient


@pytest.fixture
async def pyneo4j_client():
    """
    Create a Pyneo4jClient instance from the package for the test session.
    """
    client = await Pyneo4jClient().connect("bolt://localhost:7687", auth=("neo4j", "password"))

    # Drop all nodes, indexes, and constraints from the database.
    await client.drop_constraints()
    await client.drop_indexes()
    await client.drop_nodes()

    yield client

    await client.close()


@pytest.fixture
async def neo4j_session():
    """
    Create a neo4j driver instance for the test session.
    """
    driver = AsyncGraphDatabase.driver(uri="bolt://localhost:7687", auth=("neo4j", "password"))

    async with driver.session() as session:
        yield session

    await driver.close()
