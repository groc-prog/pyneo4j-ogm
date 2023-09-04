# pylint: disable=invalid-name, redefined-outer-name, unused-import

from neo4j_ogm.queries.query_builder import QueryBuilder
from tests.unit.fixtures.query_builder import query_builder


def test_node_match_with_labels(query_builder: QueryBuilder):
    result = query_builder.node_match(labels=["Person"], ref="p")
    assert result == "(p:Person)"
