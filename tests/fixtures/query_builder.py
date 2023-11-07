"""
Fixture for setup/teardown of unit tests using QueryBuilder instance.
"""
import pytest

from pyneo4j_ogm.queries.query_builder import QueryBuilder


@pytest.fixture
def query_builder():
    """
    Fixture for providing a QueryBuilder instance.
    """
    builder = QueryBuilder()
    builder.reset_query()
    builder.parameters = {}

    return builder
