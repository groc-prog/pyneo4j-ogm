# pylint: disable=invalid-name, redefined-outer-name, unused-import

from neo4j_ogm.queries.query_builder import QueryBuilder
from tests.unit.fixtures.query_builder import query_builder


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
    query_builder.query_options(options={"order": "DESC"})
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
    query_builder.query_options(options={"sort": ["name", "age"], "order": "DESC", "limit": 10, "skip": 5})
    expected_result = "ORDER BY n.name, n.age DESC SKIP 5 LIMIT 10"
    assert query_builder.query["options"] == expected_result
