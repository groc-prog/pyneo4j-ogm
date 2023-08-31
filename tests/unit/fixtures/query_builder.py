"""
Fixture for setup/teardown of unit tests using QueryBuilder instance.
"""
import pytest

from neo4j_ogm.queries.query_builder import QueryBuilder


@pytest.fixture
def query_builder():
    """
    Fixture for providing a QueryBuilder instance.
    """
    return QueryBuilder()
