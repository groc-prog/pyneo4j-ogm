# pylint: disable=invalid-name, redefined-outer-name, unused-import

from pyneo4j_ogm.queries.query_builder import QueryBuilder
from tests.unit.fixtures.query_builder import query_builder


def test_build_projections_with_empty_projections(query_builder: QueryBuilder):
    query_builder.build_projections(projections={}, ref="n")
    assert query_builder.query["projections"] == ""


def test_build_projections_with_projections(query_builder: QueryBuilder):
    projections = {"name_prop": "name", "age_prop": "age"}
    expected_result = "DISTINCT collect({name_prop: n.name, age_prop: n.age})"

    query_builder.build_projections(projections=projections, ref="n")
    assert query_builder.query["projections"] == expected_result


def test_build_projections_with_ref(query_builder: QueryBuilder):
    projections = {"name_prop": "name", "age_prop": "age"}
    expected_result = "DISTINCT collect({name_prop: a.name, age_prop: a.age})"

    query_builder.build_projections(projections=projections, ref="a")
    assert query_builder.query["projections"] == expected_result
