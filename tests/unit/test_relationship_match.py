# pylint: disable=invalid-name, redefined-outer-name, unused-import, missing-module-docstring

import pytest

from pyneo4j_ogm.exceptions import InvalidRelationshipDirection, InvalidRelationshipHops
from pyneo4j_ogm.queries.query_builder import QueryBuilder
from pyneo4j_ogm.queries.types import RelationshipMatchDirection
from tests.fixtures.query_builder import query_builder


def test_relationship_match_without_parameters(query_builder: QueryBuilder):
    result = query_builder.relationship_match()
    assert result == "()-[r]-()"


def test_relationship_match_with_ref(query_builder: QueryBuilder):
    result = query_builder.relationship_match(ref="a")
    assert result == "()-[a]-()"


def test_relationship_match_with_type(query_builder: QueryBuilder):
    result = query_builder.relationship_match(type_="REL")
    assert result == "()-[r:REL]-()"

    result = query_builder.relationship_match(type_="")
    assert result == "()-[r]-()"


def test_relationship_match_with_node_labels(query_builder: QueryBuilder):
    result = query_builder.relationship_match(start_node_labels=["A"], end_node_labels=["B", "C"])
    assert result == "(:A)-[r]-(:B:C)"

    result = query_builder.relationship_match(start_node_labels=["A"], end_node_labels=[])
    assert result == "(:A)-[r]-()"


def test_relationship_match_with_node_refs(query_builder: QueryBuilder):
    result = query_builder.relationship_match(start_node_ref="a", end_node_ref="b")
    assert result == "(a)-[r]-(b)"


def test_relationship_match_with_direction(query_builder: QueryBuilder):
    result = query_builder.relationship_match(direction=RelationshipMatchDirection.OUTGOING)
    assert result == "()-[r]->()"

    result = query_builder.relationship_match(direction=RelationshipMatchDirection.INCOMING)
    assert result == "()<-[r]-()"

    result = query_builder.relationship_match(direction=RelationshipMatchDirection.BOTH)
    assert result == "()-[r]-()"

    with pytest.raises(InvalidRelationshipDirection):
        query_builder.relationship_match(direction="invalid")  # type: ignore


def test_relationship_match_hops(query_builder: QueryBuilder):
    result = query_builder.relationship_match(min_hops=3)
    assert result == "()-[r*3..]-()"

    result = query_builder.relationship_match(min_hops=3, max_hops="*")
    assert result == "()-[r*3..]-()"

    result = query_builder.relationship_match(min_hops=3, max_hops=10)
    assert result == "()-[r*3..10]-()"

    result = query_builder.relationship_match(max_hops=10)
    assert result == "()-[r*..10]-()"

    result = query_builder.relationship_match(max_hops="*")
    assert result == "()-[r*]-()"


def test_invalid_relationship_hops(query_builder: QueryBuilder):
    with pytest.raises(InvalidRelationshipHops):
        query_builder.relationship_match(min_hops=-1)

    with pytest.raises(InvalidRelationshipHops):
        query_builder.relationship_match(max_hops="INVALID_VALUE")  # type: ignore

    with pytest.raises(InvalidRelationshipHops):
        query_builder.relationship_match(max_hops=-1)
