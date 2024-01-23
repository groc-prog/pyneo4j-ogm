# pylint: disable=unused-argument, unused-import, redefined-outer-name, protected-access, missing-module-docstring, missing-class-docstring
# pyright: reportGeneralTypeIssues=false

import pytest
from pydantic import ValidationError

from pyneo4j_ogm.queries.query_builder import QueryBuilder
from tests.fixtures.query_builder import query_builder


def test_invalid_node_filters(query_builder: QueryBuilder):
    query_builder.node_filters({})

    assert query_builder.query["where"] == ""
    assert query_builder.parameters == {}


def test_valid_node_filters(query_builder: QueryBuilder):
    query_builder.node_filters({"name": {"$eq": "Jenny"}})

    assert query_builder.query["where"] == "n.name = $_n_0"
    assert query_builder.parameters == {"_n_0": "Jenny"}


def test_node_filters_ref(query_builder: QueryBuilder):
    query_builder.node_filters({"name": {"$eq": "Jenny"}}, ref="m")

    assert query_builder.query["where"] == "m.name = $_n_0"
    assert query_builder.parameters == {"_n_0": "Jenny"}


def test_invalid_relationship_filters(query_builder: QueryBuilder):
    query_builder.relationship_filters({})

    assert query_builder.query["where"] == ""
    assert query_builder.parameters == {}


def test_valid_relationship_filters(query_builder: QueryBuilder):
    query_builder.relationship_filters({"name": {"$eq": "Jenny"}})

    assert query_builder.query["where"] == "r.name = $_n_0"
    assert query_builder.parameters == {"_n_0": "Jenny"}


def test_relationship_filters_ref(query_builder: QueryBuilder):
    query_builder.relationship_filters({"name": {"$eq": "Jenny"}}, ref="m")

    assert query_builder.query["where"] == "m.name = $_n_0"
    assert query_builder.parameters == {"_n_0": "Jenny"}


def test_invalid_relationship_property_filters(query_builder: QueryBuilder):
    query_builder.relationship_property_filters({})

    assert query_builder.query["where"] == ""
    assert query_builder.parameters == {}


def test_relationship_property_node_filters(query_builder: QueryBuilder):
    query_builder.relationship_property_filters({"name": {"$eq": "Jenny"}})

    assert query_builder.query["where"] == "end.name = $_n_0"
    assert query_builder.parameters == {"_n_0": "Jenny"}


def test_relationship_property_relationship_filters(query_builder: QueryBuilder):
    query_builder.relationship_property_filters({"$relationship": {"name": {"$eq": "Jenny"}}})

    assert query_builder.query["where"] == "r.name = $_n_0"
    assert query_builder.parameters == {"_n_0": "Jenny"}


def test_relationship_property_all_filters(query_builder: QueryBuilder):
    query_builder.relationship_property_filters(
        {"$relationship": {"name": {"$eq": "Jenny"}}, "name": {"$eq": "Johnny"}}
    )

    assert query_builder.query["where"] == "r.name = $_n_0 AND end.name = $_n_1"
    assert query_builder.parameters == {"_n_0": "Jenny", "_n_1": "Johnny"}


def test_relationship_property_all_filters_refs(query_builder: QueryBuilder):
    query_builder.relationship_property_filters(
        {"$relationship": {"name": {"$eq": "Jenny"}}, "name": {"$eq": "Johnny"}}, ref="rel", node_ref="node"
    )

    assert query_builder.query["where"] == "rel.name = $_n_0 AND node.name = $_n_1"
    assert query_builder.parameters == {"_n_0": "Jenny", "_n_1": "Johnny"}


def test_invalid_multi_hop_filters(query_builder: QueryBuilder):
    with pytest.raises(ValidationError):
        query_builder.multi_hop_filters({})  # type: ignore

    assert query_builder.query["where"] == ""
    assert query_builder.parameters == {}

    with pytest.raises(ValidationError):
        query_builder.multi_hop_filters({"$node": {}})

    assert query_builder.query["where"] == ""
    assert query_builder.parameters == {}


def test_valid_multi_hop_filters(query_builder: QueryBuilder):
    query_builder.multi_hop_filters({"$node": {"$labels": "Node", "name": "Jenny"}})

    assert query_builder.query["match"] == ", path = (n)-[r*]->(m)"
    assert query_builder.query["where"] == "ALL(i IN labels(m) WHERE i IN $_n_0) AND m.name = $_n_1"
    assert query_builder.parameters == {"_n_0": ["Node"], "_n_1": "Jenny"}


def test_valid_multi_hop_filters_with_ref(query_builder: QueryBuilder):
    query_builder.multi_hop_filters({"$node": {"$labels": "Node", "name": "Jenny"}}, start_ref="start", end_ref="end")

    assert query_builder.query["match"] == ", path = (start)-[r*]->(end)"
    assert query_builder.query["where"] == "ALL(i IN labels(end) WHERE i IN $_n_0) AND end.name = $_n_1"
    assert query_builder.parameters == {"_n_0": ["Node"], "_n_1": "Jenny"}


def test_invalid_multi_hop_filters_with_relationships(query_builder: QueryBuilder):
    with pytest.raises(ValidationError):
        query_builder.multi_hop_filters(
            {
                "$node": {"$labels": "Jenny", "name": "Jenny"},
                "$relationships": [
                    {"name": "type_a"},
                ],
            }
        )

    assert query_builder.query["where"] == ""
    assert query_builder.parameters == {}


def test_multi_hop_filters_with_relationships(query_builder: QueryBuilder):
    query_builder.multi_hop_filters(
        {
            "$node": {"$labels": "Node", "name": "Jenny"},
            "$relationships": [
                {"$type": "A", "name": "type_a"},
                {"$type": "B", "name": "type_b"},
            ],
        }
    )

    expected_query_string = """
        ALL(i IN labels(m) WHERE i IN $_n_0) AND
        m.name = $_n_1 AND
        ALL(r IN relationships(path) WHERE
            CASE type(r)
                WHEN 'A' THEN r.name = $_n_2
                WHEN 'B' THEN r.name = $_n_3
                ELSE true
            END
        )
    """

    normalized_builder_query = "".join(query_builder.query["where"].split())
    normalized_expected_query = "".join(expected_query_string.split())

    assert query_builder.query["match"] == ", path = (n)-[r*]->(m)"
    assert normalized_builder_query == normalized_expected_query
    assert query_builder.parameters == {"_n_0": ["Node"], "_n_1": "Jenny", "_n_2": "type_a", "_n_3": "type_b"}


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
