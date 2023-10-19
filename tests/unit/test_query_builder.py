# pylint: disable=invalid-name, redefined-outer-name, unused-import, missing-module-docstring

from pyneo4j_ogm.queries.query_builder import QueryBuilder
from tests.unit.fixtures.query_builder import query_builder


def test_reset_query(query_builder: QueryBuilder):
    query_builder.query = {
        "match": "MATCH (n)",
        "where": "WHERE n.name = 'John'",
        "projections": "RETURN n",
        "options": "ORDER BY n.age DESC",
    }
    query_builder.reset_query()

    assert query_builder.query == {
        "match": "",
        "where": "",
        "projections": "",
        "options": "",
    }
