# pylint: disable=invalid-name, redefined-outer-name, unused-import

from neo4j_ogm.queries.query_builder import QueryBuilder
from tests.unit.fixtures.query_builder import query_builder


def test_node_match_with_labels(query_builder: QueryBuilder):
    result = query_builder.node_match(labels=["Person"], ref="p")
    assert result == "(p:Person)"


def test_node_match_without_labels(query_builder: QueryBuilder):
    result = query_builder.node_match(ref="p")
    assert result == "(p)"


def test_node_match_with_empty_ref(query_builder: QueryBuilder):
    result = query_builder.node_match(labels=["Person"], ref="")
    assert result == "(:Person)"


def test_node_match_with_empty_labels(query_builder: QueryBuilder):
    result = query_builder.node_match(labels=[], ref="p")
    assert result == "(p)"

    result = query_builder.node_match(labels=[""], ref="p")
    assert result == "(p)"


def test_node_match_with_none_ref(query_builder: QueryBuilder):
    result = query_builder.node_match(labels=["Person"], ref=None)
    assert result == "(:Person)"


def test_node_match_with_none_labels(query_builder: QueryBuilder):
    result = query_builder.node_match(labels=None, ref="p")
    assert result == "(p)"
