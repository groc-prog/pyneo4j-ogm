# pylint: disable=unused-argument, unused-import, redefined-outer-name, protected-access, missing-module-docstring, missing-class-docstring
# pyright: reportGeneralTypeIssues=false

import pytest
from pydantic import ValidationError

from pyneo4j_ogm.exceptions import InvalidRelationshipDirection, InvalidRelationshipHops
from pyneo4j_ogm.queries.query_builder import QueryBuilder
from pyneo4j_ogm.queries.types import QueryOptionsOrder, RelationshipMatchDirection
from tests.fixtures.query_builder import query_builder
from tests.utils.string_utils import assert_string_equality


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


def test_build_projections_with_empty_projections(query_builder: QueryBuilder):
    query_builder.build_projections(projections={}, ref="n")
    assert query_builder.query["projections"] == ""


def test_build_projections_with_non_dict_param(query_builder: QueryBuilder):
    query_builder.build_projections(projections="not a dict", ref="n")  # type: ignore
    assert query_builder.query["projections"] == ""


def test_build_projections_with_projections(query_builder: QueryBuilder):
    projections = {"name_prop": "name", "age_prop": "age"}
    expected_result = "WITH DISTINCT n RETURN DISTINCT collect({name_prop: n.name, age_prop: n.age})"

    query_builder.build_projections(projections=projections, ref="n")
    assert_string_equality(query_builder.query["projections"], expected_result)


def test_build_projections_with_ref(query_builder: QueryBuilder):
    projections = {"name_prop": "name", "age_prop": "age"}
    expected_result = "WITH DISTINCT a RETURN DISTINCT collect({name_prop: a.name, age_prop: a.age})"

    query_builder.build_projections(projections=projections, ref="a")
    assert_string_equality(query_builder.query["projections"], expected_result)


def test_build_projections_with_special_keys(query_builder: QueryBuilder):
    projections = {"element_id": "$elementId", "id": "$id"}
    expected_result = "WITH DISTINCT n RETURN DISTINCT collect({element_id: elementId(n), id: ID(n)})"

    query_builder.build_projections(projections=projections)
    assert_string_equality(query_builder.query["projections"], expected_result)


def test_query_options_with_empty_options(query_builder: QueryBuilder):
    query_builder.query_options(options={})
    assert query_builder.query["options"] == ""


def test_query_options_with_sort_option(query_builder: QueryBuilder):
    query_builder.query_options(options={"sort": ["name", "age"]})
    expected_result = "ORDER BY n.name, n.age"
    assert query_builder.query["options"] == expected_result

    query_builder.query_options(options={"sort": "name"})
    expected_result = "ORDER BY n.name"
    assert query_builder.query["options"] == expected_result


def test_query_options_with_order_option(query_builder: QueryBuilder):
    query_builder.query_options(options={"order": QueryOptionsOrder.DESCENDING})
    expected_result = "ORDER BY n DESC"
    assert query_builder.query["options"] == expected_result


def test_query_options_with_limit_option(query_builder: QueryBuilder):
    query_builder.query_options(options={"limit": 10})
    expected_result = "LIMIT 10"
    assert query_builder.query["options"] == expected_result


def test_query_options_with_skip_option(query_builder: QueryBuilder):
    query_builder.query_options(options={"skip": 5})
    expected_result = "SKIP 5"
    assert query_builder.query["options"] == expected_result


def test_query_options_with_ref(query_builder: QueryBuilder):
    query_builder.query_options(options={"sort": "name"}, ref="a")
    expected_result = "ORDER BY a.name"
    assert query_builder.query["options"] == expected_result


def test_query_options_with_all_options(query_builder: QueryBuilder):
    query_builder.query_options(
        options={"sort": ["name", "age"], "order": QueryOptionsOrder.DESCENDING, "limit": 10, "skip": 5}
    )
    expected_result = "ORDER BY n.name, n.age DESC SKIP 5 LIMIT 10"
    assert query_builder.query["options"] == expected_result


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


def test_valid_multi_hop_filters_with_min_hops(query_builder: QueryBuilder):
    query_builder.multi_hop_filters({"$node": {"$labels": "Node", "name": "Jenny"}, "$minHops": 3})

    assert query_builder.query["match"] == ", path = (n)-[r*3..]->(m)"
    assert query_builder.query["where"] == "ALL(i IN labels(m) WHERE i IN $_n_0) AND m.name = $_n_1"
    assert query_builder.parameters == {"_n_0": ["Node"], "_n_1": "Jenny"}


def test_valid_multi_hop_filters_with_max_hops(query_builder: QueryBuilder):
    query_builder.multi_hop_filters({"$node": {"$labels": "Node", "name": "Jenny"}, "$maxHops": 3})

    assert query_builder.query["match"] == ", path = (n)-[r*..3]->(m)"
    assert query_builder.query["where"] == "ALL(i IN labels(m) WHERE i IN $_n_0) AND m.name = $_n_1"
    assert query_builder.parameters == {"_n_0": ["Node"], "_n_1": "Jenny"}


def test_valid_multi_hop_filters_with_max_hops_special_char(query_builder: QueryBuilder):
    query_builder.multi_hop_filters({"$node": {"$labels": "Node", "name": "Jenny"}, "$maxHops": "*"})

    assert query_builder.query["match"] == ", path = (n)-[r*]->(m)"
    assert query_builder.query["where"] == "ALL(i IN labels(m) WHERE i IN $_n_0) AND m.name = $_n_1"
    assert query_builder.parameters == {"_n_0": ["Node"], "_n_1": "Jenny"}


def test_valid_multi_hop_filters_with_min_and_max_hops(query_builder: QueryBuilder):
    query_builder.multi_hop_filters({"$node": {"$labels": "Node", "name": "Jenny"}, "$minHops": 3, "$maxHops": 5})

    assert query_builder.query["match"] == ", path = (n)-[r*3..5]->(m)"
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
