# pylint: disable=unused-argument, unused-import, redefined-outer-name, protected-access, missing-module-docstring, missing-class-docstring
# pyright: reportGeneralTypeIssues=false

from pyneo4j_ogm.queries.query_builder import QueryBuilder
from tests.fixtures.query_builder import query_builder
from tests.utils.string_utils import assert_string_equality


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
